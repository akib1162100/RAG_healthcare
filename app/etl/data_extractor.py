"""
Data Extractor for Odoo Medical Models.

All Odoo data access is exclusively via the JSON-RPC API with Bearer auth.
No XML-RPC or direct database access is used.
"""
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
import logging


logger = logging.getLogger(__name__)

PAGE_SIZE = 500


class OdooDataExtractor:
    """Extract data from Odoo via JSON-RPC API and normalize it for the ETL transformer."""

    def __init__(self, vector_engine: AsyncEngine, instance_config: Optional[Dict] = None):
        self.vector_engine = vector_engine
        self._odoo_config = instance_config or None

    def _cfg(self) -> Dict:
        if not hasattr(self, "_odoo_config") or not self._odoo_config:
            from app.core.config import settings
            self._odoo_config = settings.get_default_odoo_instance()
            logger.info(
                f"[ODOO API] url={self._odoo_config['url']} "
                f"db={self._odoo_config['db']} "
                f"instance_id={self._odoo_config['instance_id']}"
            )
        return self._odoo_config

    async def _call_odoo_api(self, endpoint_suffix: str, params: Dict) -> Dict:
        """Call an Odoo JSON endpoint with Bearer auth."""
        cfg = self._cfg()
        api_key = cfg.get("api_key")
        if not api_key:
            raise RuntimeError("ODOO_API_KEY is not configured")

        import aiohttp

        url = f"{cfg['url']}{endpoint_suffix}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
        }

        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                response_text = await response.text()
                if response.status != 200:
                    raise RuntimeError(
                        f"Odoo API {endpoint_suffix} failed with HTTP {response.status}: "
                        f"{response_text[:500]}"
                    )
                try:
                    data = await response.json(content_type=None)
                except Exception as exc:
                    raise RuntimeError(
                        f"Odoo API {endpoint_suffix} returned invalid JSON: "
                        f"{response_text[:500]}"
                    ) from exc

        result = data.get("result") if isinstance(data, dict) else None
        if not isinstance(result, dict):
            raise RuntimeError(f"Odoo API {endpoint_suffix} returned no result payload")
        if result.get("status") != "success":
            raise RuntimeError(
                f"Odoo API {endpoint_suffix} error: {result.get('message') or result}"
            )
        return result

    async def _fetch_all_via_api(
        self,
        endpoint_suffix: str,
        domain: List,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Paginate over an Odoo bulk JSON endpoint until all rows are fetched."""
        all_records: List[Dict] = []
        offset = 0
        remaining = limit

        while True:
            page_limit = PAGE_SIZE if remaining is None else min(PAGE_SIZE, remaining)
            if page_limit <= 0:
                break

            result = await self._call_odoo_api(
                endpoint_suffix,
                {"domain": domain or [], "limit": page_limit, "offset": offset},
            )
            batch = result.get("data") or []
            if not isinstance(batch, list):
                raise RuntimeError(f"Odoo API {endpoint_suffix} returned non-list data")

            all_records.extend(batch)
            logger.info(
                f"[ODOO API] {endpoint_suffix}: fetched {len(all_records):,} records so far..."
            )

            if remaining is not None:
                remaining -= len(batch)
            if len(batch) < page_limit or remaining == 0:
                break
            offset += len(batch)

        return all_records

    def _get_patient_sequence_field(self) -> str:
        """Return the patient sequence field name from config."""
        from app.core.config import settings
        return settings.PATIENT_SEQ_FIELD

    @staticmethod
    def _m2o_id(val) -> Optional[int]:
        return val[0] if isinstance(val, (list, tuple)) and val else None

    @staticmethod
    def _m2o_name(val) -> str:
        return val[1] if isinstance(val, (list, tuple)) and len(val) > 1 else ""

    @staticmethod
    def _normalize_rich_prescription(record: Dict) -> Dict:
        """
        Bulk Odoo payloads already contain nested data; add the flat scalar
        aliases the transformer still expects for text-building.
        """
        rec = dict(record or {})
        vitals = rec.get("vitals") if isinstance(rec.get("vitals"), dict) else {}
        clinical = rec.get("clinical_scores") if isinstance(rec.get("clinical_scores"), dict) else {}
        status_updates = rec.get("status_updates") if isinstance(rec.get("status_updates"), dict) else {}
        exams = rec.get("physical_examinations") if isinstance(rec.get("physical_examinations"), dict) else {}

        rec.setdefault("prescription_number", rec.get("name", ""))
        rec.setdefault("patient", rec.get("patient_name", ""))
        rec.setdefault("physician", rec.get("physician_name", ""))
        rec.setdefault("patient_id", rec.get("patient_seq", ""))

        rec.setdefault("v_weight", vitals.get("weight"))
        rec.setdefault("v_height", vitals.get("height"))
        rec.setdefault("v_bmi", vitals.get("bmi"))
        rec.setdefault("blood_presure", vitals.get("bp_systolic"))
        rec.setdefault("blood_presure_2", vitals.get("bp_diastolic"))
        rec.setdefault("v_pulse", vitals.get("pulse"))
        rec.setdefault("v_respiratory_rate", vitals.get("respiratory_rate"))
        rec.setdefault("temperature", vitals.get("temperature"))
        rec.setdefault("spo2", vitals.get("spo2"))
        rec.setdefault("rbs", vitals.get("rbs"))

        rec.setdefault("pain_score", clinical.get("pain_score"))
        rec.setdefault("dyspnea", clinical.get("dyspnea"))
        rec.setdefault("cardiac_rythm", clinical.get("cardiac_rythm"))
        rec.setdefault("cardiac_rythm_type", clinical.get("cardiac_rythm_type"))
        rec.setdefault("nihss", clinical.get("nihss"))
        rec.setdefault("motor_power", clinical.get("motor_power"))
        rec.setdefault("pupil_reaction", clinical.get("pupil_reaction"))
        rec.setdefault("pupil_reaction_right", clinical.get("pupil_reaction_right"))
        rec.setdefault("glassgow_coma_scale", clinical.get("glassgow_coma_scale"))

        rec.setdefault("symptom_status", status_updates.get("symptom_status"))
        rec.setdefault("medication_adherence", status_updates.get("medication_adherence"))
        rec.setdefault("performance_status_update", status_updates.get("performance_status_update"))
        rec.setdefault("counseling_behavioral_response", status_updates.get("counseling_behavioral_response"))
        rec.setdefault("side_effects", status_updates.get("side_effects"))

        rec.setdefault("general", exams.get("general"))
        rec.setdefault("heent", exams.get("heent"))
        rec.setdefault("cvs", exams.get("cvs"))
        rec.setdefault("respiratory", exams.get("respiratory"))
        rec.setdefault("abdomen", exams.get("abdomen"))
        rec.setdefault("msk", exams.get("msk"))
        rec.setdefault("cns", exams.get("cns"))

        for key in (
            "medications", "diagnoses", "complaints", "investigations", "signs",
            "procedures", "gcs_scores", "bmi_records", "exercises", "ortho",
            "old_history", "medical_history", "past_medical_history",
            "medication_history", "family_history", "social_history",
        ):
            if not isinstance(rec.get(key), list):
                rec[key] = []

        for key in (
            "investigation_result", "procedure_result", "patient_history",
            "advice_notes", "patient_details", "followup_notes", "extra_notes",
            "additional_comments", "check_patient", "date_of_next_visit",
        ):
            rec.setdefault(key, rec.get(key) or "")

        rec.setdefault("next_visit_days", rec.get("next_visit_days"))

        if not isinstance(rec.get("vitals"), dict):
            rec["vitals"] = {}
        if not isinstance(rec.get("clinical_scores"), dict):
            rec["clinical_scores"] = {}
        if not isinstance(rec.get("status_updates"), dict):
            rec["status_updates"] = {}
        if not isinstance(rec.get("physical_examinations"), dict):
            rec["physical_examinations"] = {}

        # Fallback to 1 if not present
        company_val = rec.get("company_id")
        rec["company_id"] = OdooDataExtractor._m2o_id(company_val) if isinstance(company_val, (list, tuple)) else (company_val or 1)

        return rec

    async def get_last_indexed_date(self, model_name: str, instance_id: str = "default") -> Optional[datetime]:
        query = """
        SELECT last_write_date
        FROM etl_metadata
        WHERE odoo_model = :m AND odoo_instance_id = :instance_id
        """
        async with self.vector_engine.connect() as conn:
            row = (await conn.execute(
                text(query),
                {"m": model_name, "instance_id": instance_id},
            )).fetchone()
            return row[0] if row and row[0] else None

    async def update_etl_metadata(
        self,
        model_name: str,
        last_write_date: datetime,
        total_records: int,
        total_chunks: int,
        instance_id: str = "default",
    ):
        if isinstance(last_write_date, str):
            try:
                last_write_date = datetime.fromisoformat(
                    last_write_date.replace("Z", "+00:00")
                )
            except Exception:
                last_write_date = datetime.now()
        query = """
        INSERT INTO etl_metadata
            (odoo_instance_id, odoo_model, last_indexed_at, last_write_date, total_records, total_chunks)
        VALUES (:instance_id, :m, :ia, :ld, :tr, :tc)
        ON CONFLICT (odoo_instance_id, odoo_model) DO UPDATE SET
            last_indexed_at = :ia, last_write_date = :ld,
            total_records = :tr, total_chunks = :tc
        """
        async with self.vector_engine.begin() as conn:
            await conn.execute(
                text(query),
                {
                    "m": model_name,
                    "instance_id": instance_id,
                    "ia": datetime.now(),
                    "ld": last_write_date,
                    "tr": total_records,
                    "tc": total_chunks,
                },
            )

    async def get_existing_odoo_ids(self, odoo_model: str, instance_id: str = "default") -> set:
        query = """
        SELECT DISTINCT odoo_res_id
        FROM medical_rag_index
        WHERE odoo_model = :m AND odoo_instance_id = :instance_id
        """
        ids = set()
        async with self.vector_engine.connect() as conn:
            rows = (await conn.execute(
                text(query),
                {"m": odoo_model, "instance_id": instance_id},
            )).fetchall()
            for row in rows:
                if row[0] is not None:
                    ids.add(int(row[0]))
        return ids

    async def mark_records_as_synced(self, odoo_model: str, record_ids: List[int]) -> int:
        return 0

    async def extract_appointments(
        self,
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
        incremental: bool = True,
    ) -> List[Dict]:
        domain = [("appoint_state", "!=", "rejected")]
        if incremental and since_date:
            domain.append(("write_date", ">", since_date.strftime("%Y-%m-%d %H:%M:%S")))

        try:
            raw = await self._fetch_all_via_api(
                "/api/rag/appointments/fetch_all",
                domain,
                limit=limit,
            )
            records = [self._normalize_appointment(r) for r in raw]
            logger.info(f"Extracted {len(records):,} appointments via Odoo API")
            return records
        except Exception as e:
            logger.error(f"Appointment extraction error (API): {e}")
            return []

    def _normalize_appointment(self, record: Dict) -> Dict:
        customer = record.get("customer")
        patient_name = record.get("patient_name") or self._m2o_name(customer)
        patient_res_id = record.get("patient_res_id") or self._m2o_id(customer)
        patient_seq = record.get("patient_seq") or record.get("patient_id") or ""
        doctor = record.get("appoint_person_id")
        return {
            "id": record["id"],
            "appointment_number": record.get("appointment_number") or record.get("name", ""),
            "name": record.get("name", ""),
            "appoint_date": record.get("appoint_date") or "",
            "appoint_state": record.get("appoint_state") or "",
            "patient_name": patient_name,
            "patient_id": patient_seq,
            "patient_seq": patient_seq,
            "patient_res_id": patient_res_id,
            "doctor_name": record.get("doctor_name") or self._m2o_name(doctor),
            "doctor_res_id": record.get("doctor_res_id") or self._m2o_id(doctor),
            "description": record.get("description") or "",
            "amount_total": record.get("amount_total") or 0,
            "write_date": record.get("write_date") or "",
            "company_id": OdooDataExtractor._m2o_id(record.get("company_id")) if isinstance(record.get("company_id"), (list, tuple)) else (record.get("company_id") or 1),
        }

    async def extract_prescriptions(
        self,
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
        incremental: bool = True,
    ) -> List[Dict]:
        domain = [("state", "!=", "cancelled")]
        if incremental and since_date:
            domain.append(("write_date", ">", since_date.strftime("%Y-%m-%d %H:%M:%S")))

        try:
            raw = await self._fetch_all_via_api(
                "/api/rag/prescriptions/fetch_all",
                domain,
                limit=limit,
            )
            records = [self._normalize_rich_prescription(r) for r in raw]
            logger.info(f"Extracted {len(records):,} prescriptions via Odoo API")
            return records
        except Exception as e:
            logger.error(f"Prescription extraction error (API): {e}")
            return []

    async def extract_patients(
        self,
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
        incremental: bool = True,
    ) -> List[Dict]:
        seq_field = self._get_patient_sequence_field()
        domain = [(seq_field, "!=", False)]
        if incremental and since_date:
            domain.append(("write_date", ">", since_date.strftime("%Y-%m-%d %H:%M:%S")))

        try:
            raw = await self._fetch_all_via_api(
                "/api/rag/patients/fetch_all",
                domain,
                limit=limit,
            )
            records = [self._normalize_patient(r, seq_field=seq_field) for r in raw]
            logger.info(f"Extracted {len(records):,} patients via Odoo API")
            return records
        except Exception as e:
            logger.error(f"Patient extraction error (API): {e}")
            return []

    def _normalize_patient(self, record: Dict, seq_field: str = "patient_seq") -> Dict:
        return {
            "id": record["id"],
            "name": record.get("name", ""),
            "patient_seq": record.get(seq_field) or record.get("patient_seq") or record.get("seq") or "",
            "gender": record.get("gender") or "",
            "age": record.get("age") or "",
            "phone": record.get("phone") or "",
            "email": record.get("email") or "",
            "city": record.get("city") or "",
            "write_date": record.get("write_date") or "",
            "company_id": OdooDataExtractor._m2o_id(record.get("company_id")) if isinstance(record.get("company_id"), (list, tuple)) else (record.get("company_id") or 1),
        }

    async def extract_diseases(
        self,
        limit: Optional[int] = None,
        incremental: bool = False,
    ) -> List[Dict]:
        domain: List = []

        try:
            raw = await self._fetch_all_via_api(
                "/api/rag/diseases/fetch_all",
                domain,
                limit=limit,
            )
            logger.info(f"Extracted {len(raw):,} diseases via Odoo API")
            return raw
        except Exception as e:
            logger.error(f"Disease extraction error (API): {e}")
            return []
