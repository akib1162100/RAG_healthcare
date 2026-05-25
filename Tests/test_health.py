import requests

def check_health():
    try:
        res = requests.get("http://localhost:8000/api/v1/config/status")
        print(res.json())
        
        # Test chat alias directly
        payload = {
            "prompt": "Hello test",
            "session_id": "test_alias_boot_1",
            "patient_seq": "20250600042005"
        }
        chat_res = requests.post("http://localhost:8000/chat", json=payload)
        print("Alias Chat Response:", chat_res.status_code)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check_health()
