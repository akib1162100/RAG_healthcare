"""
Nightly scheduler for the RAG Healthcare system.

Runs three phases for each configured Odoo instance:
1. Incremental ETL sync
2. Roll-forward stale patient summaries
3. Generate uncached prescription details
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level scheduler instance (started in main.py)
scheduler = AsyncIOScheduler()


async def nightly_sync_and_rebuild_job():
    """Run the nightly ETL/summarization/detail-generation workflow."""
    logger.info("[SCHEDULER] Starting nightly 3-phase job")
    instance_configs = settings.get_odoo_instances() or [settings.get_default_odoo_instance()]

    # Phase 1: incremental ETL
    logger.info("[SCHEDULER] Phase 1: Incremental ETL sync")
    for instance_config in instance_configs:
        try:
            from app.etl.pipeline import ETLPipeline

            pipeline = ETLPipeline(instance_config=instance_config)
            results = await pipeline.run_full_indexing(
                models=['wk.appointment', 'prescription.order.knk'],
                incremental=True,
            )
            total_synced = sum(r.get('records_indexed', 0) for r in results.values())
            logger.info(
                f"[SCHEDULER] Phase 1 complete for {pipeline.instance_id}: "
                f"{total_synced} records synced"
            )
            await pipeline.close()
        except Exception as e:
            logger.error(
                f"[SCHEDULER] Phase 1 ETL sync failed for {instance_config['instance_id']}: {e}"
            )

    # Phase 2: rebuild stale summaries
    logger.info("[SCHEDULER] Phase 2: Rolling forward stale summaries")
    try:
        import asyncio
        from app.api.v1.endpoints.rag import background_rolling_rebuild_task
        from app.core.database import AsyncSessionLocal
        from app.models.schemas import SummaryRequest
        from app.repositories.vector_repository import VectorRepository

        for instance_config in instance_configs:
            instance_id = instance_config['instance_id']
            async with AsyncSessionLocal() as session:
                vector_repo = VectorRepository(session, instance_id=instance_id)
                stale_patients = await vector_repo.get_all_stale_patients()

            if not stale_patients:
                logger.info(f"[SCHEDULER] Phase 2: All summaries up-to-date for {instance_id}")
                continue

            logger.info(
                f"[SCHEDULER] Phase 2: Found {len(stale_patients)} stale patient(s) for {instance_id}"
            )
            for patient_seq in stale_patients:
                request = SummaryRequest(patient_seq=patient_seq, instance_id=instance_id)
                logger.info(f"[SCHEDULER] Queuing roll-forward for {patient_seq} [{instance_id}]")
                asyncio.ensure_future(background_rolling_rebuild_task(request, chunk_size=5))
    except Exception as e:
        logger.error(f"[SCHEDULER] Phase 2 summary rebuild failed: {e}")

    # Phase 3: generate uncached details
    logger.info("[SCHEDULER] Phase 3: Generating uncached prescription details")
    try:
        import asyncio
        from app.api.v1.endpoints.rag import background_details_task
        from app.core.database import AsyncSessionLocal
        from app.models.schemas import SummaryRequest
        from app.repositories.vector_repository import VectorRepository

        for instance_config in instance_configs:
            instance_id = instance_config['instance_id']
            async with AsyncSessionLocal() as session:
                vector_repo = VectorRepository(session, instance_id=instance_id)
                stale_patients = await vector_repo.get_all_stale_patients()

            if not stale_patients:
                logger.info(f"[SCHEDULER] Phase 3: No uncached details to generate for {instance_id}")
                continue

            for patient_seq in stale_patients:
                request = SummaryRequest(patient_seq=patient_seq, instance_id=instance_id)
                logger.info(f"[SCHEDULER] Queuing details generation for {patient_seq} [{instance_id}]")
                asyncio.ensure_future(background_details_task(request))
    except Exception as e:
        logger.error(f"[SCHEDULER] Phase 3 details generation failed: {e}")

    logger.info("[SCHEDULER] Nightly 3-phase job complete")


def start_scheduler():
    """Register scheduled jobs and start the APScheduler."""
    scheduler.add_job(
        nightly_sync_and_rebuild_job,
        trigger=CronTrigger(hour=0, minute=0),
        id="nightly_sync_and_rebuild",
        name="Nightly ETL Sync + Summary Roll-Forward + Details Generation",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("[SCHEDULER] APScheduler started. Nightly 3-phase job registered at 00:00.")


def stop_scheduler():
    """Gracefully shut down the scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[SCHEDULER] APScheduler stopped.")
