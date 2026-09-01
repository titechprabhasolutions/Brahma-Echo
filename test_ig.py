import json
import os
from pathlib import Path
from instagrapi import Client
import time

def get_base_dir():
    return Path(__file__).resolve().parent

BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
SESSION_PATH = BASE_DIR / "config" / "ig_session.json"

def test_ig():
    print("[TEST] Loading credentials...")
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            username = data.get("instagram_username", "")
            password = data.get("instagram_password", "")
    except Exception as e:
        print(f"Error reading config: {e}")
        return

    if not username or not password:
        print("[TEST] No credentials found.")
        return
        
    print(f"[TEST] Attempting to login with {username}...")
    client = Client()
    try:
        if SESSION_PATH.exists():
            client.load_settings(SESSION_PATH)
        client.login(username, password)
        print("[TEST] Login successful!")
        
        # Check pending inbox and approve
        print("[TEST] Checking pending inbox...")
        pending = client.direct_pending_inbox()
        print(f"[TEST] Found {len(pending)} pending threads.")
        for p in pending:
            print(f"  - Approving Pending Thread ID: {p.id}")
            client.direct_pending_approve(p.id)
            time.sleep(1)
             
        # Check direct threads and reply
        print("[TEST] Checking direct threads...")
        threads = client.direct_threads(amount=5)
        print(f"[TEST] Found {len(threads)} threads.")
        for thread in threads:
            print(f"  - Thread ID: {thread.id}")
            if thread.messages:
                last_msg = thread.messages[0]
                if str(last_msg.user_id) != str(client.user_id):
                    print(f"    - Replying to {last_msg.user_id}: {last_msg.text}")
                    client.direct_send("Hello from Brahma AI! Your request was approved.", thread_ids=[thread.id])
                    time.sleep(2)
                else:
                    print("    - Already replied or sent by us.")
            else:
                print("    - No messages in thread.")
                
    except Exception as e:
        print(f"[TEST] Error: {e}")

if __name__ == "__main__":
    test_ig()
