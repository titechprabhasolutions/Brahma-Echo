# actions/instagram_chat.py
"""
Instagram Chat Integration for Brahma AI.

Listens for incoming DMs on Instagram and replies using Brahma's core generation.
"""

import threading
import time
import json
import os
from pathlib import Path

# Provide a fallback if instagrapi fails to install or load
try:
    from instagrapi import Client
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    INSTAGRAPI_AVAILABLE = False

_reply_callback = None
_thread = None
_running = False
_client = None
_last_processed_msgs = {}
_auto_threads = set()

def ig_log(msg):
    try:
        print(msg)
    except Exception:
        print(msg.encode('ascii', 'replace').decode('ascii'))
    with open("ig_debug.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def get_base_dir():
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
SESSION_PATH = BASE_DIR / "config" / "ig_session.json"

def set_ig_prompt_callback(callback):
    """
    callback should take (thread_id: str, username: str, message: str, is_auto: bool)
    If is_auto is True, it returns the AI response string directly.
    If False, it prompts the user locally and returns None.
    """
    global _reply_callback
    _reply_callback = callback

def add_auto_thread(thread_id):
    _auto_threads.add(thread_id)
    ig_log(f"[InstagramChat] Thread {thread_id} added to auto mode.")

def send_direct_reply(thread_id, text):
    if _client:
        try:
            _client.direct_send(text, thread_ids=[thread_id])
            ig_log(f"[InstagramChat] Sent manual reply to {thread_id}: {text[:40]}...")
        except Exception as e:
            ig_log(f"[InstagramChat] Error sending manual reply: {e}")

def get_recent_messages(amount=5) -> str:
    """Returns a formatted string of the most recent messages for the AI to read to the user."""
    if not _client:
        return "Error: Instagram daemon is not running or client is not initialized."
    try:
        threads = _client.direct_threads(amount=amount)
        if not threads:
            return "You have no recent messages."
            
        result = []
        for thread in threads:
            latest_msg = thread.messages[0] if thread.messages else None
            if latest_msg:
                sender = thread.users[0].username if thread.users else "Unknown"
                # Check if the last message was sent by us or them
                if str(latest_msg.user_id) == str(_client.user_id):
                    result.append(f"- You replied to {sender}: \"{latest_msg.text}\"")
                else:
                    result.append(f"- {sender} said: \"{latest_msg.text}\"")
        return "\n".join(result)
    except Exception as e:
        return f"Error fetching messages: {e}"

def _load_credentials():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("instagram_username", ""), data.get("instagram_password", "")
    except Exception:
        return "", ""

def _instagram_loop():
    global _client, _running
    
    username, password = _load_credentials()
    if not username or not password:
        print("[InstagramChat] Missing credentials in config/api_keys.json. Stopping daemon.")
        _running = False
        return

    _client = Client()
    _client.delay_range = [1, 3] # Keep delay low to avoid rate limits but not seem totally like a bot

    ig_log(f"[InstagramChat] Attempting login for {username}...")
    try:
        if SESSION_PATH.exists():
            _client.load_settings(SESSION_PATH)
            
        try:
            _client.login(username, password)
            _client.get_timeline_feed() # Validate session
        except Exception as e:
            ig_log(f"[InstagramChat] Session invalid, relogging: {e}")
            _client.login(username, password, relogin=True)
            
        _client.dump_settings(SESSION_PATH)
        ig_log("[InstagramChat] Login successful. Listening for DMs...")
    except Exception as e:
        ig_log(f"[InstagramChat] Login failed: {e}")
        _running = False
        return

    # To avoid being rate-limited too fast, poll every 20 seconds
    POLL_INTERVAL = 20
    
    while _running:
        try:
            # Get recent threads
            threads = _client.direct_threads(amount=10)
            for thread in threads:
                latest_msg = thread.messages[0] if thread.messages else None
                
                # Check if it's sent by someone else and we haven't replied
                if latest_msg and str(latest_msg.user_id) != str(_client.user_id):
                    if _last_processed_msgs.get(thread.id) != latest_msg.id:
                        _last_processed_msgs[thread.id] = latest_msg.id
                        
                        text = latest_msg.text
                        sender_username = thread.users[0].username if thread.users else "Unknown"
                        
                        ig_log(f"[InstagramChat] New message from {sender_username}: {text}")
                        
                        if _reply_callback:
                            is_auto = str(thread.id) in _auto_threads
                            ai_response = _reply_callback(str(thread.id), sender_username, text, is_auto)
                            if ai_response:
                                ig_log(f"[InstagramChat] Replying to {sender_username}: {ai_response[:40]}...")
                                _client.direct_send(ai_response, thread_ids=[thread.id])
                                
                        time.sleep(2)
            
            # Check pending inbox (message requests) and approve them
            pending = _client.direct_pending_inbox()
            for thread in pending:
                ig_log(f"[InstagramChat] Approving message request from {thread.users[0].username if thread.users else 'Unknown'}")
                _client.direct_pending_approve(thread.id)
                time.sleep(1)
                        
        except Exception as e:
            ig_log(f"[InstagramChat] Error in polling loop: {e}")
            
        time.sleep(POLL_INTERVAL)

def start_daemon():
    global _thread, _running
    ig_log("[InstagramChat] start_daemon() was invoked!")
    if not INSTAGRAPI_AVAILABLE:
        ig_log("[InstagramChat] instagrapi not installed. Run 'pip install instagrapi'")
        return
        
    if _running:
        ig_log("[InstagramChat] Daemon is already running.")
        return
        
    _running = True
    _thread = threading.Thread(target=_instagram_loop, daemon=True)
    _thread.start()

def stop_daemon():
    global _running
    _running = False
