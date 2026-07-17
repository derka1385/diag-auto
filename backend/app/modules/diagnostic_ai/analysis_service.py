import hashlib,json,uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.models import AICall,DiagnosticEvent,DiagnosticHypothesis,DiagnosticSession,DiagnosticStep,now
from .context_builder import DiagnosticContextBuilder
from app.core.config import settings
from .providers import AIInvalidResponse,AIProviderUnavailable,PROMPT_VERSION,get_ai_provider
from .schemas import DiagnosticAnalysis

class AnalysisInProgress(Exception):pass

def _event(db,case,kind,payload):db.add(DiagnosticEvent(session_id=case.id,event_type=kind,payload=payload,actor_type="system",actor_id=None))

def _persist(db,case,result,context_hash,operation):
    payload=result.analysis.model_dump(mode="json");body=json.dumps(payload,sort_keys=True,ensure_ascii=False)
    run=AICall(session_id=case.id,provider=result.provider,model=result.model,operation_type=operation,status="completed",schema_version="1.0",prompt_version=PROMPT_VERSION,request_id=str(uuid.uuid4()),input_hash=context_hash,output_hash=hashlib.sha256(body.encode()).hexdigest(),output_payload=payload,validation_status="repaired" if result.repaired else "valid",error_safe=None,latency_ms=result.latency_ms,token_usage=result.token_usage);db.add(run);db.flush()
    for old in db.scalars(select(DiagnosticHypothesis).where(DiagnosticHypothesis.session_id==case.id,DiagnosticHypothesis.status.in_(["active","possible","likely"]))).all():old.status="superseded"
    for h in result.analysis.hypotheses:
        db.add(DiagnosticHypothesis(session_id=case.id,title=h.label,suspected_component=h.component or "not_determined",probability_score=h.confidence*100,confidence_label="high" if h.confidence>=.75 else "medium" if h.confidence>=.4 else "low",reasoning="; ".join(h.requiredConfirmation) or "Hypothèse à confirmer",supporting_evidence=h.supportingEvidence,contradicting_evidence=h.contradictingEvidence,source_ids=[],status=h.status))
    for old_step in db.scalars(select(DiagnosticStep).where(DiagnosticStep.session_id==case.id,DiagnosticStep.status.in_(["current","pending"]))).all():old_step.status="superseded"
    base=db.scalar(select(DiagnosticStep.step_order).where(DiagnosticStep.session_id==case.id).order_by(DiagnosticStep.step_order.desc())) or 0
    for i,check in enumerate(result.analysis.nextChecks):
        db.add(DiagnosticStep(session_id=case.id,step_order=base+i+1,title=check.title,objective=check.objective,instructions=check.instructions,required_tools=check.requiredTools,expected_results=[{"result_id":f"{check.id}:{j}","label":x.outcome,"meaning":x.interpretation,"next_action":x.nextAction} for j,x in enumerate(check.expectedResults)],safety_notes=check.safetyWarnings,source_ids=[],status="current" if i==0 else "pending",result=None,technician_comment=None,hypotheses_before=[x.model_dump() for x in result.analysis.hypotheses],hypotheses_after=[]))
    case.status="in_progress";case.analysis_started_at=None;case.analysis_context_hash=context_hash;case.urgency_level=result.analysis.urgency.level;case.current_summary=result.analysis.caseSummary;case.prompt_version=PROMPT_VERSION;case.ai_model=result.model
    _event(db,case,"ai_analysis_completed",{"ai_run_id":run.id,"provider":result.provider,"model":result.model,"operation":operation,"validation_status":run.validation_status});db.commit();return payload

async def analyze_case(db:Session,case:DiagnosticSession,follow_up=False):
    if case.status=="analyzing":raise AnalysisInProgress("Une analyse est déjà en cours")
    context,images=DiagnosticContextBuilder().build(db,case)
    if not context["fault_codes"]:raise ValueError("Ajoutez au moins un code défaut")
    canonical=DiagnosticContextBuilder.canonical(context);context_hash=hashlib.sha256(canonical.encode()).hexdigest();operation="follow_up" if follow_up else "initial_analysis"
    cached=db.scalar(select(AICall).where(AICall.session_id==case.id,AICall.input_hash==context_hash,AICall.operation_type==operation,AICall.status=="completed",AICall.output_payload.is_not(None)).order_by(AICall.created_at.desc()))
    if cached:return DiagnosticAnalysis.model_validate(cached.output_payload).model_dump(mode="json")
    previous=case.status;case.status="analyzing";case.analysis_started_at=now();db.commit()
    provider=get_ai_provider()
    try:result=await (provider.analyze_follow_up(context,images) if follow_up else provider.analyze_initial_case(context,images));return _persist(db,case,result,context_hash,operation)
    except Exception as exc:
        db.rollback();fresh=db.get(DiagnosticSession,case.id);fresh.status=previous if previous!="analyzing" else "draft";fresh.analysis_started_at=None
        safe=str(exc) if isinstance(exc,(AIProviderUnavailable,AIInvalidResponse,ValueError)) else "Erreur interne du fournisseur IA"
        db.add(AICall(session_id=case.id,provider=settings.llm_provider,model="unavailable",operation_type=operation,status="failed",schema_version="1.0",prompt_version=PROMPT_VERSION,request_id=str(uuid.uuid4()),input_hash=context_hash,output_hash=None,output_payload=None,validation_status="failed",error_safe=safe[:300],latency_ms=0,token_usage=None));db.commit();raise
