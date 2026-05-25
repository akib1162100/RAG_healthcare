"""
API Router for RAG endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, AsyncSessionLocal
from app.models.schemas import QueryRequest, ChatRequest, RAGQueryResponse, SummaryRequest, SummaryResponse
from app.services.rag_service import RAGService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.odoo_service import OdooService
from app.utils.html_builder import HTMLBuilder
from app.utils.prescription_details_builder import (
    build_deterministic_prescription_details,
    group_prescription_records,
    has_meaningful_prescription_details,
    merge_prescription_details,
    needs_prescription_detail_refresh,
)
from app.utils.rolling_summary_fallback import (
    build_deterministic_rolling_summary,
    has_meaningful_rolling_summary,
)
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])

# Global service instances (initialized at startup)
embedding_service: EmbeddingService = None
llm_service: LLMService = None
rag_service: RAGService = None
odoo_service: OdooService = None


async def _generate_detail_for_group(rag: RAGService, vector_repo, group_record: dict) -> dict:
    """
    Build one 10-section detail document for a prescription source record.
    Uses deterministic extraction as the base and LLM enrichment as an overlay.
    The final merged document is cached against every chunk record id in the group.
    """
    group_ids = group_record.get("group_record_ids") or [group_record.get("id")]
    valid_cached = None
    for rid in group_ids:
        cached = await vector_repo.get_formatted_record(rid)
        if cached is not None and not needs_prescription_detail_refresh(cached):
            valid_cached = cached
            break
    if valid_cached is not None:
        return valid_cached

    base_details = build_deterministic_prescription_details(group_record)
    meta = group_record.get("metadata") or {}
    meta_str = json.dumps(meta, ensure_ascii=False)
    context = f"[Prescription {group_record.get('source_id')}] {group_record.get('content', '')}\nMetadata: {meta_str}"

    final_details = base_details
    try:
        enriched_json_str = await rag.llm_service.generate_prescription_details(
            patient_seq=group_record.get("patient_seq") or meta.get("patient_seq") or "",
            context=context,
            base_details=base_details,
        )
        enriched_dict = json.loads(enriched_json_str)
        final_details = merge_prescription_details(base_details, enriched_dict)
    except Exception as ex:
        logger.warning(f"Prescription detail enrichment failed for source {group_record.get('source_id')}: {ex}")

    if not has_meaningful_prescription_details(final_details):
        final_details = base_details

    for rid in group_ids:
        await vector_repo.save_formatted_record(
            record_id=rid,
            patient_seq=group_record.get("patient_seq") or meta.get("patient_seq") or "",
            formatted_json=final_details,
            odoo_model=group_record.get("source_model"),
            odoo_res_id=group_record.get("source_id"),
        )
    return final_details

async def get_rag_service() -> RAGService:
    """Dependency to get RAG service"""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    return rag_service

@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: QueryRequest,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service)
):
    """
    General RAG query endpoint
    
    - **prompt**: Natural language question
    - **patient_seq**: Optional patient ID to restrict context to that patient
    """
    try:
        metadata_filter = {}
        if request.patient_seq:
            metadata_filter['patient_seq'] = request.patient_seq
            
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
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
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
        metadata_filter = {}
        if request.patient_seq:
            metadata_filter['patient_seq'] = request.patient_seq
            
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
    limit: int = 1000,
    offset: int = 0,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieve raw indexed medical records.
    Bypasses the LLM and returns the exact data chunks stored in the vector database.
    """
    try:
        from app.repositories.vector_repository import VectorRepository
        repo = VectorRepository(session)
        total_records = await repo.count_patient_records(patient_seq)
        records = await repo.get_patient_records(patient_seq, limit=limit, offset=offset)
        message = "No medical records found." if not records else f"Successfully retrieved {'all records' if not patient_seq else 'patient records'}"
        return {
            "status": "success",
            "patient_seq": patient_seq or "ALL",
            "message": message,
            "total_records": total_records,
            "limit": limit,
            "offset": offset,
            "returned_records": len(records),
            "has_more": (offset + len(records)) < total_records,
            "data": records
        }
    except Exception as e:
        logger.error(f"Error fetching patient data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prescriptions")
