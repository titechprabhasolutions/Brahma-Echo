<div align="center">
  <img src="assets/Brahma_Lite_Logo.png" alt="Brahma Echo" width="260" />

  <h1>Brahma Echo</h1>

  <p><strong>Open-source Windows desktop AI assistant</strong></p>
  <p>Voice-first automation · contextual desktop intelligence · productivity workflows</p>

  <p>
    <a href="#overview"><img src="https://img.shields.io/badge/experience-open%20source-blue?style=for-the-badge" alt="Open Source" /></a>
    <a href="#getting-started"><img src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey?style=for-the-badge" alt="Windows" /></a>
    <a href="#features"><img src="https://img.shields.io/badge/tech-Gemini%20%2B%20OpenRouter-green?style=for-the-badge" alt="Gemini + OpenRouter" /></a>
  </p>

  <p>
    <a href="#quick-start"><img src="https://img.shields.io/badge/Quick%20Start-Install%20%26%20Run-success?style=flat-square" alt="Quick Start" /></a>
    <a href="#project-structure"><img src="https://img.shields.io/badge/Project%20Structure-Clean%20Architecture-lightgrey?style=flat-square" alt="Project Structure" /></a>
    <a href="#community"><img src="https://img.shields.io/badge/Community-Discord-purple?style=flat-square" alt="Community" /></a>
  </p>
</div>

---

## Overview

Brahma Echo is a premium Windows desktop assistant that combines voice and text control with automated workflows, screen-aware intelligence, and rich content generation.

Designed for advanced desktop productivity, Brahma Echo delivers:

- Voice-first command and desktop automation
- Application control, browser workflows, and file handling
- Contextual screen inspection and adaptive task execution
- Presentation, document, and report generation
- Remote control via Discord and Brahma Connect

## Quick Highlights

| Core capability | Why it matters |
|---|---|
| Voice-first assistant | Speak commands naturally and stay hands-free |
| Gemini + OpenRouter | Fast responses with resilient fallback support |
| Autonomous Self-Patching | Self-repairs codebase exceptions safely via AST sandbox with zero-brick Boot Sentry |
| Continuous Self-Improvement | Learns user habits, preferences, and directives dynamically into prompts |
| Local OS Diagnostics MCP | 0 background API credits: monitor CPU/RAM hogs, battery health, display brightness |
| Google Workspace MCP | Native Gmail, Google Calendar meetings, and Google Drive management |
| Desktop Organizer MCP | Categorizes desktop clutter automatically with instant rollback |
| Full Browser MCP (@playwright/mcp) | 24+ automated actions: navigate, form-fill, click, snapshot, screenshot, and JS evaluate |
| Screen-aware context | Ask about visible windows and on-screen content |
| Document automation | Create presentations, docs, spreadsheets, and PDFs |
| Plugin-ready | Extend features with lightweight Python plugins |

## Key Benefits

- Wake-word support for “Brahma Echo” and responsive assistant activation
- Gemini 2.5 Flash-powered AI with OpenRouter fallback resilience
- **Zero-Brick Autonomous Self-Patching**: In-memory AST sandbox with automatic `boot_sentry` recovery
- **Continuous Learning Engine**: Permanent memory for user preferences and custom behaviors without code edits
- **Local OS Hardware & System Diagnostics**: 100% offline, zero background credits
- Polished Qt interface with live status displays, hardware telemetry, and self-healing controls
- Modular action architecture for clean extensibility and automation
- Secure local configuration with file-based credential storage
- Device pairing and remote routing through Brahma Connect

## Features & Complete Action Capabilities

### 🧠 The 5 Pillars of Sentient AI
- **Conversational Realism**: Barge-in (<50ms local VAD) for instant interruption, natural Conversational Fillers, and native Hinglish fluency.
- **Ambient & Proactive Intelligence**: Foreground Window Context awareness, background Battery & Posture Alerts, and an intelligent Clipboard Sentry.
- **Kinetic & Visual Realism**: 3D Cursor Gaze tracking, deep Audio Reactivity, physics-based Spring Edge Snapping, and spatial Acoustic Cues built into the FloatingLauncher.
- **Live Thinking Out Loud**: Real-time action breadcrumbs and vocalized thoughts during complex multi-step execution.
- **Deep Adaptive Living Knowledge Graph**: Zero-latency heuristic auto-learning that silently extracts identity, location, email, active project paths, technical stacks, and user preferences into a persistent long-term memory graph.

