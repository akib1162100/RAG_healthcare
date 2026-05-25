import requests

url = "http://localhost:8000/api/v1/etl/index-medical"

# The request body
data = {
    "models": ["prescription.order.knk"],
    "incremental": False,
    "limit": None
}

print("Triggering full reindex...")
try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    res = response.json()
    print("=== INDEXING RESULTS ===")
    print(f"Status: {res.get('status')}")
    print(f"Total Records Indexed: {res.get('total_records')}")
    print(f"Total Chunks Created: {res.get('total_chunks')}")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(e.response.text)
