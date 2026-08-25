from __future__ import annotations

import hashlib
import os
import platform
import re
import sqlite3
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import xml.etree.ElementTree as ET
import ctypes
from ctypes import wintypes

import pyautogui

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None

try:
    from pywinauto import Desktop
except Exception:  # pragma: no cover
    Desktop = None


_APP_ALIASES: dict[str, tuple[str, ...]] = {
    "discord": ("discord",),
    "whatsapp": ("whatsapp",),
    "telegram": ("telegram",),
    "signal": ("signal",),
    "skype": ("skype",),
    "zoom": ("zoom",),
    "teams": ("teams", "microsoft teams"),
    "phone link": ("phone link", "your phone"),
    "messenger": ("messenger", "facebook messenger"),
    "instagram": ("instagram",),
    "facebook": ("facebook",),
    "slack": ("slack",),
    "gmail": ("gmail", "google mail"),
    "mail": ("mail", "outlook"),
}

_MESSAGE_HINTS = (
    "new message",
    "message",
    "chat",
    "dm",
    "direct message",
    "unread",
    "notification",
    "mention",
    "reply",
    "preview",
    "received",
)

_CALL_HINTS = (
    "incoming call",
    "call from",
    "voice call",
    "video call",
    "ringing",
    "incoming video",
    "incoming voice",
    "accept",
    "answer",
    "decline",
    "reject",
    "hang up",
    "end call",
)

_ACCEPT_HINTS = ("accept", "answer", "pick up", "join", "allow")
_DECLINE_HINTS = ("decline", "reject", "ignore", "hang up", "end", "cut", "dismiss")
_WINDOW_CALL_HINTS = (
    "call",
    "incoming",
    "ringing",
    "voice",
    "video",
    "answer",
    "accept",
    "decline",
    "reject",
    "hang up",
    "end call",
    "meeting",
    "joined",
    "conference",
)


def _db_path() -> Path:
    local = os.environ.get("LOCALAPPDATA", "")
    return Path(local) / "Microsoft" / "Windows" / "Notifications" / "wpndatabase.db"


def _normalize_app_from_primary(primary: str | None, fallback: str = "") -> str | None:
    hay = f"{primary or ''} {fallback or ''}".lower()
    mapping = [
        ("whatsapp", "WhatsApp"),
        ("discord", "Discord"),
        ("telegram", "Telegram"),
        ("signal", "Signal"),
        ("skype", "Skype"),
        ("zoom", "Zoom"),
        ("teams", "Teams"),
        ("phone link", "Phone Link"),
        ("yourphone", "Phone Link"),
        ("phonelink", "Phone Link"),
        ("messenger", "Messenger"),
        ("instagram", "Instagram"),
        ("facebook", "Facebook"),
        ("slack", "Slack"),
        ("outlook", "Mail"),
        ("mail", "Mail"),
        ("gmail", "Gmail"),
        ("sms", "Messages"),
        ("messages", "Messages"),
    ]
    for token, name in mapping:
        if token in hay:
            return name
    return None


def _parse_toast_payload(payload: bytes | str | None) -> tuple[str, list[str], list[str], str]:
    if payload is None:
        return "", [], [], ""
    if isinstance(payload, (bytes, bytearray)):
        raw = payload.decode("utf-8", "ignore")
    else:
        raw = str(payload)

    texts: list[str] = []
    actions: list[str] = []
    try:
        root = ET.fromstring(raw)
        for node in root.findall(".//text"):
            txt = (node.text or "").strip()
            if txt:
                texts.append(txt)
        for node in root.findall(".//action"):
            for attr in ("content", "arguments", "hint-inputId"):
                val = (node.get(attr) or "").strip()
                if val:
                    actions.append(val)
    except Exception:
        pass

    flat = " ".join(texts + actions + [raw]).lower()
    kind = "call" if any(k in flat for k in _CALL_HINTS) else "message"
    if "call" in flat and not any(m in flat for m in _MESSAGE_HINTS):
        kind = "call"
    return raw, texts, actions, kind


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _proc_name(pid: int | None) -> str:
    if not pid or psutil is None:
        return ""
    try:
        return psutil.Process(pid).name().lower()
    except Exception:
        return ""