### 🛡️ Autonomous Self-Healing & Continuous Self-Improvement
- **Autonomous Error Localization**: Real-time traceback analysis (`actions/auto_heal_engine.py`) that isolates failing lines in first-party code while strictly protecting core immune files.
- **AST Safety Sandbox**: Candidate hotfixes are compiled in memory using Python's Abstract Syntax Tree (`ast.parse()`) and `py_compile` before touching disk.
- **Native Google Gemini Synthesis**: Surgical hotfix generation using Gemini 2.5/2.0-Flash to fix edge cases, `KeyError`, `NoneType`, and boundary errors.
- **Boot Sentry (Anti-Bricking Guarantee)**: Runs at startup before the UI or Gemini loads (`core/boot_sentry.py`). If a recent patch caused a startup crash, it automatically rolls back from `.bak` backup.
- **One-Click & Voice Rollback**: Revert any patch instantly via *"Brahma, undo last patch"* or the UI settings card.
- **Continuous Behavioral Learning**: Permanent rule storage (`config/learned_rules.json`) dynamically injected into `_load_system_prompt()` via `core/learned_rules.py` to personalize Brahma's behavior without modifying source code.
- **Live Test Sandbox**: Includes `actions/test_action.py` and `test_self_heal.py` to test the complete self-repair and rollback lifecycle safely.

### 🖥️ Local OS Hardware & System Diagnostics MCP (0 Background Credits)
- **Real-Time Vitals**: Instant CPU usage, thermals, storage space, and battery health/percentage (`actions/system_diagnostics_mcp.py`).
- **Process & RAM Hog Scanner**: Scan and pinpoint memory/CPU-heavy applications (*"Who is eating my RAM?"*).
- **Process Manager**: Safely terminate or force-kill frozen processes on demand (*"Kill chrome"*).
- **Multi-Monitor Brightness**: Seamless hardware display brightness control via slider or voice (*"Dim monitor 2"*, *"Brightness 80%"*).

### 📁 Smart Desktop Organizer & File Operations
- **Smart Desktop Organizer MCP**: Classifies cluttered desktop files into categorized folders (Documents, Images, Media, Archives, Installers, Code) with safety rollback (`actions/desktop_organizer_mcp.py`).
- **Deep File Controller**: Find files by name, extension, or recency, open files in default applications, move, copy, rename, and delete files (`actions/file_controller.py`).
- **Deep File Processor**: Extract and inspect content from plain text, CSV, JSON, source code, DOCX, PDF, and image OCR (`actions/file_processor.py`).

### 🌐 Google Workspace MCP (Gmail, Calendar, Drive)
- **Gmail Integration**: Read unread emails, search inbox, and send emails directly through voice or chat (`actions/google_workspace_mcp.py`).
- **Google Calendar**: Schedule meetings, check daily agenda, and get reminders.
- **Google Drive**: Search documents, read remote files, and upload local deliverables.

### 🌐 Full Browser Automation MCP (@playwright/mcp)
- **Official Model Context Protocol Integration**: Directly interfaces with Microsoft's `@playwright/mcp` server over stdio JSON-RPC 2.0 (`actions/playwright_mcp_client.py`, `actions/browser_control.py`).
- **24+ High-Level Browser Actions**: Full automation lifecycle including `browser_navigate`, `browser_click`, `browser_type`, `browser_fill_form`, `browser_snapshot`, `browser_screenshot`, `browser_evaluate`, and `browser_tabs`.
- **Accessibility Tree Navigation**: Extracts structural accessibility trees instead of fragile pixel coordinates for robust, resilient interaction across dynamic web apps.
- **Persistent Profile & Authentication**: Automatically manages session storage in `LOCALAPPDATA/BrahmaAI/PlaywrightProfile`, enabling persistent logins and headless/headed modes.

