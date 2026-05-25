"""
API Router for ETL/Indexing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.models.schemas import IndexMedicalRequest, IndexMedicalResponse, IndexStatusResponse
from app.etl.pipeline import ETLPipeline
from app.core.config import settings
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


def _resolve_pipeline(base_pipeline: ETLPipeline, instance_id: str = None) -> ETLPipeline:
    if not instance_id or instance_id == base_pipeline.instance_id:
        return base_pipeline
    instance_config = next(
        (cfg for cfg in settings.get_odoo_instances() if cfg["instance_id"] == instance_id),
        None,
    )
    if not instance_config:
        raise HTTPException(status_code=400, detail=f"Unknown instance_id: {instance_id}")
    return ETLPipeline(instance_config=instance_config)

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
    active_pipeline = None
    try:
        active_pipeline = _resolve_pipeline(pipeline, request.instance_id)
        logger.info(f"Starting medical data indexing: {request.models} [instance={active_pipeline.instance_id}]")

        results = await active_pipeline.run_full_indexing(
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
    finally:
        if active_pipeline and active_pipeline is not pipeline:
            await active_pipeline.close()

@router.post("/index-medical-all", response_model=IndexMedicalResponse)
async def index_medical_all(
    instance_id: str = None,
    pipeline: ETLPipeline = Depends(get_etl_pipeline)
):
    """
    Force a full re-indexing of all medical models from Odoo.
    Ignores sync flags and fetches all records.
    """
    active_pipeline = None
    try:
        active_pipeline = _resolve_pipeline(pipeline, instance_id)
        models = ['res.partner', 'medical.disease', 'wk.appointment', 'prescription.order.knk']
        logger.info(f"Starting FULL medical data indexing for: {models} [instance={active_pipeline.instance_id}]")
        
        results = await active_pipeline.run_full_indexing(
            models=models,
            limit=None,
            incremental=False
        )
        
        total_records = sum(r['records_indexed'] for r in results.values())
        total_chunks = sum(r['chunks_created'] for r in results.values())
        
        logger.info(f"Full indexing complete: {total_records} records, {total_chunks} chunks")
        
        return IndexMedicalResponse(
            status="success",
            results=results,
            total_records=total_records,
            total_chunks=total_chunks
        )
        
    except Exception as e:
        logger.error(f"Full medical indexing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if active_pipeline and active_pipeline is not pipeline:
            await active_pipeline.close()

@router.post("/sync")
async def sync_medical_data(
    background_tasks: BackgroundTasks,
    instance_id: str = None,
    pipeline: ETLPipeline = Depends(get_etl_pipeline)
):
    """
    Trigger an auto-sync in the background.
    Incrementally pulls latest medical records from Odoo.
    Returns immediately while processing continues in background.
    """
    try:
        active_pipeline = _resolve_pipeline(pipeline, instance_id)
        logger.info("Scheduling background auto-sync...")
        
        # Add the indexing task to background pool
        background_tasks.add_task(
            active_pipeline.run_full_indexing,
            models=['wk.appointment', 'prescription.order.knk'],
            incremental=True
        )
        
        return {
            "status": "success",
            "message": "Auto-sync started in the background"
        }
        
    except Exception as e:
        logger.error(f"Auto-sync scheduling error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/index-status", response_model=IndexStatusResponse)
async def index_status(instance_id: str = None, pipeline: ETLPipeline = Depends(get_etl_pipeline)):
    """
    Check current indexing status for all medical models
    
    Returns statistics about indexed records and chunks
    """
    active_pipeline = None
    try:
        active_pipeline = _resolve_pipeline(pipeline, instance_id)
        status = await active_pipeline.get_index_status()
        
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
    finally:
        if active_pipeline and active_pipeline is not pipeline:
            await active_pipeline.close()

@router.post("/flush-db")
async def flush_db(instance_id: str = None, pipeline: ETLPipeline = Depends(get_etl_pipeline)):
    """Temporary endpoint to completely wipe the RAG database tables."""
    active_pipeline = None
    try:
        from sqlalchemy import text
        active_pipeline = _resolve_pipeline(pipeline, instance_id)
        async with active_pipeline.engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM medical_rag_index WHERE odoo_instance_id = :instance_id"),
                {"instance_id": active_pipeline.instance_id},
            )
            await conn.execute(
                text("DELETE FROM etl_metadata WHERE odoo_instance_id = :instance_id"),
                {"instance_id": active_pipeline.instance_id},
            )
        return {"status": "success", "message": f"Database rows deleted for instance {active_pipeline.instance_id}"}
    except Exception as e:
        logger.error(f"Flush error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if active_pipeline and active_pipeline is not pipeline:
            await active_pipeline.close()


@router.post("/push-record")
async def push_record(
    request: dict,
    background_tasks: BackgroundTasks,
    pipeline: ETLPipeline = Depends(get_etl_pipeline),
):
    """
    Instant indexing of a single record pushed from Odoo on create/write.

    Payload:
        {
            "model": "prescription.order.knk",
            "res_id": 12345,
            "data": { ... normalized fields matching ETL schema ... }
        }

    The record is transformed, embedded and stored in the vector DB (~200ms).
    No LLM call is made — this is purely vector indexing.
    """
    import json as _json

    model = request.get("model")
    res_id = request.get("res_id")
    data = request.get("data")

    if not model or not data:
        raise HTTPException(status_code=400, detail="'model' and 'data' are required")

    active_pipeline = _resolve_pipeline(pipeline, request.get("instance_id"))

    try:
        # 1. Transform — reuse existing transformer
        if model == "prescription.order.knk":
            chunks_with_metadata = active_pipeline.transformer.flatten_prescription(data)
        elif model == "wk.appointment":
            text_content, metadata = active_pipeline.transformer.flatten_appointment(data)
            metadata["chunk_index"] = 0
            metadata["total_chunks"] = 1
            chunks_with_metadata = [(text_content, metadata)]
        elif model == "res.partner":
            text_content, metadata = active_pipeline.transformer.flatten_patient(data)
            metadata["chunk_index"] = 0
            metadata["total_chunks"] = 1
            chunks_with_metadata = [(text_content, metadata)]
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

        # 2. Embed — reuse existing embedding generator
        texts = [chunk for chunk, _ in chunks_with_metadata]
        embeddings = active_pipeline.embedding_generator.generate_embeddings(texts, batch_size=8)

        # 3. Store — reuse existing vector loader (upsert)
        vectors_to_load = []
        for (text_content, metadata), embedding in zip(chunks_with_metadata, embeddings):
            vectors_to_load.append((
                model,
                res_id or data.get("id", 0),
                metadata.get("chunk_index", 0),
                text_content,
                metadata,
                embedding,
            ))

        chunks_stored = await active_pipeline.loader.load_vectors(vectors_to_load)

        logger.info(
            f"[PUSH] Indexed {model} res_id={res_id} "
            f"({chunks_stored} chunk(s), patient_seq={data.get('patient_seq', '?')})"
        )

        return {
            "status": "success",
            "model": model,
            "res_id": res_id,
            "chunks_stored": chunks_stored,
            "patient_seq": data.get("patient_seq", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUSH] Failed to index {model} res_id={res_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if active_pipeline is not pipeline:
            await active_pipeline.close()

