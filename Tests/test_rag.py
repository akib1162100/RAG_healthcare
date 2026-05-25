import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def trigger_index():
    print("Triggering index...")
    url = f"{BASE_URL}/etl/index-medical"
    data = {"models": ["prescription.order.knk"], "incremental": False}
    response = requests.post(url, json=data)
    print("Index Response:", response.json())

def test_chat():
    print("Testing chat...")
    url = f"{BASE_URL}/rag/chat"
    data = {
        "prompt": "Tell me about the patient's physical examinations, complaints, signs, medical history, procedures, dyspnea, motor power, and BMI from their recent prescription.",
        "session_id": "test_session_123"
    }
    response = requests.post(url, json=data)
    try:
        print("Chat Response:", json.dumps(response.json(), indent=2))
    except:
        print(response.text)

if __name__ == "__main__":
    trigger_index()
    test_chat()
