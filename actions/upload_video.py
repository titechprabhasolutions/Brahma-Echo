#upload_video.py
"""
Hardcoded automation: uploads the video sitting on the Desktop (named 'video')
to TikTok Studio, using a fixed, always-identical sequence of steps — same
order, every single time, no improvisation.

The user gives only a rough caption BRIEF ("write that I made a plugin system
in the new version") — this plugin expands it with Gemini into a full,
SEO-keyword-rich TikTok caption in the user's own language before the
automation starts, so no Gemini latency lands in the middle of the click
sequence.

Opera GX is launched the normal way (Win key, type, Enter) — exactly like a
human opening it — so it comes up as the user's real, already-logged-in
browser instead of a separate automated instance with a blank profile.

Flow (fixed): Opera GX → new tab → tiktok.com/tiktokstudio/upload → click
screen center → Tab → Enter (file picker opens) → Ctrl+F → type 'video' →
open the found file → Tab → Ctrl+A → paste caption → 16×Tab → Enter. Done.

pyautogui.FAILSAFE stays on: slamming the mouse into the top-left corner
aborts the automation instantly.
"""
import json
import sys
import threading
import time
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = 0.05
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False


PLUGIN = {
    "name": "upload_video",
    "description": (
        "Uploads the video file named 'video' on the user's Desktop to TIKTOK "
        "with a fully automated browser flow (Opera GX + TikTok Studio). Use "
        "when the user asks to upload/post/share their video to TikTok — e.g. "
        "'upload this video to TikTok', 'videoyu tiktok'a yükle'. "
        "CAPTION RULE — STRICT: 'description' must contain the user's OWN "
        "caption idea, passed VERBATIM in their language. NEVER invent, "
        "guess, or auto-fill it yourself. If the user's request contains no "
        "caption topic, DO NOT call this tool yet — first ASK the user what "
        "the caption should be about, and call only after they answer. The "
        "single exception: if the user explicitly delegates it ('sen yaz', "
        "'default olsun', 'you decide'), you may then pass your own brief. "
        "The tool itself expands the brief into a full SEO caption — do NOT "
        "expand it yourself. Call this tool EXACTLY ONCE per request. "
        "The tool returns IMMEDIATELY while the upload keeps running in the "
        "background — when the result arrives, announce the start exactly as "
        "it instructs (uploading now + hands off mouse/keyboard), then wait: "
        "progress remarks and the completion announcement arrive by "
        "themselves. Do NOT call the tool again to check status. Never use "
        "browser_control or computer_control for TikTok uploads."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "description": {
                "type": "STRING",
                "description": ("The user's rough caption brief, verbatim, in "
                                "their own language."),
            }
        },
        "required": ["description"],
    },
}

_POST_COOLDOWN_SEC = 20.0  # ignore repeat calls for this long after a successful post
_last_post_at      = 0.0
_upload_running    = False  # a background upload is in progress right now


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR        = _get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _require_pyautogui() -> None:
    if not _PYAUTOGUI:
        raise RuntimeError("PyAutoGUI not installed. Run: pip install pyautogui")


def _paste(text: str) -> None:
    """Types text via clipboard paste so non-ASCII characters and emoji survive."""
    _require_pyautogui()
    if _PYPERCLIP:
        pyperclip.copy(text)
        time.sleep(0.15)
        pyautogui.hotkey("ctrl", "v")
    else:
        pyautogui.typewrite(text, interval=0.02)
    time.sleep(0.2)


