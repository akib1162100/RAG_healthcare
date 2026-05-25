"""
Test script: Verify chat context preservation for patient 20250800494012.
Simulates two messages on the same session (same channel) and checks
whether the 2nd response references the fainting topic from message 1.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
SESSION_ID = "odoo_channel_test_context_01"
PATIENT_SEQ = "20250800494012"

def test_context_preserved():
    print("=" * 70)
    print("CHAT CONTEXT PRESERVATION TEST")
    print(f"Patient: {PATIENT_SEQ}  |  Session: {SESSION_ID}")
    print("=" * 70)

    # --- Message 1: Ask about fainting history ---
    print("\n--- MESSAGE 1: Fainting history ---")
    payload1 = {
        "prompt": "has fainted give me history",
        "session_id": SESSION_ID,
        "patient_seq": PATIENT_SEQ,
        "reset": True  # Fresh session
    }
    res1 = requests.post(f"{BASE_URL}/rag/chat", json=payload1, timeout=60)
    data1 = res1.json()

    print(f"  Status: {res1.status_code}")
    print(f"  Sources: {len(data1.get('sources', []))}")
    meta1 = data1.get('metadata', {})
    print(f"  context_preserved: {meta1.get('context_preserved')}")
    print(f"  message_count: {meta1.get('message_count')}")
    print(f"  Response (first 300 chars):\n    {data1.get('response', '')[:300]}")

    # Brief pause to simulate user reading
    time.sleep(2)

    # --- Message 2: Follow-up about fast aid (should reference fainting) ---
    print("\n--- MESSAGE 2: Suggest fast aid (follow-up, same session) ---")
    payload2 = {
        "prompt": "suggest fast aid",
        "session_id": SESSION_ID,
        "patient_seq": PATIENT_SEQ,
        "reset": False  # Continue session
    }
    res2 = requests.post(f"{BASE_URL}/rag/chat", json=payload2, timeout=60)
    data2 = res2.json()

    print(f"  Status: {res2.status_code}")
    print(f"  Sources: {len(data2.get('sources', []))}")
    meta2 = data2.get('metadata', {})
    print(f"  context_preserved: {meta2.get('context_preserved')}")
    print(f"  message_count: {meta2.get('message_count')}")
    print(f"  Response (first 500 chars):\n    {data2.get('response', '')[:500]}")

    # --- Verdict ---
    print("\n" + "=" * 70)
    print("VERDICT:")
    response2_lower = data2.get('response', '').lower()
    if meta2.get('context_preserved') is True:
        print("  ✅ context_preserved = True  (session was reused)")
    else:
        print("  ❌ context_preserved = False (session was NOT reused)")

    if meta2.get('message_count', 0) >= 2:
        print(f"  ✅ message_count = {meta2.get('message_count')}  (multi-turn detected)")
    else:
        print(f"  ❌ message_count = {meta2.get('message_count')}  (expected >= 2)")

    if any(word in response2_lower for word in ['faint', 'syncop', 'loss of consciousness', 'collapse', 'unconscious']):
        print("  ✅ Response 2 references fainting from message 1!")
    else:
        print("  ⚠️  Response 2 may not explicitly mention fainting — review the text above")
    print("=" * 70)


if __name__ == "__main__":
    test_context_preserved()
