import csv, hashlib, io, json, re
from datetime import datetime
from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.models import DiagnosticEvent, DiagnosticHypothesis, DiagnosticObservation, DiagnosticSession, DiagnosticStep, DiagnosticTroubleCode, KnowledgeItem, KnowledgeSource, VehicleProfile, now
from app.database.session import get_db
from app.modules.diagnostics.engine import analyze, complete_step, event
from app.schemas import DTCLookup, KnowledgeImportPayload, OBDReport, ObservationCreate, SessionCreate, StepComplete, VehicleCreate
from app.seed import GARAGE_ID, USER_ID

router=APIRouter(prefix="/api")
def garage(x_garage_id: str|None=Header(default=None)): return x_garage_id or GARAGE_ID
def owned_session(db,id,gid):
    obj=db.scalar(select(DiagnosticSession).where(DiagnosticSession.id==id,DiagnosticSession.garage_id==gid))
    if not obj: raise HTTPException(404,"Session introuvable pour ce garage")
    return obj
def serialize(o):
    hidden={"vin","registration_encrypted","registration_fingerprint"} if isinstance(o,VehicleProfile) else set()
    return {c.name:getattr(o,c.name) for c in o.__table__.columns if c.name not in hidden}
DTC_PATTERN=re.compile(r"[PBCU][0-9A-F]{4}")
DTC_CATEGORY={"P":"powertrain","B":"body","C":"chassis","U":"network"}
def recognize_dtc(code):
    """Reconnaît tout code syntaxiquement valide par sa structure (catégorie + générique/constructeur),
    même sans définition stockée. Un code valide n'est jamais 'inconnu'."""
    code=(code or "").upper()
    if not DTC_PATTERN.fullmatch(code): return None
    return {"code":code,"category":DTC_CATEGORY[code[0]],"manufacturer_specific":code[1] not in "02","generic_description":None,"documented":False}

@router.get("/health")
def health(): return {"status":"ok","service":"diagpilot-api","llm_provider":settings.llm_provider}
@router.get("/vehicles")
def vehicles(db:Session=Depends(get_db),gid:str=Depends(garage)): return [serialize(x) for x in db.scalars(select(VehicleProfile).where(VehicleProfile.garage_id==gid)).all()]
@router.post("/vehicles",status_code=201)
def create_vehicle(data:VehicleCreate,db:Session=Depends(get_db),gid:str=Depends(garage)):
    v=VehicleProfile(garage_id=gid,**data.model_dump()); db.add(v); db.commit(); return serialize(v)
@router.get("/vehicles/{vehicle_id}")
def vehicle(vehicle_id:str,db:Session=Depends(get_db),gid:str=Depends(garage)):
    v=db.scalar(select(VehicleProfile).where(VehicleProfile.id==vehicle_id,VehicleProfile.garage_id==gid))
    if not v: raise HTTPException(404,"Véhicule introuvable")
    return serialize(v)
@router.put("/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id:str,data:VehicleCreate,db:Session=Depends(get_db),gid:str=Depends(garage)):
    v=db.scalar(select(VehicleProfile).where(VehicleProfile.id==vehicle_id,VehicleProfile.garage_id==gid))
    if not v: raise HTTPException(404,"Véhicule introuvable")
    for k,val in data.model_dump().items(): setattr(v,k,val)
    db.commit(); return serialize(v)

@router.get("/dtcs")
def dtcs(db:Session=Depends(get_db)): return [serialize(x) for x in db.scalars(select(DiagnosticTroubleCode).order_by(DiagnosticTroubleCode.code)).all()]
@router.get("/dtcs/{code}")
def dtc(code:str,db:Session=Depends(get_db)):
    d=db.scalar(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code==code.upper()))
    if d: return {**serialize(d),"documented":True}
    recognized=recognize_dtc(code)
    if recognized: return recognized
    raise HTTPException(404,"Code DTC syntaxiquement invalide")
@router.post("/dtcs/lookup")
def lookup(data:DTCLookup,db:Session=Depends(get_db),gid:str=Depends(garage)):
    if not db.scalar(select(VehicleProfile).where(VehicleProfile.id==data.vehicle_id,VehicleProfile.garage_id==gid)): raise HTTPException(404,"Véhicule introuvable")
    codes=list(dict.fromkeys(x.upper() for x in data.codes))
    found=db.scalars(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code.in_(codes))).all(); found_codes={d.code for d in found}
    rest=[recognize_dtc(c) or {"code":c,"invalid":True} for c in codes if c not in found_codes]
    undocumented=[r for r in rest if not r.get("invalid")]; invalid=sorted(r["code"] for r in rest if r.get("invalid"))
    return {"supported":[{**serialize(x),"documented":True} for x in found],"undocumented":undocumented,"invalid":invalid,"unsupported":sorted([r["code"] for r in undocumented]+invalid)}

