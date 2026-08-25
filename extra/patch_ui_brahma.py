import sys
from pathlib import Path

path = Path("ui.py")
content = path.read_text(encoding="utf-8")

# Replace standard literal strings
replacements = {
    '"Try asking Brahma Echo"': 'f"Try asking {identity.get_assistant_name()}"',
    '"Brahma Echo Home"': 'f"{identity.get_application_name()} Home"',
    '"Brahma Echo is listening..."': 'f"{identity.get_assistant_name()} is listening..."',
    '"Restart Brahma Echo"': 'f"Restart {identity.get_application_name()}"',
    '"Quit Brahma Echo"': 'f"Quit {identity.get_application_name()}"',
    '"Hide Brahma Echo icon?"': 'f"Hide {identity.get_application_name()} icon?"',
    '"Launch Brahma Echo →"': 'f"Launch {identity.get_application_name()} →"',
    '"Tell Brahma Echo what to do..."': 'f"Tell {identity.get_assistant_name()} what to do..."',
    '"Ask Brahma Echo anything..."': 'f"Ask {identity.get_assistant_name()} anything..."',
    '"Open Brahma Echo Home"': 'f"Open {identity.get_application_name()} Home"',
    'self.setWindowTitle("Brahma Echo")': 'self.setWindowTitle(identity.get_application_name())',
    'self._app.setApplicationDisplayName("Brahma Echo")': 'self._app.setApplicationDisplayName(identity.get_application_name())',
    'self._tray.setToolTip("Brahma Echo")': 'self._tray.setToolTip(identity.get_application_name())',
    'self._task_card.set_task("Working on it...", "Brahma Echo is processing your request.", 72)': 'self._task_card.set_task("Working on it...", f"{identity.get_assistant_name()} is processing your request.", 72)',
    'self._task_card.set_task("Responding...", "Brahma Echo is speaking now.", 100)': 'self._task_card.set_task("Responding...", f"{identity.get_assistant_name()} is speaking now.", 100)',
    'self._task_card.set_task("Ready", "Brahma Echo is idle and ready.", 0)': 'self._task_card.set_task("Ready", f"{identity.get_assistant_name()} is idle and ready.", 0)',
}

for k, v in replacements.items():
    content = content.replace(k, v)

# For "Brahma Echo: " string slicing
content = content.replace('raw[len("Brahma Echo:"):].strip()', 'raw[len(f"{identity.get_assistant_name()}:"):].strip()')

path.write_text(content, encoding="utf-8")
print("ui.py patched for hardcoded strings")
