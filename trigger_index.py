import requests
import json

url = "http://localhost:8000/api/v1/etl/index-medical"
payload = {
    "model": "prescription.order.knk",
    "limit": 100,
    "incremental": False
}
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
