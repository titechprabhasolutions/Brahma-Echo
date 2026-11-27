from core.user_paths import get_user_data_dir
import json
import logging
import requests
from pathlib import Path
from typing import Optional
from or_client import client as openrouter_client

logger = logging.getLogger("llm_client")

LLMTR_URL = "https://llmtr.com/v1"
DEFAULT_LLMTR_MODEL = "qwen/qwen3.8-27b-free"


def _get_base_dir() -> Path:
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR = _get_base_dir()
SETTINGS_PATH = get_user_data_dir() / "config" / "app_settings.json"
API_KEY_PATH = get_user_data_dir() / "config" / "api_keys.json"

def _load_llmtr_api_key() -> str:
    try:
        with open(API_KEY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("llmtr_api_key", "").strip()
    except FileNotFoundError:
        return ""
    except Exception as e:
        logger.warning(f"[LLM Client] Failed to load LLMTR API key: {e}")
        return ""

class UnifiedAIClient:
    def __init__(self):
        self._provider = "OpenRouter"
        self._local_url = "http://localhost:11434/v1"
        self._local_model = "llama3.2"
        self._llmtr_model = DEFAULT_LLMTR_MODEL
        self.reload_settings()

    def reload_settings(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._provider = data.get("default_ai_provider", "OpenRouter")
            self._local_url = data.get("local_ai_url", "http://localhost:11434/v1").rstrip("/")
            self._local_model = data.get("local_ai_model", "llama3.2")
            self._llmtr_model = data.get("llmtr_model", DEFAULT_LLMTR_MODEL) or DEFAULT_LLMTR_MODEL
        except Exception as e:
            logger.error(f"[LLM Client] Failed to load settings: {e}")

    def _is_llmtr(self) -> bool:
        return (self._provider or "").strip().lower() == "llmtr"

    def _compatible_target(self) -> tuple[str, str, Optional[str], str]:
        if self._is_llmtr():
            api_key = _load_llmtr_api_key()
            if not api_key:
                raise PermissionError(
                    "LLMTR API key is missing. Add a key in Settings or config/api_keys.json."
                )
            return (LLMTR_URL, self._llmtr_model, api_key, "LLMTR")
        return (self._local_url, self._local_model, None, "Local AI")

    def _compatible_chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        response_format: Optional[dict] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        base_url, model, api_key, label = self._compatible_target()
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format:
            payload["response_format"] = response_format

        endpoint = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            resp = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=120
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content.strip() if content else None
            else:
                logger.error(f"[LLM Client] {label} Error {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            logger.error(f"[LLM Client] {label} Request Failed: {e}")
            return None

    def _local_chat_completion(self, messages: list[dict], temperature: float = 0.7, response_format: Optional[dict] = None) -> Optional[str]:
        return self._compatible_chat_completion(messages, temperature, response_format)

    def _parse_json_content(self, raw: str, label: str) -> dict:
        clean = raw.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1] if len(parts) > 1 else clean
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip().rstrip("`").strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            raise ValueError(f"{label} returned unparseable JSON: {e}\nRaw output: {raw[:200]}")

    def chat(self, prompt: str, system: str = "You are a helpful assistant.", history: Optional[list[dict]] = None, model: Optional[str] = None, max_tokens: int = 4096, temperature: float = 0.7) -> str:
        self.reload_settings()
        if self._provider == "Local" or self._is_llmtr():
            messages = [{"role": "system", "content": system}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": prompt})
            result = self._compatible_chat_completion(messages, temperature, max_tokens=max_tokens)
            if result:
                return result
            else:
                if self._is_llmtr():
                    raise RuntimeError("LLMTR request failed. Please check your API key and model name.")
                raise RuntimeError("Local AI request failed. Please check if Ollama or LM Studio is running.")
        else:
            return openrouter_client.chat(prompt, system, history, model, max_tokens, temperature)

    def chat_json(self, prompt: str, system: str = "Return ONLY valid JSON.", model: Optional[str] = None, max_tokens: int = 4096) -> dict:
        self.reload_settings()
        if self._provider == "Local" or self._is_llmtr():
            label = "LLMTR" if self._is_llmtr() else "Local AI"
            messages = [
                {"role": "system", "content": system + " Output valid JSON only, without any markdown formatting."},
                {"role": "user", "content": prompt}
            ]
            raw = self._compatible_chat_completion(messages, temperature=0.2, response_format={"type": "json_object"}, max_tokens=max_tokens)
            if not raw:
                raise RuntimeError(f"{label} request failed.")
            return self._parse_json_content(raw, label)
        else:
            return openrouter_client.chat_json(prompt, system, model, max_tokens)

    def vision(self, prompt: str, image_b64: str, mime: str = "image/png", system: str = "Analyze the image.", model: Optional[str] = None, max_tokens: int = 1024) -> str:
        self.reload_settings()
        if self._provider == "Local" or self._is_llmtr():
            label = "LLMTR" if self._is_llmtr() else "Local AI"
            messages = [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            result = self._compatible_chat_completion(messages, temperature=0.2, max_tokens=max_tokens)
            if result:
                return result
            raise RuntimeError(f"{label} vision request failed.")
        else:
            return openrouter_client.vision(prompt, image_b64, mime, system, model, max_tokens)

    def vision_from_file(self, prompt: str, image_path: str, system: str = "Analyze the image.", model: Optional[str] = None, max_tokens: int = 1024) -> str:
        self.reload_settings()
        if self._provider == "Local" or self._is_llmtr():
            import base64
            path = Path(image_path)
            mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
            mime = mime_map.get(path.suffix.lower(), "image/png")
            with open(path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")
            return self.vision(prompt, image_b64, mime, system, model, max_tokens)
        else:
            return openrouter_client.vision_from_file(prompt, image_path, system, model, max_tokens)

    def multi_turn(self, messages: list[dict], model: Optional[str] = None, max_tokens: int = 4096, temperature: float = 0.7) -> str:
        self.reload_settings()
        if self._provider == "Local" or self._is_llmtr():
            label = "LLMTR" if self._is_llmtr() else "Local AI"
            result = self._compatible_chat_completion(messages, temperature, max_tokens=max_tokens)
            if result:
                return result
            raise RuntimeError(f"{label} request failed.")
        else:
            return openrouter_client.multi_turn(messages, model, max_tokens, temperature)

client = UnifiedAIClient()
LLMClient = UnifiedAIClient
