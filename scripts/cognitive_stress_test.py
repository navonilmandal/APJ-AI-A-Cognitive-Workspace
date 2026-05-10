import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"
USER_ID = "stress_test_user"

def ingest_memories(memories):
    print(f"--- Ingesting {len(memories)} memories ---")
    payload = []
    for m in memories:
        payload.append({
            "user_id": USER_ID,
            "memory_type": "personal",
            "conversation_id": f"stress_conv_{int(time.time())}",
            "speaker": "user",
            "message": m,
            "source": "stress_test"
        })
    start = time.time()
    resp = requests.post(f"{BASE_URL}/memory/ingest", json=payload)
    duration = time.time() - start
    print(f"Ingestion took {duration:.2f}s | Status: {resp.status_code}")
    return duration

def trigger_reflection(query=None):
    print(f"--- Triggering Reflection Cycle (Query: {query}) ---")
    start = time.time()
    resp = requests.post(f"{BASE_URL}/reflection/generate", params={"user_id": USER_ID, "query": query})
    duration = time.time() - start
    print(f"Reflection took {duration:.2f}s | Count: {len(resp.json()) if resp.status_code == 200 else 'Error'}")
    return resp.json(), duration

def run_test():
    # 1. Temporal Shift Test
    print("\n[TEST 1] Temporal Reasoning (Past vs Present)")
    ingest_memories([
        "Back in university, I used to play video games for 10 hours a day. I was obsessed with RPGs.",
        "That was years ago. Nowadays, I find gaming quite a waste of time. I haven't played a single game in 6 months.",
        "My current focus is purely on cognitive AI and neural architectures. That's where all my passion is now."
    ])
    trigger_reflection("past activities and current interests")

    # 2. Contradiction Test
    print("\n[TEST 2] Contradiction Handling")
    ingest_memories([
        "I absolutely love Python. It's the most beautiful language ever designed.",
        "Actually, after working with high-performance systems, I've started to hate Python's speed. I find it really annoying now."
    ])
    trigger_reflection("programming language preferences")

    # 3. Final Insight Check
    print("\n[FINAL RESULTS] Current Cognitive Profile")
    resp = requests.get(f"{BASE_URL}/reflection/list", params={"user_id": USER_ID})
    print(json.dumps(resp.json(), indent=2))

if __name__ == "__main__":
    run_test()
