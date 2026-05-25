import requests
import json

url = "http://localhost:8000/api/v1/rag/chat"
headers = {"Content-Type": "application/json"}
payload = {
    "prompt": "What are my prescriptions?",
    "session_id": "test_session_123",
    "patient_seq": "20250700224002",
    "reset": False
}

response = requests.post(url, headers=headers, json=payload)
print(json.dumps(response.json(), indent=2))
