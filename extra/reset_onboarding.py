import os
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
config_dir = base_dir / "config"

# 1. Clear API keys so _check_config() returns False and opens setup overlay
api_file = config_dir / "api_keys.json"
if api_file.exists():
    api_file.unlink()
    print("Deleted api_keys.json")

# 2. Reset identity.json so is_setup_complete() returns False and starts at Assistant Identity screen
identity_file = config_dir / "identity.json"
default_identity = {
    "owner": {
        "name": "",
        "preferred_name": "",
        "role": "",
        "location": "",
        "interests": [],
        "about": ""
    },
    "assistant": {
        "name": "Brahma",
        "application_name": "Brahma Echo",
        "title": "Personal AI Assistant"
    },
    "behavior": {
        "mode": "professional",
        "proactive": True,
        "custom_instructions": ""
    },
    "system": {
        "shared_computer": False
    }
}

config_dir.mkdir(parents=True, exist_ok=True)
identity_file.write_text(json.dumps(default_identity, indent=4), encoding="utf-8")
print("Reset identity.json to defaults")

print("\nOnboarding has been completely reset! When you launch the application, it will open at Stage 1 of Onboarding.")
