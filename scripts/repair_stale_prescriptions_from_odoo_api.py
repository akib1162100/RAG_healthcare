import importlib.util
import json
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


def current_chunk0_map(cur):
    cur.execute(
        """
        SELECT odoo_res_id, metadata
        FROM medical_rag_index
        WHERE odoo_model = 'prescription.order.knk'
          AND chunk_index = 0
        """
    )
    rows = cur.fetchall()
    return {row[0]: row[1] or {} for row in rows}


def count_nonempty_list(obj, key):
    value = (obj or {}).get(key) or []
    return len(value) if isinstance(value, list) else 0


def has_text(obj, key):
    value = (obj or {}).get(key)
    return bool(value and str(value).strip() and str(value).strip().lower() != "false")


def source_has_nested_content(source):
    return any([
        count_nonempty_list(source, "medications") > 0,
        count_nonempty_list(source, "medical_history") > 0,
        count_nonempty_list(source, "old_history") > 0,
        count_nonempty_list(source, "complaints") > 0,
        count_nonempty_list(source, "diagnoses") > 0,
        count_nonempty_list(source, "investigations") > 0,
        count_nonempty_list(source, "procedures") > 0,
        count_nonempty_list(source, "exercises") > 0,
        count_nonempty_list(source, "family_history") > 0,
        count_nonempty_list(source, "social_history") > 0,
        has_text(source, "patient_details"),
        has_text(source, "patient_history"),
        has_text(source, "investigation_result"),
        has_text(source, "procedure_result"),
        has_text(source, "advice_notes"),
    ])


def is_stale(source, current):
    if not source_has_nested_content(source):
        return False
    if current is None:
        return True

    checks = [
        ("medications", count_nonempty_list),
        ("medical_history", count_nonempty_list),
        ("old_history", count_nonempty_list),
        ("complaints", count_nonempty_list),
        ("diagnoses", count_nonempty_list),
        ("investigations", count_nonempty_list),
        ("procedures", count_nonempty_list),
        ("exercises", count_nonempty_list),
        ("family_history", count_nonempty_list),
        ("social_history", count_nonempty_list),
    ]
    for key, fn in checks:
        if fn(source, key) > fn(current, key):
            return True

    text_checks = [
        "patient_details",
        "patient_history",
        "investigation_result",
        "procedure_result",
        "advice_notes",
    ]
    for key in text_checks:
        if has_text(source, key) and not has_text(current, key):
            return True

    return False


def upsert_prescription(cur, transformer, source):
    chunks = transformer.flatten_prescription(source)
    delete_sql = """
    DELETE FROM medical_rag_index
    WHERE odoo_model = 'prescription.order.knk'
      AND odoo_res_id = %s
      AND chunk_index >= %s
    """
    upsert_sql = """
    INSERT INTO medical_rag_index
        (odoo_model, odoo_res_id, chunk_index, content_text, metadata, embedding, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s::jsonb, NULL, NOW(), NOW())
    ON CONFLICT (odoo_model, odoo_res_id, chunk_index)
    DO UPDATE SET
        content_text = EXCLUDED.content_text,
        metadata = EXCLUDED.metadata,
        updated_at = NOW()
    """
    for text_content, metadata in chunks:
        cur.execute(
            upsert_sql,
            (
                "prescription.order.knk",
                source["id"],
                metadata.get("chunk_index", 0),
                text_content,
                json.dumps(metadata, default=str),
            ),
        )
    cur.execute(delete_sql, (source["id"], len(chunks)))
    return len(chunks)


def main():
    env = load_dotenv(ENV_PATH)
    api_key = choose_api_key(env)
    transformer = load_transformer()

    conn = db_connection(env)
    cur = conn.cursor()
    chunk0 = current_chunk0_map(cur)

    offset = 0
    stale_ids = []
    stale_sources = []
    processed = 0

    while True:
        page = fetch_page(env["ODOO_URL"], api_key, offset)
        if not page:
            break

        for source in page:
            processed += 1
            current = chunk0.get(source["id"])
            if is_stale(source, current):
                stale_ids.append(source["id"])
                stale_sources.append(source)

        offset += len(page)
        print(f"Scanned {processed} prescriptions, found {len(stale_ids)} stale so far...")
        if len(page) < PAGE_SIZE:
            break

    updated_chunks = 0
    for idx, source in enumerate(stale_sources, start=1):
        updated_chunks += upsert_prescription(cur, transformer, source)
        if idx % 100 == 0:
            conn.commit()
            print(f"Updated {idx}/{len(stale_sources)} stale prescriptions...")
    conn.commit()

    print(
        json.dumps(
            {
                "status": "success",
                "scanned": processed,
                "stale_prescriptions": len(stale_ids),
                "updated_chunks": updated_chunks,
            },
            indent=2,
        )
    )

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