### 📱 Brahma Connect & Android Remote Autopilot
- **Local Network Pairing & Discovery**: Connects Android companion devices securely over local Wi-Fi with cryptographic pairing tokens (`actions/brahma_connect.py`).
- **Device Telemetry & Controls**: Query phone battery status, trigger flashlight, adjust media/call volume, fetch Wi-Fi state, and launch phone apps.
- **Mobile Autopilot**: Remote device control using Android's native Accessibility Service to click, scroll, type, and automate actions on mobile (`actions/mobile_autopilot.py`).
- **Clipboard & Notification Sync**: Seamlessly sync copied text and alerts between Windows and your phone.

### 📸 Vision, Screen & Attention Intelligence
- **Dynamic Screen Processor**: Real-time screenshot capture, visual question answering, active window understanding, and OCR (`actions/screen_processor.py`).
- **Focus & Attention Monitor**: Camera-based focus tracker that monitors user gaze, eye contact, drowsiness, and posture with automated break alerts (`actions/attention_monitor.py`).
- **Offline Face Detection**: Fast, zero-credit face landmark and presence verification powered by Haar cascades (`core/haarcascade_frontalface_default.xml`).

### 🏋️ AI Fitness, Workout & Nutrition Tracker
- **Computer-Vision Pushup Counter**: Live webcam rep counter with form detection, rep feedback, and workout session logging (`actions/pushup_counter.py`).
- **Intelligent Calorie & Nutrition Counter**: Log meals, calculate daily caloric budgets, track macronutrients (proteins, carbs, fats), and estimate calories from food descriptions or images (`actions/calorie_counter.py`).

### 📊 Office, Presentations & Document Engineering
- **Automated Presentation Builder**: Generates multi-slide PowerPoint `.pptx` decks complete with structured layouts, styling, diagrams, and speaker notes (`actions/ppt_template_workflow.py`).
- **Word Document Generator**: Creates and edits `.docx` documents with rich typography, bullet points, headers, tables, and formatted sections (`actions/docx_tools.py`).
- **Comprehensive PDF Tools**: Merge PDFs, split pages, convert documents to PDF, and extract text/tables with OCR (`actions/pdf_tools.py`).
- **Spreadsheet & Office Builder**: Generates Excel spreadsheets `.xlsx` with calculated formulas and formatted reports (`actions/office_builder.py`, `actions/office_generator.py`).

### 💻 Autonomous Developer & Code Engineering
- **Brahma Dev Agent**: Multi-step coding agent that reads repository code, authors files, runs scripts, and iterates on software tasks (`actions/brahma_dev_agent.py`, `actions/dev_agent.py`).
- **Code Helper**: Debugs code syntax errors, writes algorithms, explains complex codebases, and refactors functions (`actions/code_helper.py`).
- **Claude Code CLI Bridge**: Interoperability bridge to spawn and orchestrate Anthropic's Claude Code CLI tasks directly from Brahma (`actions/claude_code_bridge.py`).

### 💬 Social Media & Messaging Bridges
- **Instagram AI Assistant**: Reads Instagram direct messages, sends alerts for incoming chats, and auto-replies conversationally using AI (`actions/instagram_mcp.py`, `actions/instagram_chat.py`).
- **WhatsApp & Messaging**: Dispatches automated messages via WhatsApp web/native automation and SMS protocols (`actions/send_message.py`).
- **Social Video Uploader**: Automates video publishing and uploading flows (`actions/upload_video.py`).

### 🎵 Media, Spotify & Entertainment
- **Spotify Music Controller**: Full Spotify desktop integration to play, pause, skip, rewind, adjust playback volume, and search playlists/tracks (*"Play my chill playlist"* - `actions/spotify_controller.py`).
- **YouTube Playback & Summarization**: Search YouTube, open videos, extract transcripts, and generate instant video summaries (`actions/youtube_video.py`).
- **Game Launcher & Updater**: Detects installed games (Steam, Epic, Riot), checks patch status, optimizes system focus, and launches titles (*"Launch Valorant"* - `actions/game_updater.py`).

