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

### Preview Voice Sample (Choose Backend Engine)
```bash
# Using local Qwen3-TTS
python cli.py preview --engine qwen3 --speaker Uncle_Fu --style storyteller

# Using Cloud EdgeTTS (Free, fast, multi-lingual)
python cli.py preview --engine edge --speaker zh-CN-YunxiNeural
```

### Generate Complete Audiobook from EPUB
```bash
python cli.py generate path/to/book.epub --engine qwen3 --output ./dist/my_audiobook
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

## 🧪 Running Tests & CI

```bash
pytest -v tests/
ruff check .
```

---

## 📜 License

Apache-2.0
