"""
API Router for ETL/Indexing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.models.schemas import IndexMedicalRequest, IndexMedicalResponse, IndexStatusResponse
from app.etl.pipeline import ETLPipeline
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/etl", tags=["ETL"])

# Global ETL pipeline instance
etl_pipeline: ETLPipeline = None

async def get_etl_pipeline() -> ETLPipeline:
    """Dependency to get ETL pipeline"""
    if not etl_pipeline:
        raise HTTPException(status_code=503, detail="ETL pipeline not initialized")
    return etl_pipeline

@router.post("/index-medical", response_model=IndexMedicalResponse)
async def index_medical(
    request: IndexMedicalRequest,
    pipeline: ETLPipeline = Depends(get_etl_pipeline)
):
    """
    Trigger ETL pipeline to index medical data from Odoo
    
    - **models**: List of Odoo models to index
    - **incremental**: Only index new/modified records
    - **limit**: Max records per model
    - **days**: Only index records from last N days
    """
    try:
        logger.info(f"Starting medical data indexing: {request.models}")
        
        results = await pipeline.run_full_indexing(
            models=request.models,
            limit=request.limit,
            incremental=request.incremental
        )
        
        total_records = sum(r['records_indexed'] for r in results.values())
        total_chunks = sum(r['chunks_created'] for r in results.values())
        
        logger.info(f"Indexing complete: {total_records} records, {total_chunks} chunks")
        
        return IndexMedicalResponse(
            status="success",
            results=results,
            total_records=total_records,
            total_chunks=total_chunks
        )
        
    except Exception as e:
        logger.error(f"Medical indexing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_medical_data(
    background_tasks: BackgroundTasks,
    pipeline: ETLPipeline = Depends(get_etl_pipeline)
):
    """
    Trigger an auto-sync in the background.
    Incrementally pulls latest medical records from Odoo.
    Returns immediately while processing continues in background.
    """
    try:
        logger.info("Scheduling background auto-sync...")
        
        # Add the indexing task to background pool
        background_tasks.add_task(
            pipeline.run_full_indexing,
            models=['wk.appointment', 'prescription.order.knk'],
            incremental=False
        )
        
        return {
            "status": "success",
            "message": "Auto-sync started in the background"
        }
        
    except Exception as e:
        logger.error(f"Auto-sync scheduling error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/index-status", response_model=IndexStatusResponse)
async def index_status(pipeline: ETLPipeline = Depends(get_etl_pipeline)):
    """
    Check current indexing status for all medical models
    
    Returns statistics about indexed records and chunks
    """
    try:
        status = await pipeline.get_index_status()
        
        total_records = sum(
            m.get('total_records', 0) 
            for m in status.get('etl_metadata', {}).values()
        )
        total_chunks = sum(
            s.get('total_chunks', 0) 
            for s in status.get('index_stats', {}).values()
        )
        
        return IndexStatusResponse(
            index_stats=status.get('index_stats', {}),
            etl_metadata=status.get('etl_metadata', {}),
            total_indexed_records=total_records,
            total_chunks=total_chunks
        )
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