### 📅 Productivity, Meetings & Daily Briefings
- **Personal Daily Briefing**: Comprehensive morning audio report combining local weather, daily calendar meetings, unread emails, and news highlights (`actions/daily_briefing.py`).
- **AI Meeting Assistant**: Real-time meeting listener that captures audio, transcribes discussions, and produces formatted action items and summaries (`actions/meeting_assistant.py`).
- **Calendar & Scheduler**: Create, inspect, and update calendar appointments and alarms (`actions/calendar_scheduler.py`).
- **Smart Reminders**: Timed reminders, countdown timers, and recurring notifications (*"Remind me in 20 minutes to stretch"* - `actions/reminder.py`).

### ⚙️ Windows System Control & Direct Desktop Automation
- **System Power Manager**: Voice and automated commands for Windows sleep, shutdown, reboot, lock screen, and hibernate (`actions/system_manager.py`).
- **Application Launcher & Switcher**: Opens any installed Windows app, system utility, or web shortcut (`actions/open_app.py`, `actions/desktop.py`).
- **Direct Computer Control**: Hardware-level mouse click, cursor movement, keyboard typing, drag-and-drop, and hotkey execution (`actions/computer_control.py`).
- **Windows System Settings**: Adjust system master volume, mute/unmute, toggle Wi-Fi, toggle Bluetooth, and manage display configurations (`actions/computer_settings.py`).
- **Device Screen Wake & Unlock**: Wakes display and unlocks device screens (`actions/unlock_device.py`).

### 🔍 Live Web Intelligence, Search & Travel
- **Real-Time Web Search**: Instant web queries and cited answers powered by live search engines (`actions/web_search.py`).
- **Flight Finder & Travel Scout**: Searches flights, checks departure/arrival routes, and compares ticket options (`actions/flight_finder.py`).
- **Live Weather Forecasts**: Precise meteorological reports, temperature, precipitation, humidity, and multi-day forecasts for any city or current geolocation (`actions/weather_report.py`, `core/device_location.py`).

### 📈 Proactive Sentries & Background Monitors
- **Autonomous Background Watchers**: Monitors cryptocurrency prices, tracks website uptime, and detects system RAM spikes in the background (`actions/background_monitor.py`).
- **Proactive AI Engine**: Detects user idle periods to provide non-intrusive reminders, hydration alerts, and posture check-ins (`actions/proactive.py`).
- **Smart Clipboard Sentry**: Live clipboard listener that detects copied URLs, code blocks, or text and offers instant contextual actions (`core/clipboard_sentry.py`).
- **Foreground Window Context**: Dynamically detects the active foreground app and window title to contextualize AI responses (`core/window_context.py`).

### 🎨 Core UI & Acoustic Infrastructure
- **Cinematic Floating Launcher**: Modern Qt interface featuring 3D cursor gaze tracking, audio visualizer, edge snapping, and theme customization (`ui.py`).
- **Voice Pipeline & Interruption**: Ultra-low-latency voice activation, Gemini native voice synthesis, and true barge-in interruption (<50ms VAD) (`core/echo.py`).
- **Global Hotkey Summon**: Windows-wide keyboard shortcut to summon Brahma instantly from any application (`core/hotkey.py`).
- **Spatial Acoustic Sound Manager**: High-fidelity sound effects for listening cues, deployment whooshes, telemetry chirps, and mission completion (`sound_manager.py`).
- **Safety Confirmations & Undo Framework**: Built-in confirmation guards for sensitive/destructive operations with undo support (`core/confirm.py`, `core/undo.py`).


## Getting Started

### Prerequisites

- Windows 10 or Windows 11
- Python 3.11 or Python 3.12
- Git installed
- Gemini API key
- OpenRouter API key (optional but recommended)
- LLMTR API key (optional OpenAI-compatible provider)

### 1. Clone the repository

```powershell
git clone https://github.com/titechprabhasolutions/Brahma-AI---Lite.git
cd "Brahma AI - Lite"
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
playwright install
```

### 4. Configure API credentials

Create `config/api_keys.json` with your keys:

```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "openrouter_api_key": "YOUR_OPENROUTER_API_KEY",
  "llmtr_api_key": "YOUR_LLMTR_API_KEY",
  "instagram_username": "YOUR_IG_USERNAME",
  "instagram_password": "YOUR_IG_PASSWORD"
}
```

#### Gemini API Key

1. Create a Google Cloud or Gemini account.
2. Enable Gemini API access for your project.
3. Add the generated key to `gemini_api_key`.

