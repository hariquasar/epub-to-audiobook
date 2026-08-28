# 🎙️ EPUB to Audiobook Studio (BYOM)

> **Bring Your Own Model (BYOM)**: A universal pipeline and interactive Web UI to convert any **EPUB eBook** into structured, high-fidelity audiobooks using your preferred TTS backend (Qwen3-TTS, EdgeTTS, OpenAI-compatible endpoints, or local custom models).

---

## 🌟 Key Features

- **📖 EPUB Ingestion & Chapter Hierarchy**: Automatically parses eBook metadata, Table of Contents, and extracts clean, tag-stripped chapter text.
- **🔌 Bring Your Own Model (BYOM)**:
  - **Local Neural Models**: Native support for Alibaba `Qwen3-TTS-12Hz-1.7B` on Apple Silicon (MPS) / CUDA.
  - **Cloud TTS Providers**: Built-in Microsoft EdgeTTS engine for fast, multi-lingual narration across 50+ languages.
  - **Extensible API Interface**: Easily plug in Kokoro, CosyVoice, F5-TTS, or standard OpenAI-compatible `/v1/audio/speech` endpoints.
- **✂️ Sentence-Preserving Chunking**: Never breaks inside sentences or orphans closing quotation marks (`」`, `”`).
- **🛡️ Anti-Truncation Quality Audit**: Measures output speech duration against text length (`duration >= chars * 0.14s`) with automatic retries.
- **⚡ Silence Tightening & Normalization**: Trims artificial dead air between sentences and peak-normalizes output levels for smooth continuous listening.
- **🔁 Resumable Manifest**: Checkpoint-based generation allows resuming interrupted renders without duplicating audio chunks.
- **🌐 Dual Interface**:
  - **CLI**: Fast scriptable commands for batch jobs and headless servers.
  - **Gradio Web UI**: Browser-based drag-and-drop EPUB upload, voice audition player, and live progress bar.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone git@github.com-personal:hariquasar/epub-to-audiobook.git
cd epub-to-audiobook

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 CLI Usage

### Inspect an EPUB File
```bash
python cli.py parse path/to/book.epub
```

### Preview Voice Sample (Choose Genre & Engine)
```bash
# Fiction (Storyteller / Novel)
python cli.py preview --genre fiction --engine qwen3 --speaker Uncle_Fu

# Non-Fiction (Business / Documentary / Knowledge)
python cli.py preview --genre nonfiction --engine qwen3 --speaker Uncle_Fu

# Using Cloud EdgeTTS (Free, fast, multi-lingual)
python cli.py preview --genre nonfiction --engine edge --speaker zh-CN-YunxiNeural
```

### Generate Complete Audiobook from EPUB
```bash
# Fiction novel with immersive storytelling rhythm
python cli.py generate path/to/novel.epub --genre fiction --engine qwen3 --output ./dist/novel

# Non-fiction business/history book with crisp cadence
python cli.py generate path/to/business.epub --genre nonfiction --engine qwen3 --output ./dist/business
```

---

## 🌐 Web Interface (Browser Upload & Generate)

Launch the web studio:

```bash
python cli.py web
# Or:
python web_ui.py
```

Then open `http://127.0.0.1:7860` in your browser:
1. **Drag & drop** any `.epub` file to view chapter breakdown and character count.
2. Select your **TTS Engine** (`Local Qwen3-TTS` or `Cloud EdgeTTS`) and **Speaker / Voice**.
3. Click **"🎧 Test Narrator Voice Sample"** to preview audio.
4. Click **"🚀 Generate Audiobook"** with live progress tracking and download the final master `.flac` file.

---

## 📁 Architecture

```
epub-to-audiobook/
├── cli.py                    # Unified CLI entrypoint (parse / preview / generate / web)
├── web_ui.py                 # Gradio Web UI application
├── pyproject.toml            # Project metadata and tool configuration
├── requirements.txt          # Core dependencies
├── docs/
│   └── academic_research_audiobook_quality.md # Multi-disciplinary research report
├── core/
│   ├── __init__.py
│   ├── config.py             # Presets, style definitions, and model constants
│   ├── epub_parser.py        # EPUB extractor (metadata, chapters, HTML text cleaning)
│   ├── text_processor.py     # Sentence-preserving chunker and Traditional-to-Simplified converter
│   ├── tts_engine.py         # BYOM Multi-Backend TTS Engine (Qwen3, EdgeTTS, Extensible Base)
│   └── audiobook_builder.py  # Manifest management, chapter / full-book assembly
└── tests/
    ├── test_config.py
    ├── test_epub_parser.py
    ├── test_text_processor.py
    └── test_tts_engine.py
```

---

## 📚 Academic Research & Scientific Foundations

This project is built on cross-disciplinary scientific research across Cognitive Psychology, Psychoacoustics, Speech Synthesis (ACL / Interspeech), and Audio Engineering (AES TD1004 / Audible ACX).

Read our full research paper: [docs/academic_research_audiobook_quality.md](docs/academic_research_audiobook_quality.md).

---

## 🗺️ Product Roadmap & Milestones

- ✅ **v0.1.0 - Core Engine & BYOM Multi-Backend** (Current Release): EPUB parsing, sentence-safe chunker (0% comma splits), Qwen3-TTS & EdgeTTS backends, 300ms tail buffer, anti-truncation audit, M4B chapter export, Web UI & CLI.
- 🎯 **v0.2.0 - Psychoacoustics & ACX Audio Mastering Standards**: Audible ACX (-20 dB RMS, -3 dBTP limiter, < -60 dB noise floor), EBU R128 loudness normalizer, and zero-shot reference voice cloning.
- 🎯 **v0.3.0 - Computational Narratology & Multi-Speaker Dramatization**: Context-aware prosody modeling (Interspeech/ACL), automatic character dialogue extraction, narrator/character voice assignment, parallel batch processing, Docker container.
- 🎯 **v0.4.0 - Time-Aligned Transcripts & HCI Enhancements**: Synchronized WebVTT / LRC read-along transcripts, speed-invariant pitch scaling optimization (1.25x–2.0x playback), chapter cover embedding.
- 🎯 **v0.5.0 - Progressive Streaming & Continuous Playback (Upload & Keep Listening)**: Zero-wait instant listening (start playing within 3s of uploading EPUB), live WebSocket/HTTP stream, seamless auto-play chapter queue, and background pre-generation ahead of playback cursor.
- 🎯 **v1.0.0 - Production Readiness & Open Cloud APIs**: OpenAI `/v1/audio/speech` standard API server, Audiobookshelf library sync, >90% test coverage, and multi-lingual translation pipeline.

---

## 🧪 Running Tests & CI

```bash
pytest -v tests/
ruff check .
```

---

## 📜 License

Apache-2.0
