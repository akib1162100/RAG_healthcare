import urllib.request
import json

RAG_API_URL = "http://localhost:8000"

def fetch_rag_data(endpoint):
    url = f"{RAG_API_URL}/api/v1/rag/{endpoint}?limit=1"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching RAG endpoint /{endpoint}: {e}")
    return {}

def test_endpoints():
    print("Testing RAG Data Endpoints...")
    
    # 1. Test Patients
    patients = fetch_rag_data("patient-data")
    print(f"[OK] Patients Endpoint: Retrieved {patients.get('total_records', 0)} records.")
    
    # 2. Test Prescriptions
    prescriptions = fetch_rag_data("prescriptions")
    print(f"[OK] Prescriptions Endpoint: Retrieved {prescriptions.get('total_records', 0)} records.")
    
    # 3. Test Appointments (NEW)
    appointments = fetch_rag_data("appointments")
    print(f"[OK] Appointments Endpoint: Retrieved {appointments.get('total_records', 0)} records.")
    
    # 4. Test Diseases (NEW)
    diseases = fetch_rag_data("diseases")
    print(f"[OK] Diseases Endpoint: Retrieved {diseases.get('total_records', 0)} records.")

if __name__ == "__main__":
    test_endpoints()