#### OpenRouter API Key

1. Register at https://openrouter.ai.
2. Generate an `sk-or-` API key.
3. Add the key to `openrouter_api_key`.

#### LLMTR API Key

1. Create a key at https://llmtr.com/dashboard/keys.
2. Add the key to `llmtr_api_key`, or paste it in Settings → AI Providers.
3. Select LLMTR as the default AI provider. Model IDs use the `vendor/model` form, for example `qwen/qwen3.8-27b-free`. The default API base is `https://llmtr.com/v1`.

### 5. Optional: Configure Discord integration

If you want Discord remote control, populate `config/discord_bot.json` with your bot credentials and connection settings.

### 6. Launch Brahma Echo

```powershell
python main.py
```

For a cleaner startup experience on Windows:

```powershell
start_brahma.vbs
```

## Configuration

Core configuration files:

- `config/api_keys.json` — Gemini, OpenRouter, and LLMTR credentials
- `config/app_settings.json` — voice, UI, startup, and automation preferences
- `config/learned_rules.json` — persistent user preferences, habits, and behavioral directives
- `config/patch_history.json` — audit log of autonomous hotfixes and rollbacks
- `config/patch_backups/` — automatic atomic file backups for instant rollback
- `config/brahma_connect.json` — device pairing, gateway, and discovery settings
- `config/discord_bot.json` — Discord bridge configuration

## Project Structure

- `main.py` — application startup, AI orchestration, Boot Sentry validation, and multimodal event loop
- `ui.py` — cinematic Qt desktop interface, 3D cursor gaze, audio visualizer, and hardware telemetry dashboard
- `test_self_heal.py` — automated headless test runner for self-healing and continuous learning verification
- `sound_manager.py` — spatial acoustic audio engine for tactile UI sound cues and alerts
- `core/boot_sentry.py` — startup crash detection and automatic unbrick recovery sentry
- `core/learned_rules.py` — persistent learned rules manager and dynamic prompt injection engine
- `core/echo.py` — voice pipeline, wake-word activation, Gemini native audio, and <50ms barge-in
- `core/window_context.py` — active foreground window inspector for contextual awareness
- `core/clipboard_sentry.py` — background clipboard monitor for rapid link and code processing
- `core/audio_devices.py` — WASAPI microphone and speaker device configuration
- `core/hotkey.py` — Windows-wide global hotkey listener
- `core/confirm.py` & `core/undo.py` — safety confirmation dialogs and global rollback engine
- `actions/auto_heal_engine.py` — autonomous traceback analyzer, in-memory AST sandbox, and Gemini hotfix engine
- `actions/system_diagnostics_mcp.py` — 0-credit local OS hardware telemetry, RAM hogs, display brightness, and process termination
- `actions/desktop_organizer_mcp.py` — automated desktop decluttering with safe rollback
- `actions/google_workspace_mcp.py` — native Gmail, Google Calendar, and Drive integration
- `actions/playwright_mcp_client.py` & `actions/browser_control.py` — Microsoft @playwright/mcp client for 24+ browser automation actions
- `actions/brahma_connect.py` & `actions/mobile_autopilot.py` — Android companion app gateway and remote mobile autopilot
- `actions/screen_processor.py` — dynamic screenshot capture, active window inspection, and visual QA
- `actions/attention_monitor.py` — camera-based attention tracking, eye contact, drowsiness, and posture alerts
- `actions/pushup_counter.py` — computer-vision pushup and workout rep counter with live form feedback
- `actions/calorie_counter.py` — nutrition tracker, meal logging, and caloric budget calculator
- `actions/ppt_template_workflow.py` — PowerPoint presentation deck generator with custom slide layouts
- `actions/docx_tools.py` — Microsoft Word `.docx` generator and editor
- `actions/pdf_tools.py` — PDF merger, splitter, converter, and OCR text/table extractor
- `actions/office_builder.py` & `actions/office_generator.py` — Excel spreadsheet `.xlsx` and office document generator
- `actions/brahma_dev_agent.py` & `actions/dev_agent.py` — autonomous software engineering and debugging agent
- `actions/code_helper.py` — code syntax debugger, algorithm generator, and refactoring assistant
- `actions/claude_code_bridge.py` — Claude Code CLI execution bridge
- `actions/instagram_mcp.py` & `actions/instagram_chat.py` — Instagram DM monitor and autonomous AI chat responder
- `actions/send_message.py` — WhatsApp web/native automation and messaging dispatcher
- `actions/upload_video.py` — social video publishing automation
- `actions/spotify_controller.py` — Spotify playback, playlist search, and volume control
- `actions/youtube_video.py` — YouTube video search, playback, and transcript summarizer
- `actions/game_updater.py` — Steam/Epic/Riot game launcher and patch checker
- `actions/daily_briefing.py` — morning audio briefing (weather, agenda, emails, news highlights)
- `actions/meeting_assistant.py` — live meeting listener, transcriber, and action item extractor
- `actions/calendar_scheduler.py` — calendar appointment and event scheduler
- `actions/reminder.py` — voice timers, countdowns, and recurring reminders
- `actions/file_controller.py` — deep Windows file search, open, move, copy, rename, and delete
- `actions/file_processor.py` — content extraction from text, CSV, JSON, code, docx, pdf, and images
- `actions/computer_control.py` — direct mouse clicks, cursor movement, typing, and hotkeys
- `actions/computer_settings.py` — system volume, Wi-Fi, Bluetooth, and display controls
- `actions/system_manager.py` — Windows sleep, shutdown, restart, and lock controls
- `actions/open_app.py` & `actions/desktop.py` — launch apps, switch windows, and manage desktop
- `actions/web_search.py` — live web searches with cited summaries
- `actions/flight_finder.py` — flight route search and price estimates
- `actions/weather_report.py` — real-time local and global weather forecasts
- `actions/background_monitor.py` — autonomous crypto price, uptime, and RAM monitors
- `actions/proactive.py` — spontaneous idle suggestions and wellness alerts
- `brahma_connect/` — local gateway, pairing, and remote routing
- `config/` — local settings, credentials, learned rules, and backups
- `plugins/` — optional plugin extensions

