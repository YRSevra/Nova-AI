# Nova — Personal AI Assistant for macOS

Nova is a real-time, always-running voice AI assistant for macOS.
She listens for your voice, understands commands, controls your Mac, and responds in a natural female voice.

---

## Quick Start (Phase 1)

### Prerequisites
- macOS 12 Monterey or later
- Python 3.10+
- Homebrew installed (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)

### Step 1 — Install system dependencies
```bash
brew install portaudio ffmpeg
```

### Step 2 — Create Python virtual environment
```bash
cd ~/nova
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Add your API key
```bash
cp config/config.example.yaml config/config.yaml
# Then open config/config.yaml and paste your OpenAI API key
```

### Step 5 — Run Nova
```bash
python main.py
```

Say **"Hey Nova"** or just **"Nova"** to wake her up.

---

## Project Structure

```
nova/
├── main.py                  ← Entry point — starts everything
├── requirements.txt         ← All Python dependencies
├── config/
│   ├── config.example.yaml  ← Template (copy to config.yaml)
│   └── config.yaml          ← Your real keys (git-ignored)
├── core/
│   ├── wake_word.py         ← Listens for "Hey Nova"
│   ├── speech_to_text.py    ← Microphone → text (Whisper)
│   ├── ai_brain.py          ← Sends text to OpenAI, gets response
│   ├── voice_output.py      ← Speaks Nova's response (TTS)
│   ├── memory.py            ← Saves context to SQLite
│   └── orchestrator.py      ← Connects all modules together
├── modules/
│   ├── macos_control.py     ← AppleScript + shell commands
│   ├── browser.py           ← Playwright browser automation (Phase 2)
│   ├── file_manager.py      ← File read/write/organize (Phase 2)
│   └── assignment_gen.py    ← GTU assignment PDF generator (Phase 3)
├── data/
│   └── nova_memory.db       ← SQLite database (auto-created)
└── scripts/
    └── com.nova.assistant.plist  ← macOS launchd auto-start file
```

---

## Phase Roadmap

| Phase | What gets built |
|-------|----------------|
| 1 | Wake word, STT, AI brain, voice output, basic macOS control |
| 2 | Browser automation, file system access, persistent memory |
| 3 | Assignment generator, smart reminders, PDF creation |
| 4 | Screen understanding, multi-step autonomous tasks |

---

## Permissions Required (macOS)

Nova needs these permissions — macOS will prompt you on first run:

- **Microphone** — for voice input
- **Accessibility** — for AppleScript app control
- **Automation** — for controlling Finder, Chrome, etc.
- **Full Disk Access** — for reading/organizing your files (optional)

Grant each in: System Settings → Privacy & Security

---

## Security Notes

- `config.yaml` is git-ignored — never commit your API keys
- Nova never sends audio to external servers (Whisper runs locally)
- All automation happens on your machine only
