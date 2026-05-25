import requests
import json
import traceback

api_key = "AIzaSyD2yKS9wq4Lqi44A980ou3C8rFrv9SkoiQ"
base_url = "http://localhost:8000/api/v1"

def run_tests():
    print("1. Setting API Key...")
    res1 = requests.post(f"{base_url}/config/api-key", json={"api_key": api_key})
    print(json.dumps(res1.json(), indent=2))

    print("\n2. Getting Available Models...")
    try:
        res2 = requests.get(f"{base_url}/config/debug-models")
        print(json.dumps(res2.json(), indent=2))
    except Exception as e:
        print(f"debug-models error: {e}")

    print("\n3. Testing RAG Chat Endpoint...")
    payload = {
        "prompt": "What are my prescriptions?",
        "session_id": "test_session_123",
        "patient_seq": "20250700224002",
        "reset": False
    }
    res3 = requests.post(f"{base_url}/rag/chat", json=payload)
    print("Response Status Code:", res3.status_code)
    try:
        data = res3.json()
        print("Response Text:", data.get('response', 'No response field'))
    except Exception as e:
        print("Error parsing final JSON:", e)
        print("Raw text:", res3.text)

if __name__ == "__main__":
    run_tests()
