# actions/calendar_scheduler.py
"""
Calendar and Schedule Management for Brahma AI.

Allows creating, listing, checking, and managing calendar appointments,
meetings, and events with local persistent storage and .ics calendar exports.
"""

import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_FILE = BASE_DIR / "memory" / "calendar_events.json"

PLUGIN = {
    "name": "calendar_scheduler",
    "description": (
        "Manages calendar events, meetings, and schedules. Supports actions: "
        "'add_event', 'list_events', 'check_day', 'delete_event', 'get_upcoming', 'export_ics'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Action: add_event, list_events, check_day, delete_event, get_upcoming, export_ics",
            },
            "title": {
                "type": "STRING",
                "description": "Title or summary of the meeting/event.",
            },
            "date": {
                "type": "STRING",
                "description": "Date of event (YYYY-MM-DD or 'today', 'tomorrow').",
            },
            "time": {
                "type": "STRING",
                "description": "Time of event (HH:MM in 24h format, e.g. '14:30' or '3:00 PM').",
            },
            "duration_minutes": {
                "type": "NUMBER",
                "description": "Duration in minutes (default: 30).",
            },
            "location": {
                "type": "STRING",
                "description": "Location or online meeting URL (optional).",
            },
            "description": {
                "type": "STRING",
                "description": "Additional notes or agenda (optional).",
            },
            "event_id": {
                "type": "STRING",
                "description": "ID of event to delete (optional).",
            },
        },
        "required": ["action"],
    },
}


def _load_events() -> list[dict]:
    try:
        if EVENTS_FILE.exists():
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_events(events: list[dict]) -> None:
    try:
        EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Calendar] Save error: {e}")


def _parse_date(date_str: str | None) -> str:
    """Normalizes natural date strings to YYYY-MM-DD."""
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d")

    d = date_str.lower().strip()
    now = datetime.now()

    if d in ("today", "bugün"):
        return now.strftime("%Y-%m-%d")
    elif d in ("tomorrow", "yarın"):
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    elif d in ("yesterday", "dün"):
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    # Try standard formats
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return now.strftime("%Y-%m-%d")


def _parse_time(time_str: str | None) -> str:
    """Normalizes time string to HH:MM."""
    if not time_str:
        return datetime.now().strftime("%H:%M")

    t = time_str.strip().upper()
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%I %p", "%H.%M"):
        try:
            return datetime.strptime(t, fmt).strftime("%H:%M")
        except ValueError:
            pass
    return time_str


def calendar_scheduler(
    parameters: dict,
    response: str | None = None,
    player=None,
    session_memory=None,
    speak=None,
) -> str:
    """
    Main entry point for calendar operations.
    """
    p = parameters or {}
    action = p.get("action", "list_events").lower().strip()
    title = p.get("title", "").strip()
    date_str = _parse_date(p.get("date"))
    time_str = _parse_time(p.get("time"))
    duration = int(p.get("duration_minutes") or 30)
    location = p.get("location", "").strip()
    desc = p.get("description", "").strip()
    event_id = p.get("event_id", "").strip()

    events = _load_events()

    if action in ("add", "add_event", "create", "new"):
        if not title:
            return "Please provide a title or name for the calendar event."

        new_event = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "date": date_str,
            "time": time_str,
            "duration_minutes": duration,
            "location": location,
            "description": desc,
            "created_at": datetime.now().isoformat(),
        }
        events.append(new_event)
        # Keep sorted by date and time
        events.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))
        _save_events(events)

        if player:
            try:
                player.write_log(f"[Calendar] Scheduled: '{title}' on {date_str} at {time_str}")
            except Exception:
                pass

        return f"Event '{title}' scheduled for {date_str} at {time_str} ({duration} mins)."

    elif action in ("list", "list_events", "upcoming", "get_upcoming"):
        now_date = datetime.now().strftime("%Y-%m-%d")
        upcoming = [e for e in events if e.get("date", "") >= now_date]

        if not upcoming:
            return "You have no upcoming events on your calendar."

        lines = [f"📅 Upcoming Events ({len(upcoming)}):"]
        for ev in upcoming[:8]:
            loc_str = f" @ {ev['location']}" if ev.get("location") else ""
            lines.append(f"• {ev.get('date')} {ev.get('time')}: {ev.get('title')}{loc_str} (ID: {ev.get('id')})")

        return "\n".join(lines)

    elif action in ("check_day", "today", "tomorrow"):
        target_date = date_str
        day_events = [e for e in events if e.get("date") == target_date]

        if not day_events:
            return f"No events scheduled for {target_date}."

        lines = [f"📅 Schedule for {target_date}:"]
        for ev in day_events:
            loc_str = f" [{ev['location']}]" if ev.get("location") else ""
            lines.append(f"• {ev.get('time')} - {ev.get('title')}{loc_str}")

        return "\n".join(lines)

    elif action in ("delete", "delete_event", "remove", "cancel"):
        if not event_id and not title:
            return "Please specify the event title or ID to delete."

        orig_count = len(events)
        if event_id:
            events = [e for e in events if e.get("id") != event_id]
        elif title:
            events = [e for e in events if title.lower() not in e.get("title", "").lower()]

        if len(events) < orig_count:
            _save_events(events)
            return "Event removed from calendar."
        else:
            return "Could not find a matching event to remove."

    elif action in ("export_ics", "export"):
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Brahma AI//Calendar Scheduler//EN",
        ]
        for ev in events:
            try:
                dt_start = datetime.strptime(f"{ev['date']} {ev['time']}", "%Y-%m-%d %H:%M")
                dt_end = dt_start + timedelta(minutes=ev.get("duration_minutes", 30))
                ics_lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:{ev.get('id', uuid.uuid4())}@brahma.ai",
                    f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTSTART:{dt_start.strftime('%Y%m%dT%H%M%S')}",
                    f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%S')}",
                    f"SUMMARY:{ev.get('title')}",
                    f"DESCRIPTION:{ev.get('description', '')}",
                    f"LOCATION:{ev.get('location', '')}",
                    "END:VEVENT",
                ])
            except Exception:
                continue
        ics_lines.append("END:VCALENDAR")

        desktop_ics = Path.home() / "Desktop" / "brahma_calendar.ics"
        desktop_ics.write_text("\n".join(ics_lines), encoding="utf-8")
        return f"Exported calendar events to {desktop_ics}"

    return f"Unknown calendar action: '{action}'."


def run(parameters: dict, player=None, session_memory=None) -> str:
    """Plugin wrapper for Mark-LI architecture."""
    return calendar_scheduler(parameters, player=player, session_memory=session_memory)
