import requests
import json
import time

base_url = "http://localhost:8000/api/v1"

def test_session():
    print("0. Setting up API Key...")
    api_key_res = requests.post(f"{base_url}/config/api-key", json={"api_key": "AIzaSyD2yKS9wq4Lqi44A980ou3C8rFrv9SkoiQ"})
    print("API Key Setup:", api_key_res.json().get('status'))

    session_id = "test_persistence_session_99"
    
    print("--- Test 1: Message WITH patient_seq constraints ---")
    payload1 = {
        "prompt": "Summarize the patient's condition",
        "session_id": session_id,
        "patient_seq": "20250700224002",
        "reset": True
    }
    res1 = requests.post(f"{base_url}/rag/chat", json=payload1)
    data1 = res1.json()
    print("Sources retrieved:", len(data1.get('sources', [])))
    print("Metadata applied:", data1.get('metadata', {}).get('filters_applied'))
    print("LLM Response:", data1.get('response'))
    
    print("\n--- Test 2: Message WITHOUT patient_seq constraints (Follow-up) ---")
    payload2 = {
        "prompt": "What was their blood pressure?",
        "session_id": session_id,
        "reset": False
    }
    res2 = requests.post(f"{base_url}/rag/chat", json=payload2)
    data2 = res2.json()
    print("Sources retrieved:", len(data2.get('sources', [])))
    print("Metadata applied (Should auto-recover parent ID):", data2.get('metadata', {}).get('filters_applied'))
    print("LLM Response:", data2.get('response'))

if __name__ == "__main__":
    test_session()
