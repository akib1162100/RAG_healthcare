import requests

def main():
    try:
        url = "http://localhost:8069/api/rag/chat"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "prompt": "Hello test",
                "session_id": "test_script_session_1",
                "patient_seq": "20250600042005"
            }
        }
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        print("Response from Odoo:", res.text)
    except Exception as e:
        print("Error calling Odoo:", e)

if __name__ == "__main__":
    main()