async def get_prescription_data(
    patient_seq: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db)
):
    """Retrieve raw indexed prescription records."""
    try:
        from app.repositories.vector_repository import VectorRepository
        repo = VectorRepository(session)
        total_records = await repo.count_prescription_records(patient_seq)
        records = await repo.get_prescription_records(patient_seq, limit=limit, offset=offset)
        message = "No prescription records found." if not records else f"Successfully retrieved {'all prescriptions' if not patient_seq else 'patient prescriptions'}"
        return {
            "status": "success",
            "patient_seq": patient_seq or "ALL",
            "message": message,
            "total_records": total_records,
            "limit": limit,
            "offset": offset,
            "returned_records": len(records),
            "has_more": (offset + len(records)) < total_records,
            "data": records
        }
    except Exception as e:
        logger.error(f"Error fetching prescription data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/appointments")
async def get_appointment_data(
    patient_seq: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db)
):
    """Retrieve raw indexed appointment records."""
    try:
        from app.repositories.vector_repository import VectorRepository
        repo = VectorRepository(session)
        total_records = await repo.count_appointment_records(patient_seq)
        records = await repo.get_appointment_records(patient_seq, limit=limit, offset=offset)
        message = "No appointment records found." if not records else f"Successfully retrieved {'all appointments' if not patient_seq else 'patient appointments'}"
        return {
            "status": "success",
            "patient_seq": patient_seq or "ALL",
            "message": message,
            "total_records": total_records,
            "limit": limit,
            "offset": offset,
            "returned_records": len(records),
            "has_more": (offset + len(records)) < total_records,
            "data": records
        }
    except Exception as e:
        logger.error(f"Error fetching appointment data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diseases")
