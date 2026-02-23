from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# --- Indexing Models ---

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

# --- Query Models ---

class QueryRequest(BaseModel):
    """General RAG query request"""
    prompt: str = Field(..., description="Natural language question to ask")
    patient_seq: Optional[str] = Field(
        default=None,
        description="Optional: Patient ID (seq) to filter history"
    )

class ChatRequest(BaseModel):
    """Conversational RAG request"""
    prompt: str = Field(..., description="Natural language question or reply")
    session_id: str = Field(..., description="Unique ID for tracking conversation history")
    patient_seq: Optional[str] = Field(
        default=None,
        description="Optional: Patient ID (seq) to retrieve specific medical context"
    )
    reset: bool = Field(
        default=False,
        description="Set to true to wipe the conversation memory for this session ID"
    )

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
