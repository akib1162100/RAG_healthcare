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
                return len(data["result"]["data"])
    except Exception as e:
        return f"Error: {e}"
    return 0

def fetch_rag_data(endpoint):
    url = f"{RAG_API_URL}/api/v1/rag/{endpoint}?limit=1"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode()).get("total_records", 0)
    except Exception as e:
        return f"Error: {e}"

def generate_report():
    report = {
        "Odoo_Raw_Counts": {
            "patients": fetch_odoo_ids("res.partner"),
            "prescriptions": fetch_odoo_ids("prescription.order.knk"),
            "appointments": fetch_odoo_ids("wk.appointment"),
            "diseases": fetch_odoo_ids("medical.disease")
        },
        "RAG_Database_Counts": {
            "patients": fetch_rag_data("patient-data"),
            "prescriptions": fetch_rag_data("prescriptions"),
            "appointments": fetch_rag_data("appointments"),
            "diseases": fetch_rag_data("diseases")
        }
    }
    
    with open("P:\\RAG_healthcare\\verification_report.json", "w") as f:
        json.dump(report, f, indent=4)

if __name__ == "__main__":
    generate_report()