@router.post("/diagnostic-sessions",status_code=201)
def create_session(data:SessionCreate,db:Session=Depends(get_db),gid:str=Depends(garage)):
    if not db.scalar(select(VehicleProfile).where(VehicleProfile.id==data.vehicle_profile_id,VehicleProfile.garage_id==gid)): raise HTTPException(404,"Véhicule introuvable pour ce garage")
    s=DiagnosticSession(garage_id=gid,technician_id=data.technician_id or USER_ID,**data.model_dump(exclude={"technician_id"})); db.add(s); db.flush(); event(db,s.id,"session_created",{"vehicle_profile_id":s.vehicle_profile_id},s.technician_id); db.commit(); return serialize(s)
@router.get("/diagnostic-sessions")
def sessions(db:Session=Depends(get_db),gid:str=Depends(garage)): return [serialize(x) for x in db.scalars(select(DiagnosticSession).where(DiagnosticSession.garage_id==gid).order_by(DiagnosticSession.created_at.desc())).all()]
@router.get("/diagnostic-sessions/{session_id}")
def session_detail(session_id:str,db:Session=Depends(get_db),gid:str=Depends(garage)):
    s=owned_session(db,session_id,gid); out=serialize(s); out["vehicle"]=serialize(s.vehicle); out["observations"]=[serialize(x) for x in db.scalars(select(DiagnosticObservation).where(DiagnosticObservation.session_id==s.id)).all()]; return out
@router.post("/diagnostic-sessions/{session_id}/observations",status_code=201)
def add_observation(session_id:str,data:ObservationCreate,db:Session=Depends(get_db),gid:str=Depends(garage)):
    s=owned_session(db,session_id,gid); o=DiagnosticObservation(session_id=s.id,**data.model_dump(exclude_none=True)); db.add(o); event(db,s.id,"dtc_added" if data.observation_type=="DTC" else "observation_added",data.model_dump(mode="json"),s.technician_id); db.commit(); return serialize(o)
@router.post("/diagnostic-sessions/{session_id}/analyze")
def run_analysis(session_id:str,db:Session=Depends(get_db),gid:str=Depends(garage)):
    s=owned_session(db,session_id,gid)
    codes=[o.key for o in db.scalars(select(DiagnosticObservation).where(DiagnosticObservation.session_id==s.id,DiagnosticObservation.observation_type=="DTC")).all()]
    if not codes: raise HTTPException(422,"Ajoutez au moins un code DTC avant l’analyse")
    invalid=[code for code in codes if not re.fullmatch(r"[PBCU][0-9A-F]{4}",code.upper())]
    if invalid: raise HTTPException(422,f"Format DTC invalide : {', '.join(invalid)}")
    try: return analyze(db,s)
    except ValueError as e: raise HTTPException(409,str(e))
@router.get("/diagnostic-sessions/{session_id}/hypotheses")
def hypotheses(session_id:str,db:Session=Depends(get_db),gid:str=Depends(garage)):
    owned_session(db,session_id,gid); return [serialize(x) for x in db.scalars(select(DiagnosticHypothesis).where(DiagnosticHypothesis.session_id==session_id).order_by(DiagnosticHypothesis.probability_score.desc())).all()]
@router.get("/diagnostic-sessions/{session_id}/steps")
def steps(session_id:str,db:Session=Depends(get_db),gid:str=Depends(garage)):
    owned_session(db,session_id,gid); return [serialize(x) for x in db.scalars(select(DiagnosticStep).where(DiagnosticStep.session_id==session_id).order_by(DiagnosticStep.step_order)).all()]
@router.post("/diagnostic-sessions/{session_id}/steps/{step_id}/complete")
def finish_step(session_id:str,step_id:str,data:StepComplete,db:Session=Depends(get_db),gid:str=Depends(garage)):
    s=owned_session(db,session_id,gid); step=db.scalar(select(DiagnosticStep).where(DiagnosticStep.id==step_id,DiagnosticStep.session_id==s.id,DiagnosticStep.status=="current"))
    if not step: raise HTTPException(409,"Étape courante introuvable ou déjà terminée")
    if data.result_id not in [x["result_id"] for x in step.expected_results]: raise HTTPException(422,"Résultat non prévu pour cette étape")
    return serialize(complete_step(db,s,step,data))