async def get_disease_data(
    limit: int = 1000,
    offset: int = 0,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db)
):
    """Retrieve raw indexed medical disease reference records."""
    try:
        from app.repositories.vector_repository import VectorRepository
        repo = VectorRepository(session)
        total_records = await repo.count_disease_records()
        records = await repo.get_disease_records(limit=limit, offset=offset)
        message = "No disease records found." if not records else "Successfully retrieved all disease records"
        return {
            "status": "success",
            "message": message,
            "total_records": total_records,
            "limit": limit,
            "offset": offset,
            "returned_records": len(records),
            "has_more": (offset + len(records)) < total_records,
            "data": records
        }
    except Exception as e:
        logger.error(f"Error fetching disease data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=SummaryResponse)
async def generate_patient_summary(
    request: SummaryRequest,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
):
    """
    Quick summary endpoint (top-30 records). Use /rolling-summary for full zero-loss coverage.
    """
    try:
        from app.repositories.vector_repository import VectorRepository
        vector_repo = VectorRepository(session)
        records = await vector_repo.get_patient_records(request.patient_seq)

        if not records:
            return SummaryResponse(summary="{}", patient_seq=request.patient_seq, num_records=0)

        context_parts = []
        for i, rec in enumerate(records[:30], 1):
            context_parts.append(f"[Record {i}] {rec.get('content', '')}")
            meta = rec.get("metadata") or {}
            if meta:
                meta_str = ", ".join(f"{k}: {v}" for k, v in meta.items())
                context_parts.append(f"  Metadata: {meta_str}")
        context = "\n".join(context_parts)

        summary_json = await rag.llm_service.generate_medical_summary(
            patient_seq=request.patient_seq, context=context,
        )

        return SummaryResponse(
            summary=summary_json,
            patient_seq=request.patient_seq,
            num_records=len(records),
        )

    except Exception as e:
        logger.error(f"Summary generation error for patient {request.patient_seq}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Rolling Summary — Map-Reduce Hierarchical Checkpoint Pipeline
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/rolling-summary", response_model=SummaryResponse)
async def generate_rolling_patient_summary(
    request: SummaryRequest,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
    chunk_size: int = 5,
):
    """
    Smart 3-Tier Rolling Summary:

    TIER 1 — FRESH:  No new records → return cached summary instantly (<50ms).
    TIER 2 — ROLL-FORWARD:  New records exist + cached summary exists
             → merge only new records into existing summary (1 LLM call).
    TIER 3 — FIRST RUN:  No existing summary at all → full Map-Reduce.

    Full rebuild from scratch is ONLY available via POST /summary/regenerate/deep.
    """
    import asyncio
    import json
    from app.repositories.vector_repository import VectorRepository

    vector_repo = VectorRepository(session)

    # ── Load existing state ──────────────────────────────────────────────────
    rolling_data = await vector_repo.get_rolling_summary(request.patient_seq)
    cached_summary = rolling_data.get('summary_json', {})
    last_processed_id = rolling_data.get('last_processed_id', 0)
    if not isinstance(last_processed_id, int):
        last_processed_id = 0

    live_count = await vector_repo.get_live_record_count(request.patient_seq)

    # Count how many records existed when the summary was last built
    processed = rolling_data.get('total_records_processed', 0)
    if not isinstance(processed, int):
        processed = 0

    # ── TIER 1: FRESH — nothing changed, return cache ────────────────────────
    if has_meaningful_rolling_summary(cached_summary) and processed > 0 and live_count <= processed:
        logger.info(f"[TIER1] Cache HIT for {request.patient_seq} "
                     f"({processed} records, all fresh)")
        return SummaryResponse(
            summary=json.dumps(cached_summary) if isinstance(cached_summary, dict) else str(cached_summary),
            patient_seq=request.patient_seq,
            num_records=processed,
        )

    # ── Concurrency guard ────────────────────────────────────────────────────
    acquired = await vector_repo.set_processing_flag(request.patient_seq, True)
    if not acquired:
        rolling_data = await vector_repo.get_rolling_summary(request.patient_seq)
        cached = rolling_data.get('summary_json', {})
        return SummaryResponse(
            summary=json.dumps(cached) if isinstance(cached, dict) else str(cached),
            patient_seq=request.patient_seq, num_records=0,
        )

    try:
        # ── TIER 2: ROLL-FORWARD — existing summary + new records ────────────
        if has_meaningful_rolling_summary(cached_summary) and last_processed_id > 0:
            # Fetch ONLY records added since the last summary was built
            new_records = await vector_repo.get_patient_records(
                patient_seq=request.patient_seq,
                since_id=last_processed_id,
                limit=10000,
                order_dir="ASC",
            )

            if not new_records:
                # Edge case: live_count might differ due to deletions / re-indexing
                logger.info(f"[TIER2] No new records found for {request.patient_seq}, returning cache")
                return SummaryResponse(
                    summary=json.dumps(cached_summary) if isinstance(cached_summary, dict) else str(cached_summary),
                    patient_seq=request.patient_seq,
                    num_records=processed,
                )

            # Build text from only the new records
            new_text = "\n".join(
                f"[R{r['id']}] {r['content']}" for r in new_records
            )

            logger.info(
                f"[TIER2] Roll-forward for {request.patient_seq}: "
                f"merging {len(new_records)} new record(s) into existing summary"
            )

            # Single LLM call to merge new data into existing summary
            merged_json_str = await rag.llm_service.merge_summary_with_new_records(
                request.patient_seq, cached_summary, new_text
            )

            # Parse the LLM response
            s = merged_json_str.find('{')
            e = merged_json_str.rfind('}')
            clean = merged_json_str[s:e+1] if s != -1 else '{}'
            try:
                final_dict = json.loads(clean)
            except json.JSONDecodeError:
                logger.warning(f"[TIER2] JSON parse failed, falling back to cached summary")
                final_dict = cached_summary
            if not has_meaningful_rolling_summary(final_dict):
                all_records = await vector_repo.get_patient_records(
                    patient_seq=request.patient_seq,
                    since_id=0,
                    limit=10000,
                    order_dir="ASC",
                )
                final_dict = build_deterministic_rolling_summary(all_records, request.patient_seq)
                logger.warning(f"[TIER2] Deterministic fallback used for {request.patient_seq}")
            final_dict = HTMLBuilder.enrich_summary_for_storage(final_dict)

            new_total = processed + len(new_records)
            new_last_id = new_records[-1]['id']

            # Persist updated summary
            await vector_repo.save_rolling_summary(
                request.patient_seq, final_dict,
                last_processed_id=new_last_id,
                chunk_size=chunk_size,
                total_records_processed=new_total,
            )

            # Push HTML to Odoo
            if request.partner_id:
                try:
                    patient_name = (
                        final_dict.get('patient_demographics', {}).get('patient_name')
                        or final_dict.get('patient_demographics', {}).get('name')
                        or 'Patient'
                    )
                    html = HTMLBuilder.build_rolling_summary_html(
                        final_dict, request.patient_seq, patient_name
                    )
                    await odoo_service.update_patient_medical_html(
                        request.partner_id, summary_html=html
                    )
                    logger.info(f"[TIER2] Rolling summary HTML pushed to Odoo partner {request.partner_id}")
                except Exception as push_err:
                    logger.warning(f"Odoo HTML push failed (non-fatal): {push_err}")

            return SummaryResponse(
                summary=json.dumps(final_dict),
                patient_seq=request.patient_seq,
                num_records=new_total,
            )

        # ── TIER 3: FIRST RUN — no existing summary, full Map-Reduce ────────
        logger.info(f"[TIER3] First-time full Map-Reduce for {request.patient_seq}")

        all_records = await vector_repo.get_patient_records(
            patient_seq=request.patient_seq, since_id=0, limit=10000, order_dir="ASC"
        )
        if not all_records:
            return SummaryResponse(
                summary='{}',
                patient_seq=request.patient_seq, num_records=0,
            )

        total = len(all_records)
        num_full_chunks = total // chunk_size
        loose_records = all_records[num_full_chunks * chunk_size:]

        # Load already-cached intermediate chunk summaries
        cached_chunks = await vector_repo.get_chunked_summaries(request.patient_seq, chunk_size)
        cached_indices = {c['chunk_index'] for c in cached_chunks}

        # MAP phase
        map_concurrency = 1 if rag.llm_service.backend == 'local' else 4
        sem = asyncio.Semaphore(map_concurrency)

        async def build_chunk(chunk_idx: int):
            async with sem:
                batch = all_records[chunk_idx * chunk_size: (chunk_idx + 1) * chunk_size]
                rid_start = batch[0]['id']
                rid_end   = batch[-1]['id']

                if chunk_size > 5:
                    sub_chunks = await vector_repo.get_alternative_chunk_summaries(
                        request.patient_seq, chunk_size, 5, chunk_idx
                    )
                    if len(sub_chunks) >= chunk_size // 5:
                        combined = json.dumps([c['summary_json'] for c in sub_chunks])
                        chunk_json_str = await rag.llm_service.generate_intermediate_chunk(
                            request.patient_seq, combined
                        )
                    else:
                        records_text = "\n".join(f"[R{r['id']}] {r['content']}" for r in batch)
                        chunk_json_str = await rag.llm_service.generate_intermediate_chunk(
                            request.patient_seq, records_text
                        )
                else:
                    records_text = "\n".join(f"[R{r['id']}] {r['content']}" for r in batch)
                    chunk_json_str = await rag.llm_service.generate_intermediate_chunk(
                        request.patient_seq, records_text
                    )

                s = chunk_json_str.find('{')
                e = chunk_json_str.rfind('}')
                clean = chunk_json_str[s:e+1] if s != -1 else '{}'
                try:
                    chunk_dict = json.loads(clean)
                except json.JSONDecodeError:
                    chunk_dict = {}
                if not has_meaningful_rolling_summary(chunk_dict):
                    chunk_dict = build_deterministic_rolling_summary(batch, request.patient_seq)
                chunk_dict = HTMLBuilder.enrich_summary_for_storage(chunk_dict)

                await vector_repo.save_chunked_summary(
                    request.patient_seq, chunk_size, chunk_idx, rid_start, rid_end, chunk_dict
                )
                logger.info(f"Chunk {chunk_idx} cached for patient {request.patient_seq}")
                return chunk_dict

        missing = [i for i in range(num_full_chunks) if i not in cached_indices]
        new_dicts = await asyncio.gather(*[build_chunk(i) for i in missing])

        all_chunk_map = {c['chunk_index']: c['summary_json'] for c in cached_chunks}
        for idx, d in zip(missing, new_dicts):
            all_chunk_map[idx] = d
        ordered_chunks = [all_chunk_map[i] for i in sorted(all_chunk_map)]

        # REDUCE phase
        loose_text = "\n".join(f"[R{r['id']}] {r['content']}" for r in loose_records)
        final_json_str = await rag.llm_service.generate_summary_from_chunks(
            request.patient_seq, ordered_chunks, loose_text
        )
        s = final_json_str.find('{')
        e = final_json_str.rfind('}')
        clean_final = final_json_str[s:e+1] if s != -1 else '{}'
        try:
            final_dict = json.loads(clean_final)
        except json.JSONDecodeError:
            final_dict = {}
        if not has_meaningful_rolling_summary(final_dict):
            final_dict = build_deterministic_rolling_summary(all_records, request.patient_seq)
            logger.warning(f"[TIER3] Deterministic fallback used for {request.patient_seq}")
        final_dict = HTMLBuilder.enrich_summary_for_storage(final_dict)

        # Persist
        await vector_repo.save_rolling_summary(
            request.patient_seq, final_dict,
            last_processed_id=all_records[-1]['id'],
            chunk_size=chunk_size,
            total_records_processed=total,
        )

        # Push HTML to Odoo
        if request.partner_id:
            try:
                patient_name = (
                    final_dict.get('patient_demographics', {}).get('patient_name')
                    or final_dict.get('patient_demographics', {}).get('name')
                    or 'Patient'
                )
                html = HTMLBuilder.build_rolling_summary_html(
                    final_dict, request.patient_seq, patient_name
                )
                await odoo_service.update_patient_medical_html(
                    request.partner_id, summary_html=html
                )
                logger.info(f"[TIER3] Rolling summary HTML pushed to Odoo partner {request.partner_id}")
            except Exception as push_err:
                logger.warning(f"Odoo HTML push failed (non-fatal): {push_err}")

        return SummaryResponse(
            summary=json.dumps(final_dict),
            patient_seq=request.patient_seq,
            num_records=total,
        )

    except Exception as e:
        logger.error(f"Rolling summary error for {request.patient_seq}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await vector_repo.set_processing_flag(request.patient_seq, False)


@router.post("/summary/regenerate/deep", response_model=SummaryResponse)
async def regenerate_summary_deep(
    request: SummaryRequest,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
    chunk_size: int = 5,
):
    """
    FULL DEEP REBUILD — purges all cached chunks and rolling summary,
    then runs a complete Map-Reduce from scratch.

    This is an EXPENSIVE operation. Only use via:
    - Direct API call
    - Odoo "🔄 Rebuild Summary" button
    """
    import asyncio
    import json
    from app.repositories.vector_repository import VectorRepository

    vector_repo = VectorRepository(session)

    # Purge all caches for this patient
    await vector_repo.delete_all_chunked_summaries(request.patient_seq)
    logger.info(f"[DEEP REBUILD] Purged all cached chunks for {request.patient_seq}")

    # Reset the rolling summary so Tier 3 logic runs from scratch
    await vector_repo.save_rolling_summary(
        request.patient_seq, {},
        last_processed_id=0,
        chunk_size=chunk_size,
        total_records_processed=0,
    )

    # Log the rebuild event
    await vector_repo.log_regeneration(
        request.patient_seq, 'deep_rebuild', triggered_by='api'
    )

    # Delegate to the standard endpoint which will hit TIER 3 (first-run)
    return await generate_rolling_patient_summary(
        request=request, session=session, rag=rag, chunk_size=chunk_size
    )


# ─────────────────────────────────────────────────────────────────────────────
# Prescription Details — Lazy-Load Cache
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/details")
async def generate_prescription_details(
    request: SummaryRequest,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
):
    """
    Per-prescription detail generation with lazy-load caching.
    - Cache HIT: returns instantly (<100ms) from patient_formatted_records table.
    - Cache MISS: sends to LLM (max 2 parallel), saves result for all future requests.
    """
    import asyncio
    from app.repositories.vector_repository import VectorRepository

    try:
        vector_repo = VectorRepository(session)
        records = await vector_repo.get_prescription_records(request.patient_seq)
        if not records:
            return {"details": "[]"}

        grouped_records = group_prescription_records(records)
        sem = asyncio.Semaphore(2)

        async def process_prescription(group_record):
            async with sem:
                return await _generate_detail_for_group(rag, vector_repo, group_record)

        results = await asyncio.gather(*[process_prescription(group_record) for group_record in grouped_records])
        return {"details": json.dumps(results)}

    except Exception as e:
        logger.error(f"Details generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Status & Regeneration Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/summary/status")
async def summary_status(patient_seq: str, session: AsyncSession = Depends(get_db)):
    """
    Lightweight stale-detection. Returns 'fresh' or 'stale' with record counts.
    Poll from Odoo UI to show an 'Update Summary' badge without triggering LLM work.
    """
    from app.repositories.vector_repository import VectorRepository
    vector_repo = VectorRepository(session)
    rolling = await vector_repo.get_rolling_summary(patient_seq)
    processed = rolling.get('total_records_processed', 0)
    if not isinstance(processed, int):
        processed = 0
    live = await vector_repo.get_live_record_count(patient_seq)
    status = "stale" if live > processed else "fresh"
    return {"status": status, "live": live, "processed": processed, "patient_seq": patient_seq}


@router.post("/summary/regenerate")
async def regenerate_summary_soft(
    request: SummaryRequest,
    background_tasks: BackgroundTasks,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db),
    chunk_size: int = 5,
):
    """
    Soft reset: deletes only the final rolling summary, rebuilds it from existing
    cached intermediate chunks. Fast — intermediate LLM work is NOT repeated.
    """
    from sqlalchemy import text as _text
    from app.repositories.vector_repository import VectorRepository
    vector_repo = VectorRepository(session)
    await session.execute(_text("DELETE FROM patient_rolling_summaries WHERE patient_seq = :ps"),
                          {"ps": request.patient_seq})
    await session.commit()
    await vector_repo.log_regeneration(request.patient_seq, 'soft',
                                        triggered_by=str(getattr(request, 'partner_id', 'api')))
    background_tasks.add_task(background_rolling_rebuild_task, request, chunk_size)
    return {"status": "queued", "type": "soft", "patient_seq": request.patient_seq}


@router.post("/summary/regenerate/deep")
async def regenerate_summary_deep(
    request: SummaryRequest,
    background_tasks: BackgroundTasks,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db),
    chunk_size: int = 5,
):
    """
    Deep reset: purges ALL cached chunks AND the final rolling summary.
    Forces a complete rebuild from raw records. Use only when chunk data is fundamentally wrong.
    """
    from sqlalchemy import text as _text
    from app.repositories.vector_repository import VectorRepository
    vector_repo = VectorRepository(session)
    await vector_repo.delete_all_chunked_summaries(request.patient_seq)
    await session.execute(_text("DELETE FROM patient_rolling_summaries WHERE patient_seq = :ps"),
                          {"ps": request.patient_seq})
    await session.commit()
    await vector_repo.log_regeneration(request.patient_seq, 'deep',
                                        triggered_by=str(getattr(request, 'partner_id', 'api')))
    background_tasks.add_task(background_rolling_rebuild_task, request, chunk_size)
    return {"status": "queued", "type": "deep", "patient_seq": request.patient_seq}


@router.post("/summary/regenerate/chunk")
async def regenerate_summary_chunk(
    request: SummaryRequest,
    background_tasks: BackgroundTasks,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db),
    chunk_size: int = 5,
    chunk_index: int = 0,
):
    """
    Selective chunk reset: deletes one specific intermediate chunk and rebuilds only that slice.
    Most surgical option — use when only one date-range of records was incorrect.
    """
    from app.repositories.vector_repository import VectorRepository
    vector_repo = VectorRepository(session)
    await vector_repo.delete_chunked_summary(request.patient_seq, chunk_size, chunk_index)
    await vector_repo.log_regeneration(request.patient_seq, 'chunk', chunk_index=chunk_index,
                                        triggered_by=str(getattr(request, 'partner_id', 'api')))
    background_tasks.add_task(background_rolling_rebuild_task, request, chunk_size)
    return {"status": "queued", "type": "chunk", "chunk_index": chunk_index,
            "patient_seq": request.patient_seq}


