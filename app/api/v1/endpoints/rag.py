"""
API Router for RAG endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.schemas import QueryRequest, ChatRequest, RAGQueryResponse
from app.services.rag_service import RAGService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])

# Global service instances (initialized at startup)
embedding_service: EmbeddingService = None
llm_service: LLMService = None
rag_service: RAGService = None

async def get_rag_service() -> RAGService:
    """Dependency to get RAG service"""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    return rag_service

@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: QueryRequest,
    session: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service)
):
    """
    General RAG query endpoint
    
    - **prompt**: Natural language question
    - **patient_seq**: Optional patient ID to restrict context to that patient
    """
    try:
        # Build metadata filter for patient-specific queries
        metadata_filter = {}
        if request.patient_seq:
            metadata_filter['patient_seq'] = request.patient_seq
            
        # If filtering by patient, strictly confine LLM to their history
        system_instruction = None
        if metadata_filter:
            system_instruction = (
                "You are a medical AI assistant tailored to analyze a specific patient's context. "
                "The provided context contains the known medical history for this patient. "
                "If the user asks about a symptom or condition that is NOT explicitly mentioned "
                "in the records, DO NOT simply say it's not present. Instead, analyze the patient's "
                "existing medical history (e.g., past diseases, medications, chief complaints like heart issues) "
                "and provide medical guidance on how the new symptom might be related to their known underlying conditions. "
                "Offer plausible connections based on medical knowledge and strongly advise seeking immediate care "
                "if their history warrants it."
            )
        
        result = await rag.query(
            prompt=request.prompt,
            session=session,
            limit=5,
            metadata_filter=metadata_filter if metadata_filter else None,
            system_instruction=system_instruction
        )
        
        return RAGQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=RAGQueryResponse)
async def chat_rag(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service)
):
    """
    Conversational RAG query endpoint that remembers previous messages in a session
    
    - **prompt**: Natural language question
    - **session_id**: Unique identifier string for conversation history
    - **patient_seq**: Optional patient ID to restrict context to that patient
    - **reset**: If True, wipes the memory context for the provided session_id
    """
    try:
        # Build metadata filter for patient-specific queries
        metadata_filter = {}
        if request.patient_seq:
            metadata_filter['patient_seq'] = request.patient_seq
            
        # If filtering by patient, strictly confine LLM to their history
        system_instruction = None
        if metadata_filter:
            system_instruction = (
                "You are a medical AI assistant tailored to analyze a specific patient's context. "
                "The provided context contains the known medical history for this patient. "
                "If the user asks about a symptom or condition that is NOT explicitly mentioned "
                "in the records, DO NOT simply say it's not present. Instead, analyze the patient's "
                "existing medical history (e.g., past diseases, medications, chief complaints like heart issues) "
                "and provide medical guidance on how the new symptom might be related to their known underlying conditions. "
                "Offer plausible connections based on medical knowledge and strongly advise seeking immediate care "
                "if their history warrants it."
            )
        
        result = await rag.chat(
            prompt=request.prompt,
            session_id=request.session_id,
            session=session,
            reset=request.reset,
            limit=5,
            metadata_filter=metadata_filter if metadata_filter else None,
            system_instruction=system_instruction,
            chat_history=request.chat_history,
        )
        
        return RAGQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

from typing import Optional

@router.get("/patient-data")
async def get_patient_data(
    patient_seq: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieve raw indexed medical records.
    If patient_seq is provided, returns records for that patient.
    If no patient_seq is provided, returns all indexed records across all patients.
    Bypasses the LLM and returns the exact data chunks stored in the vector database.
    """
    try:
        from app.repositories.vector_repository import VectorRepository
        
        repo = VectorRepository(session)
        records = await repo.get_patient_records(patient_seq)
        
        message = "No medical records found." if not records else f"Successfully retrieved {'all records' if not patient_seq else 'patient records'}"
            
        return {
            "status": "success",
            "patient_seq": patient_seq or "ALL",
            "message": message,
            "total_records": len(records),
            "data": records
        }
        
    except Exception as e:
        logger.error(f"Error fetching patient data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prescriptions")
async def get_prescription_data(
    patient_seq: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieve raw indexed prescription records.
    If patient_seq is provided, returns prescriptions for that patient.
    If no patient_seq is provided, returns all indexed prescriptions across all patients.
    Bypasses the LLM and returns the exact data chunks stored in the vector database.
    """
    try:
        from app.repositories.vector_repository import VectorRepository
        
        repo = VectorRepository(session)
        records = await repo.get_prescription_records(patient_seq)
        
        message = "No prescription records found." if not records else f"Successfully retrieved {'all prescriptions' if not patient_seq else 'patient prescriptions'}"
            
        return {
            "status": "success",
            "patient_seq": patient_seq or "ALL",
            "message": message,
            "total_records": len(records),
            "data": records
        }
        
    except Exception as e:
        logger.error(f"Error fetching prescription data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


