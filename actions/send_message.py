# actions/send_message.py
# Universal messaging — WhatsApp & Instagram
# Uses lightweight pyautogui browser automation.

from __future__ import annotations

import time
from pathlib import Path

import pyautogui
import pyperclip

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.08

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _normalize_path(value: str) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _open_app(app_name: str) -> bool:
    """Opens an app via Windows search."""
    try:
        pyautogui.press("win")
        time.sleep(0.4)
        pyautogui.write(app_name, interval=0.04)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(2.0)
        return True
    except Exception as e:
        print(f"[SendMessage] Could not open {app_name}: {e}")
        return False


def _send_whatsapp(receiver: str, message: str) -> str:
    try:
        if not _open_app("WhatsApp"):
            return "Could not open WhatsApp."

        time.sleep(1.5)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.4)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write(receiver, interval=0.04)
        time.sleep(1.0)
        pyautogui.press("enter")
        time.sleep(0.8)
        pyautogui.write(message, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Message sent to {receiver} via WhatsApp."
    except Exception as e:
        return f"WhatsApp error: {e}"


def _open_instagram_home() -> None:
    import webbrowser

    webbrowser.open("https://www.instagram.com/")
    time.sleep(6.0)


def _open_instagram_post_dialog() -> None:
    """
    Open Instagram's create dialog directly so the upload flow starts on
    Create / Post instead of landing on the feed or another sidebar item.
    """
    import webbrowser

    webbrowser.open("https://www.instagram.com/create/select/")
    time.sleep(6.0)

    # Instagram usually shows a modal with "Select from computer".
    # Give it a few chances to focus that action without using the left nav.
    for _ in range(5):
        pyautogui.press("tab")
        time.sleep(0.15)
    pyautogui.press("enter")
    time.sleep(2.5)


def _send_instagram(receiver: str, message: str) -> str:
    """
    Sends an Instagram DM via browser (instagram.com).
    """
    try:
        _open_instagram_home()
        pyautogui.write(receiver, interval=0.05)
        time.sleep(1.5)

        pyautogui.press("down")
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(0.5)

        for _ in range(3):
            pyautogui.press("tab")
            time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(1.5)

        pyautogui.write(message, interval=0.04)
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Message sent to {receiver} via Instagram."
    except Exception as e:
        return f"Instagram error: {e}"


def _upload_instagram_media(media_path: str, caption: str = "", mode: str = "post") -> str:
    """
    Upload a photo/video to Instagram using the normal web UI flow.
    """
    try:
        path = _normalize_path(media_path)
        if not path or not path.exists():
            return f"Instagram upload error: media file not found: {media_path}"

        if path.suffix.lower() not in VIDEO_EXTS | IMAGE_EXTS:
            return f"Instagram upload error: unsupported media type: {path.suffix}"

        _open_instagram_post_dialog()

        # In the file chooser, paste the full file path.
        try:
            pyperclip.copy(str(path))
            time.sleep(0.2)
            pyautogui.hotkey("ctrl", "v")
        except Exception:
            pyautogui.write(str(path), interval=0.02)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(4.0)

        # If caption is requested, attempt to place it into the caption box.
        if caption:
            try:
                pyautogui.write(caption, interval=0.03)
                time.sleep(0.2)
            except Exception:
                pass

        # Advance through the common Instagram flow to the share step.
        for _ in range(4):
            pyautogui.press("tab")
            time.sleep(0.12)
        pyautogui.press("enter")
        time.sleep(2.0)

        return f"Instagram {mode} uploaded: {path.name}"
    except Exception as e:
        return f"Instagram upload error: {e}"


def _send_telegram(receiver: str, message: str) -> str:
    """Sends a Telegram message via Windows desktop app."""
    try:
        if not _open_app("Telegram"):
            return "Could not open Telegram."

        time.sleep(1.5)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.4)
        pyautogui.write(receiver, interval=0.04)
        time.sleep(1.0)
        pyautogui.press("enter")
        time.sleep(0.8)
        pyautogui.write(message, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Message sent to {receiver} via Telegram."
    except Exception as e:
        return f"Telegram error: {e}"


def _send_email_via_browser(platform: str, receiver: str, message: str) -> str:
    try:
        import urllib.parse
        import webbrowser
        import psutil
        import time
        import pyautogui
        
        # Check if Chrome or Edge is running
        browser_name = "browser"
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"].lower()
                if "chrome" in name:
                    browser_name = "Chrome"
                    break
                elif "msedge" in name:
                    browser_name = "Edge"
                    break
                elif "firefox" in name:
                    browser_name = "Firefox"
                    break
            except Exception:
                continue

        subject = "Message from Brahma Echo"
        
        plat_lower = platform.lower()
        if "gmail" in plat_lower or "chrome" in plat_lower or "browser" in plat_lower:
            quoted_recipient = urllib.parse.quote(receiver)
            quoted_subject = urllib.parse.quote(subject)
            quoted_body = urllib.parse.quote(message)
            url = f"https://mail.google.com/mail/?view=cm&fs=1&to={quoted_recipient}&su={quoted_subject}&body={quoted_body}"
            app_name = f"Gmail in {browser_name}"
            
            print(f"[SendMessage] Automating Chrome to open: {url}")
            webbrowser.open(url)
            
        elif "outlook" in plat_lower:
            quoted_recipient = urllib.parse.quote(receiver)
            quoted_subject = urllib.parse.quote(subject)
            quoted_body = urllib.parse.quote(message)
            url = f"https://outlook.live.com/default/?path=/mail/action/compose&to={quoted_recipient}&subject={quoted_subject}&body={quoted_body}"
            app_name = f"Outlook in {browser_name}"
            webbrowser.open(url)
        else:
            quoted_recipient = urllib.parse.quote(receiver)
            quoted_subject = urllib.parse.quote(subject)
            quoted_body = urllib.parse.quote(message)
            url = f"mailto:{quoted_recipient}?subject={quoted_subject}&body={quoted_body}"
            app_name = "Default Mail Client"
            webbrowser.open(url)
            
        return f"Opened {app_name} to compose email to {receiver}."
    except Exception as e:
        return f"Email browser compose error: {e}"


def _send_generic(platform: str, receiver: str, message: str) -> str:
    try:
        if not _open_app(platform):
            return f"Could not open {platform}."

        time.sleep(1.5)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.4)
        pyautogui.write(receiver, interval=0.04)
        time.sleep(1.0)
        pyautogui.press("enter")
        time.sleep(0.8)
        pyautogui.write(message, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Message sent to {receiver} via {platform}."
    except Exception as e:
        return f"{platform} error: {e}"


def send_message(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None
) -> str:
    """
    Called from main.py.

    parameters:
        receiver     : Contact name to send to
        message_text : The message content / caption
        platform     : whatsapp | instagram | telegram | <any app name>
                       Default: whatsapp
        mode         : dm | upload (instagram only; default: dm)
        media_path   : Optional media file path for Instagram uploads
    """
    params       = parameters or {}
    receiver     = params.get("receiver", "").strip()
    message_text = params.get("message_text", "").strip()
    platform     = params.get("platform", "whatsapp").strip().lower()
    mode         = params.get("mode", "dm").strip().lower()
    media_path   = params.get("media_path", "").strip()

    if mode != "upload" and not receiver:
        return "Please specify who to send the message to, sir."
    if mode != "upload" and not message_text:
        return "Please specify what message to send, sir."
    if mode == "upload" and not media_path:
        return "Please specify a media file to upload, sir."

    print(f"[SendMessage] 📨 {platform} → {receiver}: {message_text[:40]}")
    if player:
        if mode == "upload" and "instagram" in platform:
            player.write_log(f"[msg] Uploading {media_path} to Instagram...")
        else:
            player.write_log(f"[msg] Sending to {receiver} via {platform}...")

    if "instagram" in platform and mode == "upload":
        result = _upload_instagram_media(media_path, caption=message_text, mode="post")
    elif "gmail" in platform or "outlook" in platform or platform in ("email", "mail"):
        result = _send_email_via_browser(platform, receiver, message_text)
    elif "whatsapp" in platform or "wp" in platform or "wapp" in platform:
        result = _send_whatsapp(receiver, message_text)
    elif "instagram" in platform or "ig" in platform or "insta" in platform:
        result = _send_instagram(receiver, message_text)
    elif "telegram" in platform or "tg" in platform:
        result = _send_telegram(receiver, message_text)
    else:
        result = _send_generic(platform, receiver, message_text)

    print(f"[SendMessage] ✅ {result}")
    if player:
        player.write_log(f"[msg] {result}")

    return result