@router.post("/details/regenerate")
async def regenerate_prescription_detail(
    patient_seq: str,
    record_id: int,
    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
):
    """
    Force-regenerate a single cached prescription detail.
    Deletes the stale cached entry and immediately re-runs LLM inference for that record.
    """
    import json
    from sqlalchemy import text as _text
    from app.repositories.vector_repository import VectorRepository
    vector_repo = VectorRepository(session)

    await vector_repo.delete_formatted_record(record_id)
    await vector_repo.log_regeneration(patient_seq, 'record', record_id=record_id)

    result = await session.execute(
        _text("SELECT id, content_text, metadata, odoo_model, odoo_res_id "
              "FROM medical_rag_index WHERE id = :rid"), {"rid": record_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found in index")

    source_model = row[3]
    source_id = row[4]
    source_records = await vector_repo.get_source_records(source_model, source_id)
    if not source_records:
        metadata = row[2] or {}
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                metadata = {}
        source_records = [{
            "id": row[0],
            "content": row[1],
            "metadata": metadata,
            "source_model": source_model,
            "source_id": source_id,
            "patient_seq": patient_seq,
        }]
    group_record = group_prescription_records(source_records)[0]
    result_dict = await _generate_detail_for_group(rag, vector_repo, group_record)
    return {"status": "regenerated", "record_id": record_id, "source_id": source_id, "data": result_dict}


# ─────────────────────────────────────────────────────────────────────────────
# Background Tasks
# ─────────────────────────────────────────────────────────────────────────────

async def background_rolling_rebuild_task(request: SummaryRequest, chunk_size: int = 5):
    """Rebuild the final rolling summary from existing cached chunks (background)."""
    import json
    logger.info(f"Background rebuild starting for {request.patient_seq}")
    try:
        async with AsyncSessionLocal() as session:
            from app.repositories.vector_repository import VectorRepository
            vector_repo = VectorRepository(session)
            all_records = await vector_repo.get_patient_records(
                patient_seq=request.patient_seq, since_id=0, limit=10000, order_dir="ASC"
            )
            if not all_records:
                return
            total = len(all_records)
            num_full_chunks = total // chunk_size
            loose_records = all_records[num_full_chunks * chunk_size:]
            cached_chunks = await vector_repo.get_chunked_summaries(request.patient_seq, chunk_size)
            ordered = [c['summary_json'] for c in sorted(cached_chunks, key=lambda x: x['chunk_index'])]
            loose_text = "\n".join(f"[R{r['id']}] {r['content']}" for r in loose_records)
            final_str = await llm_service.generate_summary_from_chunks(
                request.patient_seq, ordered, loose_text
            )
            s = final_str.find('{'); e = final_str.rfind('}')
            clean = final_str[s:e+1] if s != -1 else '{}'
            try: final_dict = json.loads(clean)
            except: final_dict = {}
            if not has_meaningful_rolling_summary(final_dict):
                final_dict = build_deterministic_rolling_summary(all_records, request.patient_seq)
            final_dict = HTMLBuilder.enrich_summary_for_storage(final_dict)
            await vector_repo.save_rolling_summary(
                request.patient_seq, final_dict,
                last_processed_id=all_records[-1]['id'],
                chunk_size=chunk_size, total_records_processed=total,
            )
            if request.partner_id:
                patient_name = (
                    final_dict.get('patient_demographics', {}).get('patient_name')
                    or final_dict.get('patient_demographics', {}).get('name')
                    or 'Patient'
                )
                html = HTMLBuilder.build_rolling_summary_html(final_dict, request.patient_seq, patient_name)
                await odoo_service.update_patient_medical_html(request.partner_id, summary_html=html)
            logger.info(f"Background rebuild complete for {request.patient_seq}")
    except Exception as e:
        logger.error(f"Background rebuild failed for {request.patient_seq}: {e}")
    finally:
        async with AsyncSessionLocal() as session:
            from app.repositories.vector_repository import VectorRepository
            await VectorRepository(session).set_processing_flag(request.patient_seq, False)


async def background_summary_task(request: SummaryRequest):
    """Legacy: generates summary and pushes back to Odoo"""
    import json
    logger.info(f"Background: Starting summary generation for patient {request.patient_seq}")
    try:
        async with AsyncSessionLocal() as session:
            from app.repositories.vector_repository import VectorRepository
            vector_repo = VectorRepository(session)
            context = await vector_repo.get_patient_context(request.patient_seq)
            if not context:
                logger.warning(f"Background: No records found for patient {request.patient_seq}")
                return
            res_json_str = await llm_service.generate_medical_summary(request.patient_seq, context)
            try: data = json.loads(res_json_str)
            except: data = {}
            from app.utils.html_builder import HTMLBuilder
            html = HTMLBuilder.build_10_section_html(data, request.patient_seq, "Patient Profile (Auto-Sync)")
            if request.partner_id:
                await odoo_service.update_patient_medical_html(request.partner_id, summary_html=html)
            logger.info(f"Background: Summary updated for {request.patient_seq}")
    except Exception as e:
        logger.error(f"Background: Summary generation failed for {request.patient_seq}: {e}")


async def background_details_task(request: SummaryRequest):
    """Legacy: generates detailed prescriptions and pushes back to Odoo"""
    import asyncio
    logger.info(f"Background: Starting details generation for patient {request.patient_seq}")
    try:
        async with AsyncSessionLocal() as session:
            from app.repositories.vector_repository import VectorRepository
            vector_repo = VectorRepository(session)
            records = await vector_repo.get_prescription_records(request.patient_seq)
            if not records:
                return
            grouped_records = group_prescription_records(records)
            sem = asyncio.Semaphore(2)

            async def process(group_record):
                async with sem:
                    return await _generate_detail_for_group(rag_service, vector_repo, group_record)

            results = await asyncio.gather(*[process(group_record) for group_record in grouped_records])
            from app.utils.html_builder import HTMLBuilder
            PAGE_BREAK = '<div style="page-break-after:always;border-top:2px solid #1a3c5e;margin:20px 0 0 0"></div>'
            pages = [HTMLBuilder.render_clinical_doc(d, request.patient_seq, "Patient Profile (Auto-Sync)", i+1, len(results))
                     for i, d in enumerate(results)]
            html = PAGE_BREAK.join(pages)
            if request.partner_id:
                await odoo_service.update_patient_medical_html(request.partner_id, details_html=html)
            logger.info(f"Background: Details updated for {request.patient_seq}")
    except Exception as e:
        logger.error(f"Background: Details generation failed for {request.patient_seq}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Background Trigger Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/summary/background")
async def trigger_summary_background(request: SummaryRequest, background_tasks: BackgroundTasks):
    """Fire-and-forget summary generation. Returns immediately, pushes HTML to Odoo via XML-RPC."""
    if not odoo_service:
        raise HTTPException(status_code=503, detail="Odoo Service (callback) not initialized")
    background_tasks.add_task(background_summary_task, request)
    return {"status": "success", "message": "Background summary generation queued",
            "patient_seq": request.patient_seq}


@router.post("/details/background")
async def trigger_details_background(request: SummaryRequest, background_tasks: BackgroundTasks):
    """Fire-and-forget prescription formatting. Returns immediately, pushes HTML to Odoo via XML-RPC."""
    if not odoo_service:
        raise HTTPException(status_code=503, detail="Odoo Service (callback) not initialized")
    background_tasks.add_task(background_details_task, request)
    return {"status": "success", "message": "Background prescription details generation queued",
            "patient_seq": request.patient_seq}
