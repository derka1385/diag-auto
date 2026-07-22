from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator

class Strict(BaseModel): model_config=ConfigDict(extra="forbid")
class InterpretedFaultCode(Strict):
    code:str; ecu:str|None=None; meaning:str; sourceStatus:Literal["provided_by_database","ai_general_knowledge","not_found"]; relevance:Literal["primary","secondary","consequence","unknown"]
class Correlation(Strict): relatedCodes:list[str]; explanation:str; confidence:float=Field(ge=0,le=1)
class Hypothesis(Strict):
    id:str; label:str; component:str|None=None; confidence:float=Field(ge=0,le=1); supportingEvidence:list[str]; contradictingEvidence:list[str]; requiredConfirmation:list[str]; status:Literal["possible","likely","unlikely","confirmed","rejected"]
class ImageEvidence(Strict): imageId:str; observation:str; confidence:float=Field(ge=0,le=1); limitations:list[str]
class Urgency(Strict):
    level:Literal["low","medium","high","critical"]; explanation:str; drivingRecommendation:Literal["normal_use","limited_use","stop_as_soon_as_safe","do_not_drive","insufficient_information"]
class MissingInformation(Strict): field:str; reason:str; howToObtain:str; priority:Literal["low","medium","high"]
class ExpectedResultAI(Strict): outcome:str; interpretation:str; nextAction:str
class NextCheck(Strict):
    id:str; order:int=Field(ge=1); title:str; objective:str; prerequisites:list[str]; instructions:list[str]; safetyWarnings:list[str]; expectedResults:list[ExpectedResultAI]; requiredTools:list[str]; estimatedDifficulty:Literal["easy","intermediate","advanced"]
class FinalConclusion(Strict): status:Literal["insufficient_information","testing_required","probable_cause_identified","cause_confirmed"]; summary:str
class DiagnosticAnalysis(Strict):
    schemaVersion:Literal["1.0"]; caseSummary:str; reasoningApproach:str; interpretedFaultCodes:list[InterpretedFaultCode]; correlations:list[Correlation]; hypotheses:list[Hypothesis]; imageEvidence:list[ImageEvidence]; urgency:Urgency; missingInformation:list[MissingInformation]; nextChecks:list[NextCheck]; finalConclusion:FinalConclusion; warnings:list[str]
    @field_validator("hypotheses")
    @classmethod
    def ranked(cls,value):
        if any(value[i].confidence<value[i+1].confidence for i in range(len(value)-1)): raise ValueError("Les hypothèses doivent être classées par confiance décroissante")
        return value

class DiagnosticCreate(Strict):
    vehicle_id:str; mileage:int|None=Field(default=None,ge=0); symptoms:str=Field(min_length=3,max_length=5000); circumstances:str=Field(default="",max_length=3000)
class FaultCodeInput(Strict):
    code:str; ecu:str|None=Field(default=None,max_length=100); status:Literal["active","intermittent","stored","unknown"]="unknown"; freeze_frame:dict={}
    @field_validator("code")
    @classmethod
    def normalize(cls,value):
        import re
        value=value.strip().upper()
        if not re.fullmatch(r"[PBCU][0-9A-F]{4}",value): raise ValueError("Code défaut invalide")
        return value
class FaultCodesInput(Strict): fault_codes:list[FaultCodeInput]=Field(min_length=1,max_length=30)
class MeasurementInput(Strict): name:str=Field(min_length=1,max_length=100); value:float|str|bool; unit:str|None=Field(default=None,max_length=30); conditions:str=Field(default="",max_length=500); source:Literal["manual","obd","image"]="manual"
class StepResultInput(Strict): outcome:str=Field(min_length=1,max_length=500); measurement:float|None=None; unit:str|None=Field(default=None,max_length=30); comment:str=Field(default="",max_length=2000)
