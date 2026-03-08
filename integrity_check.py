import urllib.request
import json
import time

ODOO_API_URL = "http://localhost:8016"
ODOO_API_KEY = "585f944f6b85a1a9b7bf8baa81729129147d4012"
RAG_API_URL = "http://localhost:8000"

def fetch_odoo_ids(model):
    url = f"{ODOO_API_URL}/api/rag/list_ids"
    domain = []
    if model == "wk.appointment":
        domain = [("appoint_state", "!=", "rejected")]
    elif model == "prescription.order.knk":
        domain = [("state", "!=", "cancelled")]
    elif model == "res.partner":
        domain = [("partner_type", "=", "patient")]
        
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": model,
            "domain": domain,
            "limit": None,
            "offset": 0
        }
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {ODOO_API_KEY}",
        "Content-Type": "application/json"
    })
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if "result" in data and data["result"].get("status") == "success":
                return set(data["result"]["data"])
    except Exception as e:
        print(f"Error fetching {model} from Odoo: {e}")
    return set()

def fetch_rag_status():
    url = f"{RAG_API_URL}/api/v1/etl/index-status"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching RAG status: {e}")
    return {}

def main():
    print("Starting Integrity Check Odoo vs RAG...")
    
    # Wait for sync to complete (up to 300s)
    print("Waiting for any ongoing synchronizations (RAG Sync)...")
    for _ in range(30):
        status = fetch_rag_status()
        # the status doesn't explicitly show 'running', so we just wait 10s and check
        time.sleep(2)
        
    # 1. Fetch Odoo Record IDs
    print("\nFetching Odoo data...")
    odoo_patients = fetch_odoo_ids("res.partner")
    odoo_appointments = fetch_odoo_ids("wk.appointment")
    odoo_prescriptions = fetch_odoo_ids("prescription.order.knk")
    odoo_diseases = fetch_odoo_ids("medical.disease")

    # 2. Fetch RAG Status
    print("Fetching RAG status...")
    rag_status = fetch_rag_status()
    etl_meta = rag_status.get("etl_metadata", {})
    rag_patients_count = etl_meta.get("res.partner", {}).get("total_records", 0)
    rag_appointments_count = etl_meta.get("wk.appointment", {}).get("total_records", 0)
    rag_prescriptions_count = etl_meta.get("prescription.order.knk", {}).get("total_records", 0)
    rag_diseases_count = etl_meta.get("medical.disease", {}).get("total_records", 0)
    
    print("\n=== Integrity Report ===")
    def verify(name, odoo_set, rag_count):
        match = len(odoo_set) == rag_count
        status_text = "PASSED" if match else "FAILED"
        print(f"[{status_text}] {name:15}: Odoo={len(odoo_set):4} | RAG_Database={rag_count:4}")
        if not match:
            print(f"    -> WARNING: Missing {len(odoo_set) - rag_count} records in RAG database. Rerunning sync might be needed.")

    verify("Patients", odoo_patients, rag_patients_count)
    verify("Appointments", odoo_appointments, rag_appointments_count)
    verify("Prescriptions", odoo_prescriptions, rag_prescriptions_count)
    verify("Diseases", odoo_diseases, rag_diseases_count)

if __name__ == "__main__":
    main()
