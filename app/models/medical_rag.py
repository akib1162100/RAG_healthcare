"""
Pydantic Models for Medical RAG Operations
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime


class IndexMedicalRequest(BaseModel):
    """Request to index medical data"""
    models: List[str] = Field(
        default=['wk.appointment', 'prescription.order.knk'],
        description="List of Odoo models to index"
    )
    incremental: bool = Field(
        default=True,
        description="If True, only index new/modified records"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of records to index per model"
    )
    days: Optional[int] = Field(
        default=None,
        description="Only index records from last N days"
    )


class IndexMedicalResponse(BaseModel):
    """Response from medical data indexing"""
    status: str
    results: dict
    total_records: int
    total_chunks: int


class PatientQueryRequest(BaseModel):
    """Request to query patient-specific medical history"""
    patient_seq: str = Field(
        ...,
        description="Patient ID (e.g., '202402001')"
    )
    prompt: str = Field(
        ...,
        description="Natural language query about the patient"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of relevant chunks to retrieve"
    )


class PrescriptionQueryRequest(BaseModel):
    """Request to search prescriptions with filters"""
    prompt: str = Field(
        ...,
        description="Natural language query"
    )
    medication: Optional[str] = Field(
        default=None,
        description="Filter by medication name"
    )
    diagnosis_code: Optional[str] = Field(
        default=None,
        description="Filter by ICD diagnosis code"
    )
    physician_id: Optional[int] = Field(
        default=None,
        description="Filter by physician Odoo ID"
    )
    date_from: Optional[date] = Field(
        default=None,
        description="Filter prescriptions from this date"
    )
    date_to: Optional[date] = Field(
        default=None,
        description="Filter prescriptions until this date"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results"
    )


class RAGQueryResponse(BaseModel):
    """Response from RAG query"""
    response: str = Field(
        description="Generated response from LLM"
    )
    sources: List[dict] = Field(
        description="Source documents used for generation"
    )
    metadata: dict = Field(
        default={},
        description="Additional metadata about the query"
    )


class IndexStatusResponse(BaseModel):
    """Response for index status check"""
    index_stats: dict
    etl_metadata: dict
    total_indexed_records: int
    total_chunks: int


# ========================================== #
# 10-SECTION LAYOUT SCHEMAS FOR SINGLE PRESCRIPTIONS #
# ========================================== #

class PatientDemographicsSchema(BaseModel):
    patient_name: str = Field(default="-")
    date_of_birth_age: str = Field(default="-")
    contact: str = Field(default="-")
    presenting_doctor: str = Field(default="-")
    past_medical_history: str = Field(default="-")
    gender: str = Field(default="-")
    hmo_hospital: str = Field(default="-")
    reg_no: str = Field(default="-")

class VitalSignSchema(BaseModel):
    parameter: str = Field(default="-")
    recorded_value: str = Field(default="-")
    status: str = Field(default="-")
    normal_range: str = Field(default="-")

class ChiefComplaintsSchema(BaseModel):
    primary_complaints: List[str] = Field(default_factory=list)
    secondary_background_complaints: List[str] = Field(default_factory=list)

class RedFlagIndicatorsSchema(BaseModel):
    alert_message: Optional[str] = Field(default=None)
    cardiology_red_flags: List[str] = Field(default_factory=list)
    routine_red_flags: List[str] = Field(default_factory=list)

class DiagnosisSchema(BaseModel):
    diagnosis: str = Field(default="-")
    secondary_complication: str = Field(default="-")
    icd_10: str = Field(default="-")
    snomed: str = Field(default="-")
    type: str = Field(default="-")
    specialty: str = Field(default="-")

class MedicationSchema(BaseModel):
    medication_drug_name: str = Field(default="-")
    dose: str = Field(default="-")
    freq: str = Field(default="-")
    route: str = Field(default="-")
    food: str = Field(default="-")
    duration: str = Field(default="-")
    qty: str = Field(default="-")
    margin: str = Field(default="-")

class MedicationsPrescribedSchema(BaseModel):
    date: str = Field(default="-")
    current_medications: List[MedicationSchema] = Field(default_factory=list)
    other_historical_medications: List[str] = Field(default_factory=list)

class InvestigationOrderedSchema(BaseModel):
    category: str = Field(default="-")
    test_panel: str = Field(default="-")
    clinical_indication: str = Field(default="-")

class ClinicalDecisionSchema(BaseModel):
    complaint: str = Field(default="-")
    time_course: str = Field(default="-")
    pattern: str = Field(default="-")
    most_likely_dx: str = Field(default="-")
    next_action: str = Field(default="-")

class AdviseCarePlanSchema(BaseModel):
    lifestyle_diet: List[str] = Field(default_factory=list)
    medication_instructions: List[str] = Field(default_factory=list)
    warning_signs_seek_care: List[str] = Field(default_factory=list)

class FollowUpMonitoringSchema(BaseModel):
    next_visit: str = Field(default="-")
    signature_status: str = Field(default="-")
    investigations: str = Field(default="-")
    referral: str = Field(default="-")

class PrescriptionDetailsResponse(BaseModel):
    """
    Master schema for a single prescription containing the 10 standard layout sections.
    """
    allergy_alert: Optional[str] = Field(default=None)
    patient_demographics: Optional[PatientDemographicsSchema] = Field(default_factory=PatientDemographicsSchema)
    vitals_at_visit: List[VitalSignSchema] = Field(default_factory=list)
    chief_complaints: Optional[ChiefComplaintsSchema] = Field(default_factory=ChiefComplaintsSchema)
    red_flag_indicators: Optional[RedFlagIndicatorsSchema] = Field(default_factory=RedFlagIndicatorsSchema)
    diagnoses: List[DiagnosisSchema] = Field(default_factory=list)
    medications_prescribed: Optional[MedicationsPrescribedSchema] = Field(default_factory=MedicationsPrescribedSchema)
    investigations_ordered: List[InvestigationOrderedSchema] = Field(default_factory=list)
    clinical_decision_mapping: List[ClinicalDecisionSchema] = Field(default_factory=list)
    advise_care_plan: Optional[AdviseCarePlanSchema] = Field(default_factory=AdviseCarePlanSchema)
    follow_up_monitoring_plan: Optional[FollowUpMonitoringSchema] = Field(default_factory=FollowUpMonitoringSchema)

class PatientMedicalSummaryResponse(PrescriptionDetailsResponse):
    """
    Master schema for the rolling / total patient medical summary.
    Inherits identical fields from PrescriptionDetailsResponse to maintain strict UI conformity.
    """
    pass