@router.post("/diagnostic-sessions/{session_id}/complete")
def finish_session(session_id:str,db:Session=Depends(get_db),gid:str=Depends(garage)):
    s=owned_session(db,session_id,gid); s.status="completed"; s.completed_at=now(); event(db,s.id,"report_generated",{"status":"completed"},s.technician_id); db.commit(); return {"status":"completed","report_url":f"/api/diagnostic-sessions/{s.id}/report"}
@router.get("/diagnostic-sessions/{session_id}/report")
def report(session_id:str,db:Session=Depends(get_db),gid:str=Depends(garage)):
    s=owned_session(db,session_id,gid); hs=db.scalars(select(DiagnosticHypothesis).where(DiagnosticHypothesis.session_id==s.id).order_by(DiagnosticHypothesis.probability_score.desc())).all(); ss=db.scalars(select(DiagnosticStep).where(DiagnosticStep.session_id==s.id).order_by(DiagnosticStep.step_order)).all(); src={i for h in hs for i in h.source_ids}
    return {"disclaimer":"RAPPORT DE DÉMONSTRATION — ne pas utiliser sur un véhicule réel.","session":serialize(s),"vehicle":serialize(s.vehicle),"dtcs":[o.key for o in db.scalars(select(DiagnosticObservation).where(DiagnosticObservation.session_id==s.id,DiagnosticObservation.observation_type=="DTC")).all()],"tests":[serialize(x) for x in ss],"hypotheses":[serialize(x) for x in hs],"leading_hypothesis":serialize(hs[0]) if hs else None,"sources":[serialize(x) for x in db.scalars(select(KnowledgeSource).where(KnowledgeSource.id.in_(src))).all()] if src else [],"limitations":["Classement interne non scientifique","Corpus fictif","Validation professionnelle requise"]}

@router.get("/knowledge/sources")
def sources(db:Session=Depends(get_db)): return [serialize(x) for x in db.scalars(select(KnowledgeSource)).all()]
@router.post("/knowledge/sources",status_code=201)
def source(data:dict,db:Session=Depends(get_db)):
    allowed={"title","source_type","publisher","version","license_type","source_url","local_file_path","checksum","trust_level","review_status"}
    if set(data)-allowed: raise HTTPException(422,"Champs de source non autorisés")
    s=KnowledgeSource(**data); db.add(s); db.commit(); return serialize(s)
@router.get("/knowledge/items")
def items(dtc_code:str|None=None,db:Session=Depends(get_db)):
    q=select(KnowledgeItem)
    if dtc_code:
        d=db.scalar(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code==dtc_code.upper())); q=q.where(KnowledgeItem.dtc_id==d.id) if d else q.where(False)
    return [serialize(x) for x in db.scalars(q).all()]
@router.post("/knowledge/search")
def search_knowledge(data:dict,db:Session=Depends(get_db)):
    term=str(data.get("query","")).lower(); rows=db.scalars(select(KnowledgeItem)).all(); return [serialize(x) for x in rows if term in (x.title+" "+x.content+" "+x.component).lower()]

def ingest_obd(report:OBDReport,db:Session,gid:str,session_id:str|None):
    vehicle=db.scalar(select(VehicleProfile).where(VehicleProfile.garage_id==gid,VehicleProfile.engine_code==report.vehicle.engine_code))
    if not vehicle: raise HTTPException(404,"Aucun véhicule compatible dans ce garage")
    if session_id: s=owned_session(db,session_id,gid)
    else:
        s=DiagnosticSession(garage_id=gid,technician_id=USER_ID,vehicle_profile_id=vehicle.id,status="collecting_data",customer_complaint="Import OBD de démonstration",observed_symptoms=""); db.add(s); db.flush(); event(db,s.id,"session_created",{"origin":"obd_import"},USER_ID)
    supported=[]; unsupported=[]
    for item in report.scan.dtcs:
        if db.scalar(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code==item.code)): supported.append(item.code)
        else: unsupported.append(item.code)
        db.add(DiagnosticObservation(session_id=s.id,observation_type="DTC",key=item.code,value={"status":item.status},source=f"obd_import:{report.scan.tool}",observed_at=report.scan.timestamp))
    if report.scan.freeze_frame: db.add(DiagnosticObservation(session_id=s.id,observation_type="freeze_frame",key="scan_freeze_frame",value=report.scan.freeze_frame,source=f"obd_import:{report.scan.tool}",observed_at=report.scan.timestamp))
    event(db,s.id,"dtc_added",{"supported":supported,"unsupported":unsupported},USER_ID); db.commit(); return {"session_id":s.id,"vehicle_id":vehicle.id,"supported":supported,"unsupported":unsupported,"warnings":["Import de démonstration ; aucune connexion OBD physique."]}

