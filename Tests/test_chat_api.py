import requests
import json

url = "http://localhost:8000/api/v1/rag/chat"

# The request body
data = {
    "prompt": "Tell me about the patient's physical examinations and GCS scores.",
    "session_id": "test_session_123",
    "patient_seq": "20250700265001"
}

print("=== REQUEST BODY ===")
print(json.dumps(data, indent=2))
print("\n=== INVOKING ENDPOINT ===")

try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    print("\n=== RAW API RESPONSE ===")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(e.response.text)
