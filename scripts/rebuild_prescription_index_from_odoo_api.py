import importlib.util
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import psycopg2
import requests


WORKSPACE = Path(__file__).resolve().parents[1]
ENV_PATH = WORKSPACE / ".env"
TRANSFORMER_PATH = WORKSPACE / "app" / "etl" / "data_transformer.py"
PAGE_SIZE = 250


def load_dotenv(path: Path):
    data = {}
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def db_connection(env):
    parsed = urlparse(env["DATABASE_URL"].replace("+asyncpg", ""))
    host = parsed.hostname or "localhost"
    port = parsed.port or 5433
    if host == "db":
        host = "localhost"
        port = 5433
    return psycopg2.connect(
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        host=host,
        port=port,
    )


def load_transformer():
    spec = importlib.util.spec_from_file_location("medical_data_transformer_direct", TRANSFORMER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MedicalDataTransformer(chunk_size=800, chunk_overlap=150)


def normalize_prescription(record):
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

    for key in ("vitals", "clinical_scores", "status_updates", "physical_examinations"):
        if not isinstance(rec.get(key), dict):
            rec[key] = {}

    return rec


def fetch_page(base_url, api_key, offset):
    url = base_url.rstrip("/") + "/api/rag/prescriptions/fetch_all"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "domain": [],
            "limit": PAGE_SIZE,
            "offset": offset,
        },
    }
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    body = response.json()
    result = body.get("result") or {}
    if result.get("status") != "success":
        raise RuntimeError(result.get("message") or result)
    return result.get("data") or []


def choose_api_key(env):
    candidates = [
        env.get("ODOO_API_KEY", ""),
        "585f944f6b85a1a9b7bf8baa81729129147d4012",
        "2d08e96badd84f0fc0663da74eb36bab963efd3f",
    ]
    tried = []
    for api_key in candidates:
        if not api_key or api_key in tried:
            continue
        tried.append(api_key)
        try:
            fetch_page(env["ODOO_URL"], api_key, 0)
            return api_key
        except Exception:
            continue
    raise RuntimeError("No working Odoo API key found for prescriptions/fetch_all")


def main():
    env = load_dotenv(ENV_PATH)
    api_key = choose_api_key(env)
    transformer = load_transformer()

    conn = db_connection(env)
    cur = conn.cursor()

    cur.execute("DELETE FROM medical_rag_index WHERE odoo_model = %s", ("prescription.order.knk",))
    conn.commit()

    insert_sql = """
    INSERT INTO medical_rag_index
        (odoo_model, odoo_res_id, chunk_index, content_text, metadata, embedding, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s::jsonb, NULL, NOW(), NOW())
    ON CONFLICT (odoo_model, odoo_res_id, chunk_index)
    DO UPDATE SET
        content_text = EXCLUDED.content_text,
        metadata = EXCLUDED.metadata,
        embedding = EXCLUDED.embedding,
        updated_at = NOW()
    """

    total_records = 0
    total_chunks = 0
    last_write_date = None
    offset = 0

    while True:
        page = fetch_page(env["ODOO_URL"], api_key, offset)
        if not page:
            break

        batch = []
        for raw_record in page:
            record = normalize_prescription(raw_record)
            chunks = transformer.flatten_prescription(record)
            for content_text, metadata in chunks:
                batch.append((
                    "prescription.order.knk",
                    record["id"],
                    metadata.get("chunk_index", 0),
                    content_text,
                    json.dumps(metadata, default=str),
                ))
            total_records += 1
            total_chunks += len(chunks)

            write_date = record.get("write_date")
            if write_date:
                try:
                    parsed = datetime.fromisoformat(str(write_date).replace("Z", "+00:00"))
                    if last_write_date is None or parsed > last_write_date:
                        last_write_date = parsed
                except Exception:
                    pass

        cur.executemany(insert_sql, batch)
        conn.commit()
        offset += len(page)
        print(f"Indexed {total_records} prescriptions, {total_chunks} chunks so far...")

        if len(page) < PAGE_SIZE:
            break

    cur.execute(
        """
        INSERT INTO etl_metadata (odoo_model, last_indexed_at, last_write_date, total_records, total_chunks)
        VALUES (%s, NOW(), %s, %s, %s)
        ON CONFLICT (odoo_model) DO UPDATE SET
            last_indexed_at = EXCLUDED.last_indexed_at,
            last_write_date = EXCLUDED.last_write_date,
            total_records = EXCLUDED.total_records,
            total_chunks = EXCLUDED.total_chunks
        """,
        (
            "prescription.order.knk",
            last_write_date,
            total_records,
            total_chunks,
        ),
    )
    conn.commit()

    cur.close()
    conn.close()

    print(
        json.dumps(
            {
                "status": "success",
                "api_key_used": "configured",
                "records_indexed": total_records,
                "chunks_created": total_chunks,
                "last_write_date": last_write_date.isoformat() if last_write_date else None,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
