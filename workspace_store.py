from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import google.generativeai as genai


def _base_dir() -> Path:
    return Path(__file__).resolve().parent


BASE_DIR = _base_dir()
CONFIG_DIR = BASE_DIR / "config"
STORE_FILE = CONFIG_DIR / "workspace_store.sqlite3"


def _ensure_dir() -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _clean_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def _title_from_message(message: str) -> str:
    text = _clean_text(message)
    if not text:
        return "New Conversation"
    text = re.sub(r"^[\"'`]+|[\"'`]+$", "", text)
    text = re.sub(r"[^\w\s&/-]+", "", text)
    words = text.split()
    if not words:
        return "New Conversation"
    stop = {"a", "an", "the", "and", "or", "to", "for", "of", "in", "on", "with", "my", "your", "please"}
    pieces: list[str] = []
    for idx, word in enumerate(words[:7]):
        low = word.lower()
        if idx > 0 and low in stop:
            pieces.append(low)
        else:
            pieces.append(word[:1].upper() + word[1:].lower())
    return " ".join(pieces)[:64]


def _serialize_attachments(attachments: list[dict[str, Any]] | None) -> str:
    try:
        return json.dumps(attachments or [], ensure_ascii=False)
    except Exception:
        return "[]"


def _deserialize_attachments(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


class WorkspaceStore:
    def __init__(self, db_path: Path | None = None):
        _ensure_dir()
        self._db_path = Path(db_path or STORE_FILE)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    pinned INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    attachments_json TEXT NOT NULL DEFAULT '[]',
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL UNIQUE,
                    created_at INTEGER NOT NULL,
                    source_conversation TEXT
                );

                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    def _get_state(self, key: str) -> str | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT value FROM state WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    def _set_state(self, key: str, value: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO state(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def get_active_conversation_id(self) -> str | None:
        return self._get_state("active_conversation_id")

    def set_active_conversation_id(self, conversation_id: str | None) -> None:
        if conversation_id:
            self._set_state("active_conversation_id", conversation_id)

    def create_conversation(self, title: str = "New Conversation") -> str:
        conversation_id = str(uuid.uuid4())
        stamp = _now_ms()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations(id, title, created_at, updated_at, pinned)
                VALUES(?, ?, ?, ?, 0)
                """,
                (conversation_id, title or "New Conversation", stamp, stamp),
            )
        self.set_active_conversation_id(conversation_id)
        return conversation_id

    def ensure_active_conversation(self, first_user_message: str | None = None) -> str:
        conversation_id = self.get_active_conversation_id()
        if conversation_id and self.get_conversation(conversation_id):
            return conversation_id
        return self.create_conversation(_title_from_message(first_user_message or "New Conversation"))

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            convo = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if not convo:
                return None
            messages = conn.execute(
                """
                SELECT role, content, timestamp, attachments_json
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC, rowid ASC
                """,
                (conversation_id,),
            ).fetchall()
            return {
                "id": convo["id"],
                "title": convo["title"],
                "createdAt": int(convo["created_at"]),
                "updatedAt": int(convo["updated_at"]),
                "pinned": bool(convo["pinned"]),
                "messages": [
                    {
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": int(row["timestamp"]),
                        "attachments": _deserialize_attachments(row["attachments_json"]),
                    }
                    for row in messages
                ],
            }

    def conversation_has_messages(self, conversation_id: str) -> bool:
        if not conversation_id:
            return False
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM messages WHERE conversation_id = ? LIMIT 1",
                (conversation_id,),
            ).fetchone()
        return bool(row)

    def _summarize_session_async(self, conversation_id: str) -> None:
        messages = self.get_message_payloads(conversation_id)
        if not messages:
            return
        
        user_texts = [m["text"] for m in messages if m["role"] == "user"]
        if not user_texts:
            return
            
        full_text = "\n".join(user_texts)
        if len(full_text) > 10000:
            full_text = full_text[-10000:]
            
        def _do_summary():
            try:
                from google import genai
                base_dir = Path(__file__).resolve().parent
                key_path = base_dir / "config" / "api_keys.json"
                with open(key_path, "r", encoding="utf-8") as f:
                    api_key = json.load(f)["gemini_api_key"]
                
                client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
                prompt = (
                    "Summarize the following user conversation into 1-2 short, conversational sentences "
                    "that describe what the user was doing or asking about. Phrase it as 'Yesterday you were...'\n\n"
                    f"Conversation:\n{full_text}"
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"temperature": 0.5},
                )
                
                text_parts = []
                for candidate in getattr(response, "candidates", []) or []:
                    content = getattr(candidate, "content", None)
                    if not content: continue
                    for part in getattr(content, "parts", []) or []:
                        pt = getattr(part, "text", None)
                        if pt: text_parts.append(pt)
                summary = "".join(text_parts).strip()
                if not summary:
                    summary = (getattr(response, "text", "") or "").strip()
                
                if summary:
                    self._set_state("last_session_summary", summary)
            except Exception as e:
                print(f"[WorkspaceStore] Failed to summarize session: {e}")
                
        threading.Thread(target=_do_summary, daemon=True).start()

    def rollover_active_conversation_on_startup(self) -> str:
        current = self.get_active_conversation_id()
        if current and not self.conversation_has_messages(current):
            return current
        if current:
            self._summarize_session_async(current)
        return self.create_conversation("New Conversation")

    def list_conversations(self, search: str = "") -> list[dict[str, Any]]:
        search = _clean_text(search)
        where = ""
        params: list[Any] = []
        if search:
            where = "WHERE title LIKE ? OR id IN (SELECT conversation_id FROM messages WHERE content LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])
        query = f"""
            SELECT id, title, created_at, updated_at, pinned
            FROM conversations
            {where}
            ORDER BY pinned DESC, updated_at DESC, created_at DESC
        """
        with self._lock, self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "createdAt": int(row["created_at"]),
                    "updatedAt": int(row["updated_at"]),
                    "pinned": bool(row["pinned"]),
                }
                for row in rows
            ]

    def grouped_conversations(self, search: str = "") -> dict[str, list[dict[str, Any]]]:
        items = self.list_conversations(search)
        now = _now_ms()
        day_ms = 24 * 60 * 60 * 1000
        groups = {"Today": [], "Yesterday": [], "Previous 7 Days": [], "Older": []}
        for item in items:
            delta = now - int(item["updatedAt"])
            if delta < day_ms:
                groups["Today"].append(item)
            elif delta < day_ms * 2:
                groups["Yesterday"].append(item)
            elif delta < day_ms * 8:
                groups["Previous 7 Days"].append(item)
            else:
                groups["Older"].append(item)
        return {key: val for key, val in groups.items() if val}

    def _touch_conversation(self, conn: sqlite3.Connection, conversation_id: str) -> None:
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (_now_ms(), conversation_id),
        )

    def rename_conversation(self, conversation_id: str, title: str) -> None:
        title = _clean_text(title) or "Conversation"
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title[:80], _now_ms(), conversation_id),
            )

    def pin_conversation(self, conversation_id: str, pinned: bool = True) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE conversations SET pinned = ?, updated_at = ? WHERE id = ?",
                (1 if pinned else 0, _now_ms(), conversation_id),
            )

    def delete_conversation(self, conversation_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            current = self.get_active_conversation_id()
            if current == conversation_id:
                conn.execute("DELETE FROM state WHERE key = 'active_conversation_id'")

    def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        timestamp: int | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> None:
        content = _clean_text(content)
        if not content:
            return
        stamp = int(timestamp or _now_ms())
        with self._lock, self._connect() as conn:
            convo = conn.execute("SELECT id, title FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
            if convo is None:
                conversation_id = self.create_conversation(_title_from_message(content) if role == "user" else "New Conversation")
                with self._connect() as conn2:
                    conn2.execute(
                        """
                        INSERT INTO messages(id, conversation_id, role, content, timestamp, attachments_json)
                        VALUES(?, ?, ?, ?, ?, ?)
                        """,
                        (str(uuid.uuid4()), conversation_id, role, content, stamp, _serialize_attachments(attachments)),
                    )
                    if role == "user" and (convo_title := _title_from_message(content)):
                        conn2.execute("UPDATE conversations SET title = ? WHERE id = ?", (convo_title, conversation_id))
                    self._touch_conversation(conn2, conversation_id)
                    return
            conn.execute(
                """
                INSERT INTO messages(id, conversation_id, role, content, timestamp, attachments_json)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), conversation_id, role, content, stamp, _serialize_attachments(attachments)),
            )
            if role == "user":
                row = conn.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
                current_title = (row["title"] if row else "").strip()
                if current_title in {"New Conversation", "Conversation", ""}:
                    conn.execute(
                        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                        (_title_from_message(content), stamp, conversation_id),
                    )
                else:
                    self._touch_conversation(conn, conversation_id)
            else:
                self._touch_conversation(conn, conversation_id)

    def record_chat(
        self,
        role: str,
        content: str,
        *,
        conversation_id: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> str:
        if role == "user":
            conversation_id = conversation_id or self.ensure_active_conversation(content)
        else:
            conversation_id = conversation_id or self.get_active_conversation_id() or self.ensure_active_conversation()
        self.append_message(conversation_id, role, content, attachments=attachments)
        if role == "user":
            self._ingest_memory(content, conversation_id)
        self.set_active_conversation_id(conversation_id)
        return conversation_id

    def _ingest_memory(self, user_text: str, conversation_id: str) -> None:
        text = _clean_text(user_text)
        if len(text) < 4:
            return
        text_low = text.lower()
        candidates: list[str] = []
        patterns = [
            r"\bi(?:'m| am)?\s+(?:a|an)?\s*(?:software|python|web|desktop|mobile|full[- ]?stack|frontend|backend|data|ai|ml)?\s*(?:developer|engineer|creator|builder|user)?\s*(?:who\s+)?(?:use|uses|using|like|likes|love|loves|prefer|prefers|own|owns|work with|work on)\s+(.+)",
            r"\bmy favorite\s+(.+)",
            r"\bi (?:use|prefer|like|love|own|build|built|am using|work with|work on)\s+(.+)",
            r"\bi'm\s+(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text_low, flags=re.IGNORECASE)
            if match:
                value = _clean_text(match.group(1))
                if value:
                    candidates.append(value[:220])
        if not candidates:
            if any(trigger in text_low for trigger in ("prefers", "uses", "uses firebase", "likes", "owns", "working on")):
                candidates.append(text[:220])
        with self._lock, self._connect() as conn:
            for item in candidates:
                normalized = _clean_text(item)
                if not normalized:
                    continue
                conn.execute(
                    """
                    INSERT OR IGNORE INTO memories(id, content, created_at, source_conversation)
                    VALUES(?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), normalized, _now_ms(), conversation_id),
                )

    def search_memories(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query = _clean_text(query)
        if not query:
            return []
        tokens = [t for t in re.split(r"\s+", query.lower()) if len(t) > 2][:8]
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT id, content, created_at, source_conversation FROM memories ORDER BY created_at DESC"
            ).fetchall()
        scored: list[tuple[int, dict[str, Any]]] = []
        for row in rows:
            content = row["content"]
            content_low = content.lower()
            score = 0
            for token in tokens:
                if token in content_low:
                    score += 3
            overlap = set(tokens) & set(re.findall(r"[a-z0-9]+", content_low))
            score += len(overlap)
            if score:
                scored.append(
                    (
                        score,
                        {
                            "id": row["id"],
                            "content": content,
                            "createdAt": int(row["created_at"]),
                            "sourceConversation": row["source_conversation"],
                        },
                    )
                )
        scored.sort(key=lambda item: (-item[0], -item[1]["createdAt"]))
        return [item[1] for item in scored[:limit]]

    def memory_context(self, query: str, limit: int = 5) -> str:
        memories = self.search_memories(query, limit=limit)
        if not memories:
            return ""
        lines = ["Relevant Memories:"]
        for memory in memories:
            lines.append(f"- {memory['content']}")
        return "\n".join(lines)

    def get_message_payloads(self, conversation_id: str) -> list[dict[str, Any]]:
        convo = self.get_conversation(conversation_id)
        if not convo:
            return []
        return list(convo.get("messages", []))

    def export_conversation(self, conversation_id: str, path: str | Path) -> Path:
        convo = self.get_conversation(conversation_id)
        if not convo:
            raise ValueError("Conversation not found")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(convo, indent=2, ensure_ascii=False), encoding="utf-8")
        return target

    def all_memories(self) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT id, content, created_at, source_conversation FROM memories ORDER BY created_at DESC"
            ).fetchall()
        return [
            {
                "id": row["id"],
                "content": row["content"],
                "createdAt": int(row["created_at"]),
                "sourceConversation": row["source_conversation"],
            }
            for row in rows
        ]


_STORE = WorkspaceStore()


def store() -> WorkspaceStore:
    return _STORE