def _match_app(text: str, proc_name: str) -> str | None:
    hay = f"{text} {proc_name}".lower()
    for canonical, aliases in _APP_ALIASES.items():
        if any(alias in hay for alias in aliases):
            return canonical
    return None


def _collect_text_snapshot(win, limit: int = 18) -> list[str]:
    out: list[str] = []
    try:
        title = _norm(win.window_text())
        if title:
            out.append(title)
    except Exception:
        pass

    try:
        desc = win.descendants()
    except Exception:
        desc = []

    for child in desc:
        text = ""
        for attr in ("window_text",):
            try:
                text = getattr(child, attr)() or ""
            except Exception:
                text = ""
            if text:
                break
        if not text:
            try:
                text = getattr(getattr(child, "element_info", None), "name", "") or ""
            except Exception:
                text = ""
        text = _norm(text)
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break

    return out


def _is_notification_shape(win) -> bool:
    try:
        rect = win.rectangle()
        width = abs(rect.right - rect.left)
        height = abs(rect.bottom - rect.top)
        return width <= 720 and height <= 320
    except Exception:
        return False


def _contains_any(hay: str, needles: tuple[str, ...]) -> bool:
    return any(needle in hay for needle in needles)


def _window_title(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(512)
    try:
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, len(buf))
    except Exception:
        return ""
    return _norm(buf.value)


