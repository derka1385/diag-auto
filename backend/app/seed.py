import hashlib, json
from pathlib import Path
from sqlalchemy import select
from app.database.models import Base, DiagnosticRule, DiagnosticTroubleCode, Garage, KnowledgeItem, KnowledgeSource, User, VehicleProfile
from app.database.session import SessionLocal, engine

GARAGE_ID="00000000-0000-0000-0000-000000000001"
USER_ID="00000000-0000-0000-0000-000000000002"
VEHICLE_ID="00000000-0000-0000-0000-000000000003"
SOURCE_ID="00000000-0000-0000-0000-000000000004"
CATALOG_SOURCE_ID="00000000-0000-0000-0000-000000000005"

def import_dtc_catalog(db):
    candidates=[Path.cwd()/"data/fixtures/dtc_catalog.json",Path(__file__).resolve().parents[2]/"data/fixtures/dtc_catalog.json"]
    path=next((candidate for candidate in candidates if candidate.exists()),None)
    if not path: return {"imported":0,"updated":0,"missing_fixture":True}
    payload=json.loads(path.read_text())
    if payload.get("schema_version")!="1.0" or payload.get("input_report",{}).get("missing"):
        raise ValueError("Catalogue DTC invalide ou incomplet")
    metadata=payload["source"]
    source=db.get(KnowledgeSource,CATALOG_SOURCE_ID)
    if not source:
        source=KnowledgeSource(id=CATALOG_SOURCE_ID,title=metadata["title"],source_type=metadata["source_type"],publisher=metadata["publisher"],version=metadata["source_commit"][:12],license_type=metadata["license_type"],source_url=metadata["source_url"],local_file_path="data/fixtures/dtc_catalog.json",checksum=payload["content_checksum_sha256"],trust_level=metadata["trust_level"],review_status=metadata["review_status"])
        db.add(source); db.flush()
    imported=updated=0
    for definition in payload["definitions"]:
        dtc=db.scalar(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code==definition["code"]))
        if dtc:
            dtc.generic_description=definition["description_en"]; dtc.source_id=source.id; dtc.manufacturer_specific=False; updated+=1
        else:
            db.add(DiagnosticTroubleCode(code=definition["code"],category="powertrain",generic_description=definition["description_en"],manufacturer_specific=False,affected_system="powertrain_unspecified",severity_hint="unknown",source_id=source.id)); imported+=1
    return {"imported":imported,"updated":updated,"missing_fixture":False}

def seed(db=None):
    owns=db is None; db=db or SessionLocal(); Base.metadata.create_all(engine)
    try:
        if not db.get(Garage,GARAGE_ID): db.add(Garage(id=GARAGE_ID,name="Atelier Démonstration"))
        if not db.get(User,USER_ID): db.add(User(id=USER_ID,garage_id=GARAGE_ID,email="tech@demo.invalid",display_name="Technicien Démo",role="technician"))
        if not db.get(VehicleProfile,VEHICLE_ID): db.add(VehicleProfile(id=VEHICLE_ID,garage_id=GARAGE_ID,make="Demo Motors",model="DM-1",year=2020,market="generic_demo",engine_name="Generic 1.6 Demo",engine_code="DEMO-ENG-01",fuel_type="gasoline",transmission="manual",notes="Véhicule entièrement fictif. Ne pas utiliser sur un véhicule réel.",is_demo_vehicle=True))
        checksum=hashlib.sha256(b"diagpilot-demo-ignition-v1").hexdigest()
        if not db.get(KnowledgeSource,SOURCE_ID): db.add(KnowledgeSource(id=SOURCE_ID,title="Demo ignition diagnostic knowledge",source_type="internal_demo",publisher="DiagPilot demonstration",version="1.0",license_type="internal_demo",trust_level="demo",review_status="reviewed",checksum=checksum,local_file_path="data/fixtures/demo_knowledge.json"))
        db.flush()
        dtcs=[("P0301","Raté d’allumage détecté cylindre 1","engine_ignition","medium"),("P0351","Circuit primaire/secondaire bobine A","engine_ignition","high"),("P0171","Mélange trop pauvre banc 1","fuel_air_metering","high"),("P0101","Plage/performance mesure d’air","fuel_air_metering","medium")]
        for code,desc,system,severity in dtcs:
            if not db.scalar(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code==code)):
                db.add(DiagnosticTroubleCode(code=code,category="powertrain",generic_description=f"[DÉMO] {desc}",manufacturer_specific=False,affected_system=system,severity_hint=severity,source_id=SOURCE_ID))
        db.flush(); p0301=db.scalar(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code=="P0301"))
        if not db.scalar(select(KnowledgeItem).where(KnowledgeItem.title=="Permutation contrôlée des bobines 1 et 2")):
            items=[
              ("possible_cause","ignition_coil_1","Bobine cylindre 1 possible","Le code seul ne suffit pas. Une permutation contrôlée peut tester si le raté suit la bobine.",{"demo_only":True,"ranking_weight":65}),
              ("test_procedure","ignition_coil_1","Permutation contrôlée des bobines 1 et 2","Couper le contact, refroidir, permuter puis relever les DTC en lecture seule.",{"demo_only":True,"outcomes":["fault_moved_to_cylinder_2","fault_stayed_on_cylinder_1"]}),
              ("safety_warning","engine_ignition","Avertissement allumage","Risque électrique et thermique. Données fictives non applicables à un véhicule réel.",{"demo_only":True,"severity":"danger"}),
              ("technical_note","spark_plug_1","Bougie comme cause alternative","Si le raté ne suit pas la bobine, inspecter la bougie puis poursuivre vers injection et étanchéité.",{"demo_only":True})]
            for typ,component,title,content,data in items: db.add(KnowledgeItem(source_id=SOURCE_ID,vehicle_profile_id=VEHICLE_ID,dtc_id=p0301.id,system="engine_ignition",component=component,item_type=typ,title=title,content=content,structured_data=data,confidence_level="demo",human_verified=True))
        db.flush()
        for item in db.scalars(select(KnowledgeItem).where(KnowledgeItem.dtc_id==p0301.id,KnowledgeItem.source_id==SOURCE_ID)).all():
            item.structured_data={**(item.structured_data or {}),"compatibility_scope":{"make":"Demo Motors","model":"DM-1","engine_code":"DEMO-ENG-01"}}
        if not db.scalar(select(DiagnosticRule).where(DiagnosticRule.name=="P0301 initial coil swap")):
            db.add(DiagnosticRule(vehicle_profile_id=VEHICLE_ID,dtc_id=p0301.id,name="P0301 initial coil swap",conditions={"dtc":"P0301","prior_results":[]},action={"step":"swap_coils_1_2","branches":{"fault_moved_to_cylinder_2":"confirm_coil","fault_stayed_on_cylinder_1":"inspect_spark_plug"}},priority=100,enabled=True,source_ids=[SOURCE_ID],human_verified=True))
        import_dtc_catalog(db)
        db.commit()
    finally:
        if owns: db.close()

if __name__=="__main__": seed()