def _generate_caption(brief: str) -> str:
    """Expands the user's rough brief into a LONG, SEO-heavy TikTok caption
    with Gemini, in the same language as the brief, keyword-targeted at
    Tier-1 audiences (US/UK/CA/AU/DE...). Falls back to the brief itself if
    the call fails — the upload must never be blocked by a caption error."""
    try:
        from google import genai
        client = genai.Client(api_key=_get_api_key())
        prompt = (
            "You are a TikTok SEO copywriter. The user gives you only a rough "
            "TITLE/BRIEF; you turn it into ONE ready-to-post, LONG caption in "
            "the SAME language as the brief:\n"
            f'BRIEF: "{brief}"\n'
            "Rules:\n"
            "- LONG and substantial: at least 1000 characters of body text "
            "(not counting hashtags). Expand the brief into a detailed, "
            "engaging story/description — this is for search ranking, not a "
            "one-liner.\n"
            "- Strong scroll-stopping hook as the first line.\n"
            "- Weave in plenty of high-search-volume SEO keywords and phrases "
            "naturally throughout the body, chosen to rank with TIER-1 "
            "audiences (US, UK, Canada, Australia, Germany...). Keywords may "
            "be in English even if the body language differs.\n"
            "- End with a call-to-action (follow/comment/share), then 15-25 "
            "hashtags: mix broad high-volume Tier-1 English hashtags with "
            "niche topic hashtags.\n"
            "- Plain text only — no quotes, no markdown, no explanations.\n"
            "- Maximum 3500 characters total."
        )
        r = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
        caption = (r.text or "").strip()
        return caption[:3900] if caption else brief
    except Exception as e:
        print(f"[UploadVideo] Caption generation failed, using brief as-is: {e}")
        return brief


def _run_upload_flow(brief: str, caption_holder: dict,
                     caption_ready: threading.Event) -> str:
    _require_pyautogui()
    w, h = pyautogui.size()

    # Open Opera GX exactly like a human would (Win key -> type -> Enter)
    pyautogui.press("win")
    time.sleep(0.7)
    pyautogui.write("opera gx", interval=0.05)
    time.sleep(0.9)
    pyautogui.press("enter")
    time.sleep(3.0)  # give Opera GX time to come to the foreground

    # New tab -> TikTok Studio upload page
    pyautogui.hotkey("ctrl", "t")
    time.sleep(0.6)
    _paste("https://www.tiktok.com/tiktokstudio/upload")
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(5.0)  # page load

    # Click dead center of the screen (upload dropzone area), then Tab + Enter
    # to activate the 'Select video' control -> native file picker opens
    pyautogui.click(w // 2, h // 2)
    time.sleep(0.8)
    pyautogui.press("tab")
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(2.0)

    # Ctrl+F is a fixed OS-level shortcut that always opens the Open dialog's
    # search box regardless of screen/resolution -- no lookup needed.
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.6)
    pyautogui.write("video", interval=0.03)
    time.sleep(1.5)  # let Explorer filter the results down to the matching file

    # Open the found file. 180x120 on the reference 1920x1080 layout, scaled
    # to the actual resolution. Double-click = select + open in one motion
    # (same proven pattern as the old Instagram flow's file pick).
    pyautogui.doubleClick(int(w * 240 / 1920), int(h * 135 / 1080))
    time.sleep(4.0)  # TikTok starts processing the upload; caption box appears

    # Caption: Tab once into the field, select the auto-filled text, replace it.
    # The SEO caption has been generating in a background thread since the very
    # first keystroke — by now (~20s in) it's almost always ready; wait max 15s
    # more, then fall back to the raw brief so the flow never stalls.
    caption_ready.wait(timeout=15)
    caption = (caption_holder.get("caption") or brief).strip()
    pyautogui.press("tab")
    pyautogui.press("tab")
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.3)
    _paste(caption)
    time.sleep(3)

    # 16 Tabs down to the Post button, Enter -> published
    time.sleep(6)
    for _ in range(17):
        pyautogui.press("tab")
        time.sleep(0.12)
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(1)
    pyautogui.click(int(w * 1089 / 1920), int(h * 653 / 1080))
    pyautogui.click(int(w * 1200 / 1920), int(h * 655 / 1080))

    return "OK"


