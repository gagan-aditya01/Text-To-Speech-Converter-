# 🗣️ Multi-Language Text-to-Speech (TTS) Converter

> A modular, production-ready AI Voice Synthesizer built with Python & Streamlit.  
> Designed for real-time web integration during R&D internship.

---

## ✨ Features

- 🌐 **50+ Languages** — powered by gTTS with BCP-47 language codes
- 🔍 **Searchable Language & Voice Selectors** — instant filtering UI
- 🎙️ **Voice Customization** — gender, tone, and mood options
- 🎧 **In-browser Audio Playback** — stream or download generated audio
- 📜 **Session History** — replay and re-download past conversions
- ⚙️ **Settings Page** — API key management, defaults
- 🔌 **Dual TTS Engine** — gTTS (free) + ElevenLabs (premium)

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/Text-To-Speech-Converter-.git
cd Text-To-Speech-Converter-

# 2. Set up environment
make setup

# 3. Configure .env (copy and fill in your keys)
cp .env.example .env

# 4. Run the app
make run
```

---

## 🏗️ Architecture

```
app/
├── main.py           # Streamlit entry point
├── pages/            # Multi-page layout
├── components/       # Reusable UI components
├── services/         # TTS engine implementations
├── utils/            # Shared utilities
└── config/           # App settings & language data
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed breakdown.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| UI Framework | Streamlit |
| TTS (Free tier) | gTTS |
| TTS (Premium) | ElevenLabs API |
| Audio Processing | pydub |
| Config | python-dotenv |
| Testing | pytest |
| Linting | ruff |

---

## 📋 Development Phases

This project is built in **17 incremental phases** — each a clean, Git-committed unit.

| Phase | Title |
|-------|-------|
| 1 | Project Scaffolding & Git Setup ✅ |
| 2 | Language Data Registry |
| 3 | Abstract TTS Base Class |
| 4 | gTTS Service Integration |
| 5 | Audio Utilities Module |
| 6 | Configuration & Environment Setup |
| 7 | Streamlit App Entry Point |
| 8 | Language Selector Component |
| 9 | Text Input Component |
| 10 | Audio Player Component |
| 11 | Voice & Gender Selector |
| 12 | ElevenLabs Service Integration |
| 13 | Conversion History Module |
| 14 | Settings Page |
| 15 | Unit Tests |
| 16 | UI Polish & Theming |
| 17 | README & Deployment Prep |

---

## 🧪 Testing

```bash
make test    # run pytest with coverage
make lint    # run ruff linter
```

---

## 📄 License

MIT © 2024 — Built during R&D Internship
