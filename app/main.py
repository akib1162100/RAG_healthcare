from fastapi import FastAPI
from app.api.v1.api import api_router
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.etl.pipeline import ETLPipeline
from app.core.config import settings
import app.api.v1.endpoints.rag as rag_endpoints
import app.api.v1.endpoints.etl as etl_endpoints
import app.api.v1.endpoints.config as config_endpoints
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Medical RAG system for Odoo healthcare data with ClinicalBERT embeddings and Google Gemma LLM",
    version=settings.APP_VERSION
)

@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    logger.info("Starting up RAG Healthcare Service...")
    
    # Initialize database tables (pgvector, medical_rag_index, etl_metadata)
    from app.core.db_init import init_database
    from app.core.database import engine
    await init_database(engine)
    
    # Initialize Embedding Service (ClinicalBERT - Local CPU)
    embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL_NAME)
    await embedding_service.initialize()
    
    # Initialize LLM Service (Google Gemma - External API)
    llm_service = LLMService()
    await llm_service.initialize()
    
    # Initialize RAG Service (Orchestrator)
    rag_service = RAGService(
        embedding_service=embedding_service,
        llm_service=llm_service
    )
    
    # Initialize ETL Pipeline
    etl_pipeline = ETLPipeline()
    
    # Set global instances in endpoint modules
    rag_endpoints.embedding_service = embedding_service
    rag_endpoints.llm_service = llm_service
    rag_endpoints.rag_service = rag_service
    etl_endpoints.etl_pipeline = etl_pipeline
    config_endpoints.llm_service = llm_service
    
    logger.info("RAG Healthcare Service ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RAG Healthcare Service...")
    
    # Close ETL pipeline if needed
    if etl_endpoints.etl_pipeline:
        await etl_endpoints.etl_pipeline.close()
    
    logger.info("RAG Healthcare Service shutdown complete")

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Add a legacy/alias endpoint for older cached Odoo modules sending requests to /chat root directly
from app.models.schemas import ChatRequest, RAGQueryResponse
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

@app.post("/chat", response_model=RAGQueryResponse)
async def chat_rag_alias(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Alias for POST /api/v1/rag/chat 
    Resolves a cache-staleness issue in Odoo where it requests the root /chat endpoint.
    """
    return await rag_endpoints.chat_rag(request=request, session=session, rag=rag_endpoints.rag_service)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