## 🎙️ Command Quick Reference

| Category | Voice / Text Command | Action / Capability |
|---|---|---|
| **Autonomous Self-Healing** | *"Trigger test bug"* | Triggers safe simulated error in `actions/test_action.py` |
| **Autonomous Self-Healing** | *"Brahma, fix that bug"* | Synthesizes Gemini hotfix, runs AST verification, and patches code |
| **Autonomous Self-Healing** | *"Brahma, undo last patch"* | Restores modified file from atomic `.bak` backup |
| **Autonomous Self-Healing** | *"Show patch history"* | Displays recent hotfixes, target files, and status |
| **Continuous Learning** | *"Remember to always [rule]"* | Permanently commits behavioral directive into system prompt |
| **Continuous Learning** | *"Show learned rules"* | Lists all active behavioral directives in memory |
| **Hardware & Diagnostics** | *"What's eating my RAM?"* | Pinpoints top memory-consuming applications |
| **Hardware & Diagnostics** | *"Check battery status"* | Reports battery health, percent, and power state |
| **Hardware & Diagnostics** | *"Kill chrome"* | Safely terminates frozen or high-resource applications |
| **Hardware & Diagnostics** | *"Dim screen 20%"* / *"Set brightness 80"* | Adjusts multi-monitor display brightness |
| **Desktop & Files** | *"Organize my desktop"* | Classifies desktop clutter into categorized folders |
| **Desktop & Files** | *"Find file budget.xlsx"* | Searches disk and opens requested file |
| **Desktop & Files** | *"Open downloads folder"* | Navigates directly to requested directory |
| **Browser Automation** | *"Go to github.com and click explore"* | Automated browsing, clicking, and form-filling via Playwright MCP |
| **Google Workspace** | *"Read my unread emails"* | Retrieves and summarizes latest Gmail inbox messages |
| **Google Workspace** | *"What is my schedule today?"* | Reads today's agenda from Google Calendar |
| **Google Workspace** | *"Search Google Drive for quarterly deck"* | Finds documents stored on Google Drive |
| **Android Phone Control** | *"Check phone battery"* | Fetches live phone battery status via Brahma Connect |
| **Android Phone Control** | *"Turn on phone flashlight"* | Triggers mobile hardware flashlight remotely |
| **Android Phone Control** | *"Launch YouTube on phone"* | Remotely opens app via mobile autopilot |
| **Office & Documents** | *"Create a presentation on AI Agents"* | Builds a formatted multi-slide PowerPoint `.pptx` deck |
| **Office & Documents** | *"Generate a Word report for Sprint 4"* | Creates a styled `.docx` document with tables and headers |
| **Office & Documents** | *"Merge these two PDF files"* | Combines multiple PDFs into a single file |
| **Office & Documents** | *"Build a spreadsheet for monthly expenses"* | Creates a `.xlsx` spreadsheet with calculated sum formulas |
| **Coding & Dev Agent** | *"Debug this Python script"* | Pinpoints syntax and logic errors with code solutions |
| **Coding & Dev Agent** | *"Build a simple REST API in FastAPI"* | Autonomous developer agent creates and tests project files |
| **Social & Messaging** | *"Check my Instagram DMs"* | Reads new direct messages and suggests replies |
| **Social & Messaging** | *"Send WhatsApp message to Alex"* | Dispatches message via WhatsApp automation |
| **Media & Music** | *"Play my chill playlist on Spotify"* | Searches and starts Spotify playback |
| **Media & Music** | *"Pause music"* / *"Next track"* | Controls Spotify media playback |
| **Media & Music** | *"Search YouTube for Lo-Fi beats"* | Launches and plays video on YouTube |
| **Media & Music** | *"Launch Valorant"* | Checks patch status and launches game |
| **Vision & Screen** | *"What's on my screen?"* | Analyzes active screen content and provides context |
| **Vision & Screen** | *"Start posture monitor"* | Monitors webcam for slouching and eye fatigue |
| **Fitness & Nutrition** | *"Start pushup counter"* | Uses webcam vision to count workout reps with live form audio |
| **Fitness & Nutrition** | *"Log 450 calories for grilled chicken"* | Logs meal and updates daily macro totals |
| **Productivity & Routine** | *"Good morning Brahma"* / *"Daily briefing"* | Delivers spoken morning brief (weather, meetings, news) |
| **Productivity & Routine** | *"Start meeting assistant"* | Listens, transcribes, and formats meeting action items |
| **Productivity & Routine** | *"Remind me in 25 minutes to take a break"* | Schedules audio and visual countdown reminder |
| **Windows Control** | *"Lock my computer"* | Immediately locks the Windows workstation |
| **Windows Control** | *"Mute system volume"* | Toggles master system audio |
| **Windows Control** | *"Turn off Wi-Fi"* / *"Toggle Bluetooth"* | Toggles Windows hardware connectivity |
| **Travel & Scout** | *"Find flights from New York to London"* | Searches routes and estimated airline pricing |
| **Travel & Scout** | *"What is the weather in Paris tomorrow?"* | Reports meteorological forecast and temperatures |