@router.post("/imports/obd-report")
async def import_obd(request:Request,session_id:str|None=None,file:UploadFile|None=File(default=None),db:Session=Depends(get_db),gid:str=Depends(garage)):
    try:
        if file:
            raw=await file.read(settings.max_upload_bytes+1)
            if len(raw)>settings.max_upload_bytes: raise HTTPException(413,"Fichier supérieur à 1 Mio")
            if file.content_type not in {"application/json","text/json","text/csv","application/csv","application/vnd.ms-excel"}: raise HTTPException(415,"Type de fichier non accepté")
            if "csv" in (file.content_type or ""):
                rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8")))); codes=[{"code":r.get("code",""),"status":r.get("status","confirmed")} for r in rows]
                payload={"schema_version":"1.0","vehicle":{"vin":None,"make":rows[0].get("make","Demo Motors"),"model":rows[0].get("model","DM-1"),"year":int(rows[0].get("year","2020")),"engine_code":rows[0].get("engine_code","DEMO-ENG-01")},"scan":{"timestamp":datetime.now().isoformat(),"tool":"csv-demo-import","dtcs":codes,"freeze_frame":{},"live_data":[]}}
            else: payload=json.loads(raw)
        else: payload=await request.json()
        return ingest_obd(OBDReport.model_validate(payload),db,gid,session_id)
    except (ValidationError,json.JSONDecodeError,UnicodeDecodeError,IndexError,ValueError) as e:
        db.rollback(); raise HTTPException(422,f"Rapport OBD invalide : {e}")

@router.post("/imports/knowledge")
def import_knowledge(data:KnowledgeImportPayload,db:Session=Depends(get_db)):
    canonical=json.dumps(data.model_dump(mode="json"),sort_keys=True,separators=(",",":")); checksum=hashlib.sha256(canonical.encode()).hexdigest()
    duplicate=db.scalar(select(KnowledgeSource).where(KnowledgeSource.checksum==checksum))
    if duplicate: return {"imported":False,"duplicate":True,"source_id":duplicate.id,"checksum":checksum,"items_created":0,"warnings":["Ce contenu exact a déjà été importé."]}
    if not data.source.demo_only or not data.vehicle_scope.demo_only or any(not d.demo_only for d in data.dtcs): raise HTTPException(422,"Le premier import exige demo_only=true à tous les niveaux")
    try:
        src=KnowledgeSource(title=data.source.title,source_type=data.source.source_type,publisher="Import contrôlé DiagPilot",version=data.source.version,license_type=data.source.license_type,trust_level=data.source.trust_level,review_status=data.source.review_status,checksum=checksum); db.add(src); db.flush(); count=0
        for entry in data.dtcs:
            dtc=db.scalar(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code==entry.code.upper()))
            if not dtc: dtc=DiagnosticTroubleCode(code=entry.code.upper(),category="powertrain",generic_description="[DÉMO] Définition importée",manufacturer_specific=False,affected_system=entry.system,severity_hint="unknown",source_id=src.id); db.add(dtc); db.flush()
            for typ,rows in (("possible_cause",entry.possible_causes),("test_procedure",entry.test_procedures)):
                for index,row in enumerate(rows):
                    structured=row if isinstance(row,dict) else {"value":row}; title=str(structured.get("title") or structured.get("id") or row)
                    db.add(KnowledgeItem(source_id=src.id,dtc_id=dtc.id,system=entry.system,component=str(structured.get("component","unspecified_demo")),item_type=typ,title=title,content=f"[DÉMO] {title}",structured_data={**structured,"demo_only":True},confidence_level="demo",human_verified=data.source.review_status=="reviewed")); count+=1
        db.commit(); return {"imported":True,"duplicate":False,"source_id":src.id,"checksum":checksum,"items_created":count,"warnings":["Corpus fictif uniquement."]}
    except Exception:
        db.rollback(); raise
