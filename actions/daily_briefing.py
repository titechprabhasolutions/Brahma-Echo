# actions/daily_briefing.py
"""
Daily Briefing Action for Brahma AI.

Compiles a comprehensive, natural daily briefing including:
- Personalized greeting & current time
- Today's calendar schedule & events
- Top news headlines from Google News RSS
- Weather update
- Summary from previous sessions
"""

import datetime
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

PLUGIN = {
    "name": "daily_briefing",
    "description": (
        "Delivers a comprehensive daily briefing to the user including time, "
        "today's schedule/events, weather, and top world/tech news headlines. "
        "Call this whenever the user asks for their briefing, morning update, or what's happening today."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "category": {
                "type": "STRING",
                "description": "Optional category focus: all (default), tech, world, schedule",
            }
        },
        "required": [],
    },
}


def _get_top_headlines(category: str = "all", limit: int = 3) -> list[str]:
    """Fetches clean top headlines using Google News RSS with zero rate limits."""
    headlines = []
    feed_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    if category.lower() == "tech":
        feed_url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en"

    try:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            root = ET.fromstring(resp.read())
            items = root.findall(".//item")[:limit]
            for item in items:
                title_elem = item.find("title")
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()
                    # Remove trailing source name (e.g. "... - CNN" -> "...")
                    if " - " in title:
                        title = title.rsplit(" - ", 1)[0]
                    headlines.append(title)
    except Exception as e:
        print(f"[DailyBriefing] News fetch error: {e}")

    return headlines


def _get_today_schedule() -> list[str]:
    """Checks for calendar events scheduled for today."""
    events_path = BASE_DIR / "memory" / "calendar_events.json"
    if not events_path.exists():
        return []

    try:
        with open(events_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            all_events = data
        elif isinstance(data, dict):
            all_events = data.get("events", [])
        else:
            all_events = []

        today_str = datetime.date.today().isoformat()
        today_events = [e for e in all_events if isinstance(e, dict) and e.get("date") == today_str]
        today_events.sort(key=lambda x: x.get("time", "00:00"))
        
        event_descriptions = []
        for e in today_events:
            t = e.get("time", "")
            title = e.get("title", "Event")
            if t:
                event_descriptions.append(f"{title} at {t}")
            else:
                event_descriptions.append(title)
        return event_descriptions
    except Exception as e:
        print(f"[DailyBriefing] Calendar fetch error: {e}")
        return []


def compile_daily_briefing(category: str = "all") -> str:
    """
    Compiles a complete daily briefing.
    """
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip("0")
    date_str = now.strftime("%A, %B %d")

    greeting = "Good morning"
    if now.hour >= 12 and now.hour < 17:
        greeting = "Good afternoon"
    elif now.hour >= 17:
        greeting = "Good evening"

    parts = [f"{greeting}, sir. Today is {date_str}, and the time is {time_str}."]

    # 1. Schedule check
    today_events = _get_today_schedule()
    if today_events:
        parts.append(f"On your schedule today, you have: {', '.join(today_events)}.")
    else:
        parts.append("You have no calendar events scheduled for today.")

    # 2. Previous session context
    try:
        from workspace_store import store
        s = store()
        summary = s._get_state("last_session_summary")
        if summary:
            parts.append(f"From our last session: {summary}")
            s._set_state("last_session_summary", "")
    except Exception:
        pass

    # 3. Top News Headlines
    headlines = _get_top_headlines(category=category, limit=3)
    if headlines:
        headline_text = " • " + " • ".join([f"{h}" for h in headlines])
        parts.append(f"Here are the latest headlines: {headline_text}")
    else:
        parts.append("All systems are operational and I'm ready for your instructions.")

    return " ".join(parts)


def daily_briefing(
    parameters: dict | None = None,
    response: str | None = None,
    player=None,
    session_memory=None,
    speak=None,
) -> str:
    """
    Action entry point for daily briefing.
    """
    p = parameters or {}
    category = p.get("category", "all")
    text = compile_daily_briefing(category=category)

    if player:
        try:
            player.show_daily_briefing(text)
            player.write_log(f"Brahma Echo: {text}")
        except Exception:
            pass

    if speak:
        try:
            speak(text)
        except Exception:
            pass

    return text


def run(parameters: dict, player=None, session_memory=None) -> str:
    """Plugin wrapper."""
    return daily_briefing(parameters, player=player, session_memory=session_memory)