def run(parameters: dict, player=None, session_memory=None) -> str:
    global _last_post_at, _upload_running

    if _upload_running:
        return ("The upload is STILL RUNNING right now — this call was "
                "ignored. Do not call the tool again; briefly tell the user, "
                "in their language, that it is still in progress.")

    since_last = time.monotonic() - _last_post_at
    if since_last < _POST_COOLDOWN_SEC:
        print(f"[UploadVideo] Ignoring duplicate call ({since_last:.0f}s after last post)")
        return ("The video was ALREADY posted successfully — this duplicate "
                "call was ignored. Do not repeat any status message. Simply "
                "confirm ONCE, in the user's language and in past tense, that "
                "the video is posted (e.g. 'I posted the video, sir — you're "
                "welcome.').")

    brief = ((parameters or {}).get("description") or "").strip()
    print(f"[UploadVideo] brief={'<empty>' if not brief else brief[:40]!r}")
    if not brief:
        return ("I need a caption idea before I share the video, sir. What "
                "should it be about, or shall I write one myself?")

    # Kick off SEO caption generation in the BACKGROUND — the click sequence
    # starts immediately (within ~1s); the caption is only needed ~20s later
    # at the paste step, by which time it's ready.
    caption_holder: dict = {}
    caption_ready = threading.Event()

    def _gen():
        try:
            caption_holder["caption"] = _generate_caption(brief)
        finally:
            caption_ready.set()

    threading.Thread(target=_gen, daemon=True, name="tiktok-caption").start()

    def _log(msg: str) -> None:
        if player:
            try:
                player.write_log(msg)
            except Exception:
                pass

    _log("JARVIS: TikTok upload starting — please don't touch the mouse "
         "or keyboard.")

    say = getattr(player, "request_say", None) if player else None

    # ── No speech channel (older core): fall back to the blocking flow ──────
    if not say:
        try:
            result = _run_upload_flow(brief, caption_holder, caption_ready)
        except Exception as e:
            print(f"[UploadVideo] Error: {e}")
            return f"An error occurred while sharing the video, sir: {e}"
        if result != "OK":
            return result
        _last_post_at = time.monotonic()
        return ("The video has been posted to TikTok successfully — announce "
                "it in the user's language, in PAST tense, warm and brief. "
                "Do NOT call upload_video again.")

    # ── Two-phase mode (same trick as instant vision acknowledgment): the
    #    tool returns IMMEDIATELY so Gemini can speak right away; the actual
    #    automation, the mid-upload small talk and the completion announcement
    #    all run in background threads through the plugin speech channel. ────
    stop_chatter = threading.Event()

    def _chatter():
        remarks = [
            ("[UPLOAD STATUS — speak now] The TikTok upload is underway in "
             "the background. Make ONE warm, personal small-talk remark to "
             "the user in their language — for example, kindly remind them "
             "not to spend too much time on social media and to keep some "
             "time for themselves, or a similar caring thought. One or two "
             "sentences, natural tone, do not mention tools or steps."),
            ("[UPLOAD STATUS — speak now] Still uploading, almost done. Make "
             "ONE more brief, warm remark to the user in their language — a "
             "different caring or encouraging thought than before, never "
             "repeat earlier phrasing. One sentence, do not mention tools "
             "or steps."),
        ]
        for delay, remark in zip((10.0, 12.0), remarks):
            if stop_chatter.wait(delay):
                return
            try:
                say(remark)
            except Exception:
                return

    def _worker():
        global _last_post_at, _upload_running
        try:
            result = _run_upload_flow(brief, caption_holder, caption_ready)
            stop_chatter.set()
            if result == "OK":
                _last_post_at = time.monotonic()
                posted = (caption_holder.get("caption") or brief)[:60]
                _log(f"[UploadVideo] Posted to TikTok: \"{posted}...\"")
                say("[UPLOAD FINISHED — speak now] The video has just been "
                    "posted to TikTok successfully. Announce it to the user "
                    "in their language, PAST tense, warm and brief — e.g. "
                    "'I posted the video, sir — you're welcome.'")
            else:
                say(f"[UPLOAD PROBLEM — speak now] The upload could not be "
                    f"completed: {result}. Tell the user in their language, "
                    "briefly.")
        except Exception as e:
            print(f"[UploadVideo] Error: {e}")
            stop_chatter.set()
            say(f"[UPLOAD FAILED — speak now] The TikTok upload failed: {e}. "
                "Briefly apologize and tell the user in their language.")
        finally:
            stop_chatter.set()
            _upload_running = False

    _upload_running = True
    threading.Thread(target=_worker, daemon=True, name="tiktok-upload").start()
    threading.Thread(target=_chatter, daemon=True, name="tiktok-chatter").start()