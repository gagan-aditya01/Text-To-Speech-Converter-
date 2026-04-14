# 🗣️ VoiceCraft — Multi-Language Text-to-Speech Converter

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/Tests-416%20passing-22C55E?logo=pytest&logoColor=white)](./tests)
[![License](https://img.shields.io/badge/License-MIT-7C3AED)](./LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](./Dockerfile)

A production-ready, modular AI voice synthesizer supporting **52 languages** and **2 TTS engines** (gTTS + ElevenLabs), built with a strict **17-phase development plan** and 100% tested architecture.

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| 🌐 **52 Languages** | English, Hindi, French, Spanish, Arabic, Japanese and 46 more |
| 🎙️ **2 TTS Engines** | gTTS (free, offline-capable) · ElevenLabs (premium, neural voices) |
| 🎭 **Mood Control** | Neutral · Calm · Formal · Energetic — mapped to voice_settings |
| 🚀 **Config-driven** | Switch engines via `.env` — zero code changes |
| 📜 **Session History** | Last 10 conversions with replay buttons |
| ⬇️ **MP3 Download** | One-click download for every generated audio |
| 🔑 **RTL Support** | Arabic, Hebrew, Persian, Urdu right-aligned automatically |
| 🐳 **Docker-ready** | Multi-stage image with healthcheck and non-root user |
| 🧪 **416 Tests** | 403 unit + 13 real gTTS integration, all passing |
| 🔒 **Secure** | API keys never logged, XSRF protection, non-root container |

---

## 🏗️ Architecture

```
voicecraft/
├── app/
│   ├── main.py                    ← Streamlit entry point
│   ├── components/
│   │   ├── language_selector.py   ← Phase 8: searchable 52-language picker
│   │   ├── text_input.py          ← Phase 9: RTL, char/word counter, validation
│   │   ├── audio_player.py        ← Phase 10: metadata ribbon, session history
│   │   └── voice_selector.py      ← Phase 11: mood search, gender, speed
│   ├── services/
│   │   ├── base_tts.py            ← Phase 3: abstract BaseTTSService contract
│   │   ├── gtts_service.py        ← Phase 4: gTTS engine
│   │   ├── elevenlabs_service.py  ← Phase 12: ElevenLabs premium engine
│   │   └── engine_router.py       ← Phase 13: config-driven factory
│   ├── utils/
│   │   ├── language_data.py       ← Phase 2: 52-language registry
│   │   ├── audio_utils.py         ← Phase 5: file I/O, cleanup, MIME types
│   │   ├── error_handler.py       ← Phase 14: 8-category error system
│   │   └── logger.py              ← Phase 6: centralized logging
│   ├── config/
│   │   └── settings.py            ← Phase 6: typed env-driven config
│   └── styles/
│       └── css.py                 ← Phase 16: full design system
├── tests/
│   ├── conftest.py                ← fixtures: tmp dir, ttsr request factory
│   ├── test_integration.py        ← Phase 15: end-to-end with real gTTS
│   └── test_*.py                  ← 13 unit test files
├── Dockerfile                     ← Multi-stage production image
├── docker-compose.yml             ← Compose with named volume
├── .github/workflows/ci.yml       ← GitHub Actions (lint + unit + integration)
├── .streamlit/config.toml         ← Dark theme + headless server config
├── pytest.ini                     ← Test markers (integration, slow)
├── Makefile                       ← Dev + Docker + test commands
└── requirements.txt
```

---

## 🚀 Quick Start

### Option A — Local Development

```bash
# 1. Clone
git clone https://github.com/gagan-aditya01/Text-To-Speech-Converter-.git
cd Text-To-Speech-Converter-

# 2. Setup (creates .venv, installs deps, copies .env.example → .env)
make setup

# 3. Configure (optional — gTTS works with no changes)
nano .env

# 4. Run
make run
# → http://localhost:8501
```

### Option B — Docker

```bash
# Build + run in one command
make docker-build && make docker-run
# → http://localhost:8501

# Or with Docker Compose (detached)
make docker-compose-up
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and edit:

```bash
# ── TTS Engine ──────────────────────────────────────────
TTS_ENGINE=gtts              # "gtts" (free) | "elevenlabs" (premium)

# ── ElevenLabs API Key ──────────────────────────────────
# Required only when TTS_ENGINE=elevenlabs
# Get your free key at: https://elevenlabs.io
ELEVENLABS_API_KEY=

# ── Defaults ────────────────────────────────────────────
DEFAULT_LANGUAGE=en
DEFAULT_GENDER=female
DEFAULT_MOOD=neutral
MAX_TEXT_LENGTH=5000
MAX_OUTPUT_FILES=20
LOG_LEVEL=INFO
```

### Switching to ElevenLabs

```bash
# .env
TTS_ENGINE=elevenlabs
ELEVENLABS_API_KEY=el_your_key_here
```

Restart the app — no code changes required.

---

## 🎛️ Engine Comparison

| Feature | gTTS | ElevenLabs |
|---------|------|-----------|
| **Cost** | Free (unlimited) | Paid (10K chars/month free) |
| **Languages** | 52 | 30+ (via multilingual_v2) |
| **Voice quality** | Good | Premium neural |
| **Mood control** | Speed only | Full (stability, style, boost) |
| **API key** | None | Required |
| **Offline** | ✅ (after first use) | ❌ |

---

## 🧪 Testing

```bash
# All tests (unit + integration)
make test

# Unit tests only — fast, offline (~0.6s, 403 tests)
make test-unit

# Integration tests — real gTTS network calls (~12s, 13 tests)
make test-integration

# With HTML coverage report
make test-cov
open reports/coverage/index.html
```

### Test pyramid

```
 ┌─────────────────────────────────────────────┐
 │         Integration Tests (13)              │  real gTTS · file I/O · cleanup
 ├─────────────────────────────────────────────┤
 │              Unit Tests (403)               │  pure functions · mocked HTTP · all paths
 └─────────────────────────────────────────────┘
```

---

## 🐳 Docker

```bash
# Build image
make docker-build
# → voicecraft:latest (~250MB)

# Run with env vars
make docker-run

# Stop
make docker-stop

# Full compose stack (with persistent output volume)
make docker-compose-up
make docker-compose-down
```

The Dockerfile:
- Multi-stage build (builder → runtime) to minimize image size
- Non-root `voicecraft` user for security
- Named volume for `/app/output` (audio persists between restarts)
- HEALTHCHECK on `/_stcore/health`

---

## 🔧 Development Workflow

```bash
make help          # list all commands
make setup         # first-time setup
make run           # dev server
make test-unit     # fast test feedback loop
make lint          # flake8 check
make clean         # remove caches + generated audio
```

### Git discipline (1 phase = 1 commit)

```
Phase 1  — Project scaffolding
Phase 2  — Language data registry (52 languages)
Phase 3  — Abstract TTS base class
Phase 4  — gTTS service integration
Phase 5  — Audio utilities module
Phase 6  — Configuration & environment
Phase 7  — Streamlit app entry point
Phase 8  — Language selector component
Phase 9  — Text input component
Phase 10 — Audio player component
Phase 11 — Voice & gender selector
Phase 12 — ElevenLabs service integration
Phase 13 — Engine router factory
Phase 14 — Centralized error handler
Phase 15 — Integration tests
Phase 16 — UI polish & design system
Phase 17 — Production README & deployment config ← current
```

---

## 📦 Dependencies

```
streamlit       — UI framework
gTTS            — Google Text-to-Speech (free engine)
requests        — ElevenLabs API calls + integration tests
pydub           — Audio processing utilities
python-dotenv   — Environment configuration
pytest          — Test runner
```

---

## 📁 Key Design Decisions

### Two-layer component pattern
Every UI component has:
1. **Pure logic functions** — testable without Streamlit (e.g. `filter_moods`, `build_audio_metadata`)
2. **Thin render function** — Streamlit wrapper that calls pure functions

### Stateless services
TTS engines return `TTSResult(audio_bytes=...)`. File I/O is centralized in `audio_utils.save_audio()`. Engines never write to disk.

### Fail-fast validation
`TTSRequest`, `Settings`, and `build_voice_config()` all raise `ValueError` at instantiation if inputs are invalid. Errors never propagate silently.

### Error classification
`error_handler.classify_error()` maps any exception to one of 8 semantic categories (`AUTH`, `NETWORK`, `TIMEOUT`, `RATE_LIMIT`, etc.) each with actionable guidance and a retryable flag.

---

## 🤝 Contributing

1. Fork → branch off `main`
2. Add feature + tests (maintain 100% pure function coverage)
3. `make lint && make test-unit`
4. Open a PR — CI runs automatically

---

## 📄 License

MIT © 2024 [gagan-aditya01](https://github.com/gagan-aditya01)
