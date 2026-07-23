import json
from typing import Protocol
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.models import DiagnosticImage,DiagnosticObservation,DiagnosticSession,DiagnosticStep,DiagnosticTroubleCode,KnowledgeItem,VehicleConfiguration

class TechnicalKnowledgeRetriever(Protocol):
    def search(self,db:Session,vehicle:dict,fault_codes:list[str],symptoms:str,query:str)->list[dict]: ...

class LocalKnowledgeRetriever:
    def search(self,db,vehicle,fault_codes,symptoms,query):
        dtcs=db.scalars(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code.in_(fault_codes))).all(); ids=[x.id for x in dtcs]
        rows=db.scalars(select(KnowledgeItem).where(KnowledgeItem.dtc_id.in_(ids))).all() if ids else []
        return [{"id":x.id,"title":x.title,"source_id":x.source_id,"excerpt":x.content[:1200],"vehicle_scope":(x.structured_data or {}).get("compatibility_scope",{})} for x in rows[:20]]

def _text(value,limit): return str(value or "").replace("\x00","")[:limit]

class DiagnosticContextBuilder:
    def __init__(self,retriever=None):self.retriever=retriever or LocalKnowledgeRetriever()
    def build(self,db:Session,case:DiagnosticSession)->tuple[dict,list[DiagnosticImage]]:
        config=db.scalar(select(VehicleConfiguration).where(VehicleConfiguration.vehicle_id==case.vehicle_profile_id)); vehicle=case.vehicle
        normalized={"vehicle_id":vehicle.id,"make":config.make if config and config.make else vehicle.make,"model":config.model if config and config.model else vehicle.model,"generation":config.generation if config else None,"variant":config.type_variant_version if config else None,"model_year":config.model_year if config and config.model_year else vehicle.year,"market":config.market if config and config.market else vehicle.market,"engine_name":config.engine_name if config and config.engine_name else vehicle.engine_name,"engine_code":config.engine_code_confirmed_by_user or config.engine_code if config else (vehicle.engine_code if vehicle.engine_code!="UNKNOWN" else None),"engine_family":config.engine_family if config else None,"engine_displacement_cc":config.engine_displacement_cc if config else None,"engine_power_hp":config.engine_power_hp if config else None,"fuel_type":config.fuel_type if config and config.fuel_type else vehicle.fuel_type,"emission_standard":config.emission_standard if config else None,"transmission_type":config.transmission_type if config and config.transmission_type else vehicle.transmission,"transmission_code":config.transmission_code if config else None,"transmission_gears":config.transmission_gears if config else None,"drivetrain":config.drivetrain if config else None,"engine_ecu_manufacturer":config.engine_ecu_manufacturer if config else None,"engine_ecu_model":config.engine_ecu_model if config else None,"tecdoc_k_type":config.tecdoc_k_type if config else None,"cnit":config.cnit if config else None,"identification_confidence":config.confidence_score if config else 0,"configuration_confirmed":bool(config and config.confirmed_by_user),"user_confirmed":bool(config and config.confirmed_by_user),"precision_level":config.precision_level if config else "basic_vehicle"}
        observations=db.scalars(select(DiagnosticObservation).where(DiagnosticObservation.session_id==case.id).order_by(DiagnosticObservation.created_at.desc())).all()
        dtcs=[x for x in observations if x.observation_type=="DTC"]; measurements=[x for x in observations if x.observation_type=="measurement"][:30]
        codes=[x.key for x in dtcs]; definitions=[]
        for code in codes:
            row=db.scalar(select(DiagnosticTroubleCode).where(DiagnosticTroubleCode.code==code))
            manufacturer_specific=bool(row.manufacturer_specific) if row else (len(code)>1 and code[1]!="0")
            tier=row.confidence_tier if row and row.confidence_tier else "unknown"
            definitions.append({"code":code,"description":row.generic_description if row and row.generic_description else None,"source_id":row.source_id if row else None,"manufacturer_specific":manufacturer_specific,"definition_reliability":tier,"probable_family":row.probable_family_fr if row else None,"control_points":row.control_points_fr if row else None,"approximation_source":row.approximation_source_url if row else None})
        steps=db.scalars(select(DiagnosticStep).where(DiagnosticStep.session_id==case.id,DiagnosticStep.status=="completed").order_by(DiagnosticStep.step_order.desc())).all()
        images=db.scalars(select(DiagnosticImage).where(DiagnosticImage.session_id==case.id,DiagnosticImage.processing_status=="ready").order_by(DiagnosticImage.created_at)).all()
        context={"vehicle":normalized,"fault_codes":[{"code":x.key,"ecu":(x.value or {}).get("ecu"),"status":(x.value or {}).get("status","unknown"),"freeze_frame":(x.value or {}).get("freeze_frame",{})} for x in dtcs],"technical_definitions":definitions,"measurements":[{"name":x.key,"value":x.value,"unit":x.unit,"source":x.source} for x in measurements],"previous_steps":[{"order":x.step_order,"title":x.title,"result":x.result,"comment":_text(x.technician_comment,500)} for x in steps[:10]],"images":[{"id":x.id,"category":x.category,"description":_text(x.description,500),"ocr":x.extraction_result} for x in images],"untrusted_user_data":{"symptoms":_text(case.observed_symptoms,5000),"circumstances":_text(case.appearance_circumstances,3000)},"technical_excerpts":self.retriever.search(db,normalized,codes,case.observed_symptoms,"diagnostic controls")}
        return context,images

    @staticmethod
    def canonical(context):return json.dumps(context,sort_keys=True,separators=(",",":"),ensure_ascii=False)
