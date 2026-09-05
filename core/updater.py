import os
import sys
import subprocess
import threading
import time
import requests
from PyQt6.QtCore import QObject, pyqtSignal

class UpdateChecker(QObject):
    update_available_sig = pyqtSignal(str)

    def __init__(self, repo_owner="titechprabhasolutions", repo_name="Brahma---personal", branch="main"):
        super().__init__()
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self._stop_event = threading.Event()
        self._check_thread = None

    def start(self):
        if self._check_thread is None:
            self._check_thread = threading.Thread(target=self._check_loop, daemon=True, name="updater-thread")
            self._check_thread.start()

    def stop(self):
        self._stop_event.set()
        if self._check_thread:
            self._check_thread.join(timeout=1.0)

    def _get_local_hash(self):
        try:
            output = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            return output.decode("utf-8").strip()
        except Exception:
            return None

    def _get_remote_hash(self):
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/commits/{self.branch}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("sha")
        except Exception as e:
            print(f"[Updater] Error fetching remote hash: {e}")
        return None

    def _check_loop(self):
        while not self._stop_event.is_set():
            local_hash = self._get_local_hash()
            remote_hash = self._get_remote_hash()

            if local_hash and remote_hash and local_hash != remote_hash:
                print(f"[Updater] Update detected! Local: {local_hash[:7]}, Remote: {remote_hash[:7]}")
                self.update_available_sig.emit(remote_hash)
                break # Stop checking once an update is detected

            # Check every hour
            for _ in range(3600):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

def apply_update_and_restart():
    print("[Updater] Applying update...")
    try:
        # Fetch the latest changes from the origin
        subprocess.check_call(["git", "fetch", "origin", "main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Hard reset to the remote branch to ensure clean state
        subprocess.check_call(["git", "reset", "--hard", "origin/main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("[Updater] Update applied successfully. Restarting application...")
        # Restart the app
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        print(f"[Updater] Failed to apply update: {e}")
