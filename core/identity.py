import json
import os
from pathlib import Path
from typing import Dict, Any, List

def get_base_dir() -> Path:
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

class IdentityService:
    def __init__(self):
        self.config_file = get_base_dir() / "config" / "identity.json"
        self.data: Dict[str, Any] = {
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
        self.load()

    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    
                    # Deep merge to preserve defaults for missing keys
                    for section, values in loaded_data.items():
                        if section in self.data and isinstance(values, dict):
                            self.data[section].update(values)
                        else:
                            self.data[section] = values
            except Exception as e:
                print(f"Error loading identity config: {e}")
        else:
            self.save()

    def save(self):
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving identity config: {e}")

    # Assistant methods
    def get_assistant_name(self) -> str:
        return self.data["assistant"].get("name", "Brahma")
        
    def set_assistant_name(self, name: str):
        self.data["assistant"]["name"] = name
        self.save()

    def get_application_name(self) -> str:
        return self.data["assistant"].get("application_name", "Brahma Echo")
        
    def set_application_name(self, name: str):
        self.data["assistant"]["application_name"] = name
        self.save()

    def get_assistant_title(self) -> str:
        return self.data["assistant"].get("title", "Personal AI Assistant")
        
    def set_assistant_title(self, title: str):
        self.data["assistant"]["title"] = title
        self.save()

    # Owner Profile methods
    def get_owner_name(self) -> str:
        return self.data["owner"].get("name", "")
        
    def set_owner_name(self, name: str):
        self.data["owner"]["name"] = name
        if not self.data["owner"].get("preferred_name"):
            self.data["owner"]["preferred_name"] = name
        self.save()

    def get_owner_role(self) -> str:
        return self.data["owner"].get("role", "")
        
    def set_owner_role(self, role: str):
        self.data["owner"]["role"] = role
        self.save()

    def get_owner_location(self) -> str:
        return self.data["owner"].get("location", "")
        
    def set_owner_location(self, location: str):
        self.data["owner"]["location"] = location
        self.save()

    def get_owner_interests(self) -> List[str]:
        return self.data["owner"].get("interests", [])
        
    def set_owner_interests(self, interests: List[str]):
        self.data["owner"]["interests"] = interests
        self.save()

    def get_owner_about(self) -> str:
        return self.data["owner"].get("about", "")
        
    def set_owner_about(self, about: str):
        self.data["owner"]["about"] = about
        self.save()

    # Behavior methods
    def get_behavior_mode(self) -> str:
        return self.data["behavior"].get("mode", "professional")
        
    def set_behavior_mode(self, mode: str):
        self.data["behavior"]["mode"] = mode
        self.save()

    def get_custom_instructions(self) -> str:
        return self.data["behavior"].get("custom_instructions", "")
        
    def set_custom_instructions(self, instructions: str):
        self.data["behavior"]["custom_instructions"] = instructions
        self.save()
        
    def is_proactive(self) -> bool:
        return self.data["behavior"].get("proactive", True)
        
    def set_proactive(self, proactive: bool):
        self.data["behavior"]["proactive"] = proactive
        self.save()

    # System methods
    def is_shared_computer(self) -> bool:
        return self.data["system"].get("shared_computer", False)
        
    def set_shared_computer(self, is_shared: bool):
        self.data["system"]["shared_computer"] = is_shared
        self.save()

    def is_setup_complete(self) -> bool:
        # Consider setup complete if owner name is provided
        return bool(self.data["owner"].get("name", "").strip())

# Global singleton instance
identity = IdentityService()