def _window_class(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    try:
        ctypes.windll.user32.GetClassNameW(hwnd, buf, len(buf))
    except Exception:
        return ""
    return _norm(buf.value)


def _window_pid(hwnd: int) -> int:
    pid = wintypes.DWORD()
    try:
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    except Exception:
        return 0
    return int(pid.value)


def _enum_visible_windows() -> list[dict]:
    results: list[dict] = []
    user32 = ctypes.windll.user32
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    @enum_proc
    def callback(hwnd, lparam):
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            title = _window_title(hwnd)
            if not title:
                return True
            results.append({
                "hwnd": int(hwnd),
                "title": title,
                "class": _window_class(hwnd),
                "pid": _window_pid(hwnd),
            })
        except Exception:
            pass
        return True

    try:
        user32.EnumWindows(callback, 0)
    except Exception:
        pass
    return results


def _extract_preview(lines: list[str], app: str) -> str:
    cleaned: list[str] = []
    app_l = app.lower()
    for line in lines:
        if not line:
            continue
        if line == app_l:
            continue
        if line in {"message", "notification", "new message"}:
            continue
        cleaned.append(line)
    if not cleaned:
        return ""
    if len(cleaned) >= 2 and cleaned[0] in _APP_ALIASES:
        cleaned = cleaned[1:]
    return " ".join(cleaned[:3]).strip()


_current_player_alias = None
_current_audio_path = None
_speech_sink: Callable[[str], None] | None = None


def set_speech_sink(sink: Callable[[str], None] | None) -> None:
    global _speech_sink
    _speech_sink = sink

def _cleanup_current_audio() -> None:
    global _current_player_alias, _current_audio_path
    if _current_player_alias is not None:
        try:
            ctypes.windll.winmm.mciSendStringW(f"stop {_current_player_alias}", None, 0, None)
        except Exception:
            pass
        try:
            ctypes.windll.winmm.mciSendStringW(f"close {_current_player_alias}", None, 0, None)
        except Exception:
            pass
        _current_player_alias = None

    if _current_audio_path is not None:
        try:
            if os.path.exists(_current_audio_path):
                os.remove(_current_audio_path)
        except Exception:
            pass
        _current_audio_path = None


def _speak_edge_native(text: str) -> None:
    global _current_player_alias, _current_audio_path
    text = (text or "").strip()
    if not text:
        return

    try:
        import edge_tts
    except Exception as exc:  # pragma: no cover
        print(f"[AttentionMonitor] Edge TTS import failed: {exc}")
        return

    try:
        _cleanup_current_audio()
    except Exception:
        pass

    audio_path = os.path.join(tempfile.gettempdir(), f"brahma_edge_tts_{uuid.uuid4().hex}.mp3")
    try:
        # Use a male neural voice for app speech so daily briefing and alerts sound
        # closer to Brahma's normal male audio output.
        communicator = edge_tts.Communicate(text, voice="en-US-GuyNeural")
        communicator.save_sync(audio_path)
    except Exception as exc:  # pragma: no cover
        print(f"[AttentionMonitor] Edge TTS generation failed: {exc}")
        _cleanup_current_audio()
        return

    player_alias = f"brahma_tts_{uuid.uuid4().hex}"
    try:
        result = ctypes.windll.winmm.mciSendStringW(
            f'open "{audio_path}" type mpegvideo alias {player_alias}',
            None,
            0,
            None,
        )
        if result != 0:
            raise RuntimeError(f"MCI open failed: {result}")

        result = ctypes.windll.winmm.mciSendStringW(
            f"play {player_alias} wait",
            None,
            0,
            None,
        )
        if result != 0:
            raise RuntimeError(f"MCI play failed: {result}")

        _current_player_alias = player_alias
        _current_audio_path = audio_path
    except Exception as exc:  # pragma: no cover
        print(f"[AttentionMonitor] Edge TTS playback failed: {exc}")
        _cleanup_current_audio()
        return


_speech_sink = None


def set_speech_sink(sink_fn) -> None:
    global _speech_sink
    _speech_sink = sink_fn


def speak_native(text: str) -> None:
    text = (text or "").strip()
    if not text:
        return
    _speak_edge_native(text)


def stop_native_speech() -> None:
    _cleanup_current_audio()


def _focus_window_by_app(app: str) -> bool:
    if Desktop is None:
        return False
    try:
        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            title = _norm(win.window_text())
            proc = _proc_name(getattr(win, "process_id", lambda: None)())
            if _match_app(title, proc) == app:
                try:
                    win.set_focus()
                except Exception:
                    pass
                try:
                    win.restore()
                except Exception:
                    pass
                return True
    except Exception:
        pass
    return False


def _click_best_button(app: str, action: str) -> bool:
    if Desktop is None:
        return False
    hints = _ACCEPT_HINTS if action == "accept" else _DECLINE_HINTS
    try:
        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            title = _norm(win.window_text())
            proc = _proc_name(getattr(win, "process_id", lambda: None)())
            if _match_app(title, proc) != app and app not in title:
                continue
            try:
                for ctrl in win.descendants():
                    try:
                        text = _norm(ctrl.window_text() or getattr(getattr(ctrl, "element_info", None), "name", ""))
                    except Exception:
                        text = ""
                    if text and _contains_any(text, hints):
                        try:
                            ctrl.click_input()
                            return True
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass
    return False


def handle_call_action(event: dict, action: str) -> str:
    app = _norm(event.get("app") or "")
    if not app:
        return "No app was detected for that call."

    if action in {"pick_up", "answer", "accept"}:
        if _click_best_button(app, "accept"):
            return f"Picked up the call on {event.get('app', 'the app')}."
        if _focus_window_by_app(app):
            try:
                pyautogui.press("enter")
                return f"Tried to pick up the call on {event.get('app', 'the app')}."
            except Exception:
                pass
        return f"I found the call on {event.get('app', 'the app')}, but could not confirm the answer button."

    if action in {"ignore", "decline", "reject", "cut"}:
        if _click_best_button(app, "decline"):
            return f"Declined the call on {event.get('app', 'the app')}."
        if _focus_window_by_app(app):
            try:
                pyautogui.press("esc")
                return f"Tried to decline the call on {event.get('app', 'the app')}."
            except Exception:
                pass
        return f"I found the call on {event.get('app', 'the app')}, but could not confirm the decline button."

    return "Unknown call action."


def read_event_preview(event: dict) -> str:
    preview = (event.get("preview") or "").strip()
    app = (event.get("app") or "the app").strip()
    if preview:
        return f"You received a message on {app}. {preview}"
    return f"You received a message on {app}."


@dataclass
class _WindowState:
    signature: str = ""
    last_seen: float = 0.0


class AttentionMonitor:
    def __init__(
        self,
        on_event: Callable[[dict], None] | None = None,
        interval: float = 2.0,
    ):
        self._on_event = on_event
        self._interval = max(1.0, float(interval))
        self._running = False
        self._thread: threading.Thread | None = None
        self._db = _db_path()
        self._last_id = 0
        self._seen_keys: set[str] = set()
        self._seen_max = 80

    def start(self) -> None:
        if self._running:
            return
        self._last_id = self._current_max_id()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        if not self._db.exists():
            print(f"[AttentionMonitor] notification DB not found: {self._db}")
            return
        while self._running:
            try:
                self._poll_once()
            except Exception as exc:
                print(f"[AttentionMonitor] poll failed: {exc}")
            time.sleep(self._interval)

    def _current_max_id(self) -> int:
        try:
            with sqlite3.connect(self._db) as con:
                cur = con.cursor()
                cur.execute("SELECT COALESCE(MAX(Id), 0) FROM Notification WHERE Type='toast'")
                row = cur.fetchone()
                return int(row[0] or 0)
        except Exception:
            return 0

    def _remember_seen(self, key: str) -> None:
        self._seen_keys.add(key)
        if len(self._seen_keys) > self._seen_max:
            self._seen_keys = set(list(self._seen_keys)[-self._seen_max :])

    def _poll_once(self) -> None:
        now = time.time()
        self._poll_toasts(now)
        self._poll_windows(now)

    def _poll_toasts(self, now: float) -> None:
        with sqlite3.connect(self._db, timeout=1.5) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(
                """
                SELECT N.Id, N.HandlerId, N.Type, N.Tag, N.ArrivalTime, N.Payload, H.PrimaryId
                FROM Notification AS N
                LEFT JOIN NotificationHandler AS H ON H.RecordId = N.HandlerId
                WHERE N.Type='toast' AND N.Id > ?
                ORDER BY N.Id ASC
                """,
                (self._last_id,),
            )
            rows = cur.fetchall()

        for row in rows:
            nid = int(row["Id"] or 0)
            self._last_id = max(self._last_id, nid)

            raw, texts, actions, kind = _parse_toast_payload(row["Payload"])
            primary = row["PrimaryId"] or ""
            app = _normalize_app_from_primary(primary, " ".join(texts[:2]) or raw)
            if not app:
                continue

            flat = " ".join(texts + actions + [raw]).lower()
            if any(word in flat for word in ("start app", "screenshot copied", "never lose access")):
                continue

            if kind == "call":
                if not any(k in flat for k in _CALL_HINTS):
                    if not any(x in flat for x in ("incoming", "ringing", "accept", "decline", "answer", "reject")):
                        continue
            elif not any(k in flat for k in _MESSAGE_HINTS) and not texts:
                continue

            preview = ""
            if texts:
                if len(texts) >= 2:
                    preview = " ".join(texts[1:3]).strip()
                else:
                    preview = texts[0].strip()
            if not preview and actions:
                preview = " ".join(actions[:2]).strip()

            dedupe = hashlib.sha1(
                f"{app}|{kind}|{preview}|{raw[:240]}".encode("utf-8", "ignore")
            ).hexdigest()
            if dedupe in self._seen_keys:
                continue
            self._remember_seen(dedupe)

            event = {
                "kind": kind,
                "app": app,
                "title": texts[0] if texts else app,
                "preview": preview,
                "source": "wpndb",
                "notification_id": nid,
                "arrival_time": row["ArrivalTime"],
                "timestamp": now,
                "raw": raw,
                "primary_id": primary,
                "actions": actions,
            }

            if self._on_event:
                self._on_event(event)

    def _poll_windows(self, now: float) -> None:
        for win in _enum_visible_windows():
            title = win.get("title") or ""
            pid = int(win.get("pid") or 0)
            proc_name = _proc_name(pid)
            app = _match_app(title, proc_name)
            if not app:
                continue

            hay = f"{title} {win.get('class') or ''} {proc_name}".lower()
            if "brahma" in hay:
                continue

            if app in {"Zoom", "Teams", "WhatsApp"} and _contains_any(hay, ("meeting", "call", "incoming", "ringing", "conference", "joined")):
                pass
            elif not _contains_any(hay, _WINDOW_CALL_HINTS):
                continue

            dedupe = hashlib.sha1(
                f"window|{app}|{title}|{pid}".encode("utf-8", "ignore")
            ).hexdigest()
            if dedupe in self._seen_keys:
                continue
            self._remember_seen(dedupe)

            event = {
                "kind": "call",
                "app": app,
                "title": title,
                "preview": title,
                "source": "window",
                "notification_id": None,
                "arrival_time": None,
                "timestamp": now,
                "raw": title,
                "primary_id": proc_name,
                "actions": [],
            }
            if self._on_event:
                self._on_event(event)
