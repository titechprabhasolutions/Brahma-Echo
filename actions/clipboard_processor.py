# actions/clipboard_processor.py
"""
Clipboard Processor Action for Brahma AI.

Allows the AI to instantly read whatever text the user has copied to their Windows clipboard.
"""

import pyperclip

def process_clipboard(parameters: dict | None = None, player=None) -> str:
    """Reads the current text from the clipboard."""
    try:
        content = pyperclip.paste()
        content = (content or "").strip()
        
        if not content:
            return "The clipboard is empty or does not contain text."
            
        if player:
            player.write_log("SYS: Read clipboard contents.")
            
        # Truncate if insanely large to prevent breaking the session context
        if len(content) > 30000:
            content = content[:30000] + "\n...[Truncated for length]"
            
        return f"Clipboard Contents:\n\n{content}"
    except Exception as e:
        return f"Failed to read clipboard: {e}"

def run(parameters: dict, player=None, session_memory=None) -> str:
    return process_clipboard(parameters, player=player)