## Plugin System

Extend Brahma Echo with custom Python plugins by adding files to `plugins/`.

Supported hooks:

- `on_brahma_created(brahma)` — called when the assistant instance is initialized
- `on_startup(brahma)` — called after startup when plugins are registered
- `on_text_command(text, source, brahma=None)` — called for each incoming text command; return `True` to indicate the command was handled

## Best Practices

- Keep credentials in `config/api_keys.json` and avoid committing secrets.
- Use the virtual environment for all development and runtime sessions.
- Restart the app after changing config or adding plugins.
- Review `config/app_settings.json` to tune voice, UI, and automation behavior.

## Community & Support

- Discord: https://discord.gg/gEYmJKKtq3

## License

This project is published under a custom source-available license. See `LICENSE` for details.

## Maintainer

- **Suryaansh Tiwari** ([Buildonaut](https://www.youtube.com/@Buildonaut-AI)) — TiTech Prabha Solutions
  - GitHub: [@titechprabhasolutions](https://github.com/titechprabhasolutions)
  - YouTube: [@Buildonaut-AI](https://www.youtube.com/@Buildonaut-AI)
  - Instagram: [@buildonaut.dev](https://www.instagram.com/buildonaut.dev/)

> Preserve attribution and keep credentials secure when building on top of Brahma Echo.
