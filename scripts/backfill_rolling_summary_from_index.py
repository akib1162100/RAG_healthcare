import argparse
import asyncio
import json
from typing import List, Optional

from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.repositories.vector_repository import VectorRepository
from app.services.odoo_service import OdooService
from app.utils.html_builder import HTMLBuilder
from app.utils.rolling_summary_fallback import build_deterministic_rolling_summary


async def _get_patient_sequences(session, patient_seq: Optional[str]) -> List[str]:
    if patient_seq:
        return [patient_seq]
    result = await session.execute(
        text(
            """
            SELECT DISTINCT metadata->>'patient_seq' AS patient_seq
            FROM medical_rag_index
            WHERE COALESCE(metadata->>'patient_seq', '') <> ''
            ORDER BY metadata->>'patient_seq'
            """
        )
    )
    return [row[0] for row in result.fetchall() if row[0]]


async def _get_partner_id(records: List[dict]) -> Optional[int]:
    for record in records:
        if record.get("source_model") == "res.partner" and record.get("source_id"):
            try:
                return int(record["source_id"])
            except (TypeError, ValueError):
                return None
    return None


async def backfill_patient(patient_seq: str, push_odoo: bool) -> dict:
    async with AsyncSessionLocal() as session:
        repo = VectorRepository(session)
        records = await repo.get_patient_records(patient_seq=patient_seq, since_id=0, limit=10000, order_dir="ASC")
        if not records:
            return {"patient_seq": patient_seq, "status": "skipped", "reason": "no indexed records"}

        summary = build_deterministic_rolling_summary(records, patient_seq)
        summary = HTMLBuilder.enrich_summary_for_storage(summary)
        patient_name = summary.get("patient_demographics", {}).get("patient_name") or "Patient"
        html = HTMLBuilder.build_rolling_summary_html(summary, patient_seq, patient_name)
        last_id = max(int(record.get("id", 0) or 0) for record in records)
        await repo.save_rolling_summary(
            patient_seq,
            summary,
            last_processed_id=last_id,
            chunk_size=5,
            total_records_processed=len(records),
        )

    pushed = False
    partner_id = await _get_partner_id(records)
    if push_odoo and partner_id:
        pushed = await OdooService().update_patient_medical_html(partner_id, summary_html=html)

    return {
        "patient_seq": patient_seq,
        "status": "updated",
        "records": len(records),
        "last_id": last_id,
        "partner_id": partner_id,
        "odoo_pushed": pushed,
        "summary_preview": json.dumps(summary)[:300],
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill rolling summaries from indexed patient records.")
    parser.add_argument("--patient-seq", help="Single patient sequence to backfill.")
    parser.add_argument("--all", action="store_true", help="Backfill all indexed patients.")
    parser.add_argument("--push-odoo", action="store_true", help="Push rendered HTML back to Odoo partner records.")
    args = parser.parse_args()

    if not args.patient_seq and not args.all:
        parser.error("Provide --patient-seq or --all")

    async with AsyncSessionLocal() as session:
        patient_sequences = await _get_patient_sequences(session, args.patient_seq)

    total = len(patient_sequences)
    for index, patient_seq in enumerate(patient_sequences, start=1):
        result = await backfill_patient(patient_seq, push_odoo=args.push_odoo)
        print(f"[{index}/{total}] {result}")


if __name__ == "__main__":
    asyncio.run(main())
