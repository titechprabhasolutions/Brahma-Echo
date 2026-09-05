from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

def _load_discord_module():
    try:
        import discord as mod
        return mod
    except Exception:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "discord.py"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            import discord as mod
            return mod
        except Exception:
            return None


discord = _load_discord_module()

from google import genai

from llm_client import client as openrouter_client


logger = logging.getLogger("brahma echo.discord")


def _base_dir() -> Path:
    return Path(__file__).resolve().parent


BASE_DIR = _base_dir()
API_KEYS_FILE = BASE_DIR / "config" / "api_keys.json"


def _load_api_keys() -> dict:
    try:
        data = json.loads(API_KEYS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _extract_gemini_text(response) -> str:
    text_parts: list[str] = []
    try:
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", None)
                if part_text:
                    text_parts.append(part_text)
    except Exception:
        pass

    text = "".join(text_parts).strip()
    if text:
        return text

    try:
        return (getattr(response, "text", "") or "").strip()
    except Exception:
        return ""


def _looks_like_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(token in msg for token in (
        "429",
        "quota",
        "rate limit",
        "resource_exhausted",
        "too many requests",
        "limit",
        "exceeded",
    ))


class DiscordBotService:
    def __init__(
        self,
        *,
        status_callback: Optional[Callable[[str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self._status_callback = status_callback or (lambda *_: None)
        self._log_callback = log_callback or (lambda *_: None)
        self._token = ""
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = None
        self._lock = threading.Lock()
        self._stopping = False
        self._app_submitter: Optional[Callable[[str, str], None]] = None
        self._active_channel = None
        self._pending_channels = deque()
        self._target_channel_id: int | None = None

    def bind_app_submitter(self, submitter: Callable[[str, str], None]):
        self._app_submitter = submitter

    def set_target_channel_id(self, channel_id: str | int | None):
        try:
            cid = int(str(channel_id).strip())
            self._target_channel_id = cid if cid > 0 else None
        except Exception:
            self._target_channel_id = None

    def is_running(self) -> bool:
        client = self._client
        return bool(client and not client.is_closed())

    def _emit_status(self, message: str):
        try:
            self._status_callback(message)
        except Exception:
            logger.exception("Discord status callback failed")

    def _emit_log(self, message: str):
        try:
            self._log_callback(message)
        except Exception:
            logger.exception("Discord log callback failed")

    def mirror_chat_event(self, event: dict):
        if not isinstance(event, dict):
            return
        role = (event.get("role") or "").strip().lower()
        text = (event.get("text") or "").strip()
        source = (event.get("source") or "local").strip().lower()
        if not text:
            return
        channel = self._target_channel_id or self._active_channel
        if source == "discord":
            channel = self._pending_channels[0] if self._pending_channels else None
            if role == "user":
                return
            if self._pending_channels:
                self._pending_channels.popleft()
        if channel is None:
            return
        if self._loop is None or self._stopping:
            return
        asyncio.run_coroutine_threadsafe(self._send_channel_message(channel, role, text), self._loop)

    def _get_target_channel(self):
        if self._client is None or self._target_channel_id is None:
            return None
        try:
            return self._client.get_channel(self._target_channel_id)
        except Exception:
            return None

    async def _send_channel_message(self, channel, role: str, text: str):
        if channel is None:
            return
        if isinstance(channel, int):
            try:
                resolved = self._client.get_channel(channel) if self._client else None
                if resolved is None and self._client is not None:
                    resolved = await self._client.fetch_channel(channel)
                channel = resolved
            except Exception as exc:
                logger.warning("Discord channel resolve failed: %s", exc)
                return
        prefix = "Brahma Echo" if role == "assistant" else "You" if role == "user" else "System"
        payload = f"**{prefix}**: {text}"
        try:
            if len(payload) <= 1900:
                await channel.send(payload, allowed_mentions=discord.AllowedMentions.none())
            else:
                for part in self._split_reply(payload):
                    await channel.send(part, allowed_mentions=discord.AllowedMentions.none())
        except Exception as exc:
            logger.warning("Discord mirror send failed: %s", exc)

    def start(self, token: str):
        token = (token or "").strip()
        if not token:
            raise ValueError("Discord bot token is missing.")
        if discord is None:
            raise RuntimeError("discord.py is not installed. Add it to requirements and install dependencies.")

        if self.is_running():
            if token == self._token:
                self._emit_status("Discord bot already running.")
                return
            self.stop()

        self._token = token
        self._stopping = False
        self._thread = threading.Thread(target=self._thread_main, name="DiscordBotThread", daemon=True)
        self._thread.start()
        self._emit_status("Connecting Discord bot...")

    def stop(self):
        with self._lock:
            if self._stopping:
                return
            self._stopping = True
            client = self._client
            loop = self._loop
            thread = self._thread
            self._client = None
            self._loop = None
            self._thread = None

        if client is not None and loop is not None and not loop.is_closed():
            try:
                fut = asyncio.run_coroutine_threadsafe(client.close(), loop)
                fut.result(timeout=8)
            except Exception:
                pass

        if thread is not None and thread.is_alive():
            thread.join(timeout=8)

        self._emit_status("Discord bot stopped.")

    def _thread_main(self):
        try:
            asyncio.run(self._run())
        except Exception as exc:
            logger.exception("Discord bot thread crashed")
            self._emit_status(f"Discord error: {exc}")

    async def _run(self):
        self._loop = asyncio.get_running_loop()
        login_failure_type = getattr(discord, "LoginFailure", None)

        while not self._stopping:
            intents = discord.Intents.default()
            intents.guilds = True
            intents.messages = True
            intents.dm_messages = True
            intents.message_content = True

            client = discord.Client(intents=intents)
            self._client = client

            @client.event
            async def on_ready():
                try:
                    try:
                        await client.change_presence(
                            status=discord.Status.online,
                            activity=discord.Activity(
                                type=discord.ActivityType.listening,
                                name="Brahma Echo commands",
                            ),
                        )
                    except Exception:
                        pass
                    self._emit_status(f"Discord bot online as {client.user}.")
                    self._emit_log(f"SYS: Discord bot connected as {client.user}.")
                except Exception:
                    pass

            @client.event
            async def on_message(message):
                if self._stopping or message.author.bot:
                    return
                self._active_channel = message.channel
                if self._target_channel_id is not None and message.channel.id != self._target_channel_id and message.guild is not None:
                    if not (client.user and client.user in message.mentions):
                        return
                if message.guild is None:
                    should_reply = True
                    content = message.content.strip()
                else:
                    bot_user = client.user
                    should_reply = bool(bot_user and bot_user in message.mentions)
                    content = message.content.replace(str(bot_user.mention) if bot_user else "", "").strip()
                if not should_reply:
                    return

                if not content:
                    content = message.content.strip()

                if self._app_submitter is not None:
                    self._pending_channels.append(message.channel)
                    try:
                        await asyncio.to_thread(self._app_submitter, content, "discord")
                    except Exception as exc:
                        logger.warning("Discord app-submit failed: %s", exc)
                        if self._pending_channels:
                            self._pending_channels.pop()
                        await message.reply(
                            "I couldn’t hand that command to Brahma Echo.",
                            mention_author=False,
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                    return

                try:
                    reply = await asyncio.to_thread(self._generate_reply, content)
                except Exception as exc:
                    reply = f"I hit an error while replying: {exc}"

                reply = self._trim_reply(reply)
                if not reply:
                    reply = "I’m here, but I couldn’t generate a response right now."

                try:
                    if len(reply) <= 1900:
                        await message.reply(
                            reply,
                            mention_author=False,
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                    else:
                        first = True
                        for part in self._split_reply(reply):
                            if first:
                                await message.reply(
                                    part,
                                    mention_author=False,
                                    allowed_mentions=discord.AllowedMentions.none(),
                                )
                                first = False
                            else:
                                await message.channel.send(
                                    part,
                                    allowed_mentions=discord.AllowedMentions.none(),
                                )
                except Exception:
                    await message.channel.send(
                        reply[:1900],
                        allowed_mentions=discord.AllowedMentions.none(),
                    )

            try:
                await client.start(self._token)
                if self._stopping:
                    break
                self._emit_status("Discord bot disconnected. Reconnecting...")
            except Exception as exc:
                if self._stopping:
                    break
                self._emit_status(f"Discord error: {exc}")
                if login_failure_type and isinstance(exc, login_failure_type):
                    break
                await asyncio.sleep(5)
            finally:
                try:
                    if not client.is_closed():
                        await client.close()
                except Exception:
                    pass

        self._emit_status("Discord bot offline.")
        with self._lock:
            self._client = None
            self._loop = None

    def _split_reply(self, text: str, limit: int = 1900) -> list[str]:
        text = (text or "").strip()
        if len(text) <= limit:
            return [text]
        parts: list[str] = []
        while text:
            if len(text) <= limit:
                parts.append(text)
                break
            cut = text.rfind("\n", 0, limit)
            if cut < 500:
                cut = text.rfind(". ", 0, limit)
            if cut < 500:
                cut = limit
            parts.append(text[:cut].strip())
            text = text[cut:].strip()
        return [p for p in parts if p]

    def _trim_reply(self, text: str) -> str:
        return (text or "").strip().replace("\r\n", "\n")

    def _generate_reply(self, prompt: str) -> str:
        prompt = (prompt or "").strip()
        if not prompt:
            return "Tell me what you need help with."

        keys = _load_api_keys()
        gemini_key = (keys.get("gemini_api_key") or "").strip()
        openrouter_key = (keys.get("openrouter_api_key") or "").strip()
        system_prompt = (
            "You are Brahma Echo inside Discord. "
            "Be concise, accurate, and helpful. "
            "Keep replies friendly and under 250 words unless the user asks for detail."
        )

        if gemini_key:
            try:
                client = genai.Client(
                    api_key=gemini_key,
                    http_options={"api_version": "v1beta"},
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{system_prompt}\n\nUser: {prompt}",
                    config={"temperature": 0.5},
                )
                text = _extract_gemini_text(response)
                if text:
                    return text
            except Exception as exc:
                if not _looks_like_limit_error(exc):
                    logger.warning("Gemini Discord reply failed, falling back to OpenRouter: %s", exc)

        if openrouter_key:
            try:
                return openrouter_client.chat(
                    prompt,
                    system=system_prompt,
                    temperature=0.5,
                    max_tokens=900,
                ).strip()
            except Exception as exc:
                logger.warning("OpenRouter Discord reply failed: %s", exc)

        return "I couldn’t reach the AI providers right now."
