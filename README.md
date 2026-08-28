# 🎙️ Qwen3-TTS EPUB Audiobook Generator

An end-to-end Python pipeline and Web UI to upload any **EPUB eBook** and generate high-fidelity, chapter-aware Chinese audiobooks using Alibaba's `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` on Apple Silicon (MPS).

---

## 🌟 Key Features

- **📖 EPUB Ingestion & Chapter Parsing**: Automatically extracts metadata, chapter table of contents, and clean plain text from `.epub` eBooks.
- **✂️ Sentence-Preserving Chunking**: Never splits inside a sentence or detaches trailing quotes (`」`, `”`). Ensures smooth prosody across chunk boundaries.
- **🛡️ Anti-Truncation Audit**: Automatically measures speech duration against character counts (`duration >= chars * 0.14s`) to catch and retry any early-terminating model outputs.
- **⚡ Silence Tightening**: Trims unnatural dead air between sentences and caps pauses at 0.30 seconds.
- **🔁 Resumable Manifest**: Uses a deterministic JSON checkpoint manifest so jobs can be paused, interrupted, or restarted without losing completed audio chunks.
- **🌐 Dual Interface**:
  - **CLI**: Fast, scriptable commands for parsing, voice previewing, and batch rendering.
  - **Web UI (Gradio)**: Drag-and-drop EPUB upload, chapter inspector, voice audition player, and one-click audiobook generation in the browser.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone git@github.com-personal:hariquasar/<REPO_NAME>.git
cd qwen3-tts

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 CLI Usage

### Inspect an EPUB eBook
```bash
python cli.py parse path/to/book.epub
```

### Preview a Narrator Voice Sample
```bash
python cli.py preview --speaker Uncle_Fu --style storyteller --output audition.wav
```

### Generate Complete Audiobook from EPUB
```bash
python cli.py generate path/to/book.epub --speaker Uncle_Fu --output ./dist/my_audiobook
```

---

## 🌐 Web Interface (Upload & Generate)

Launch the local web browser UI:

```bash
python cli.py web
# Or directly:
python web_ui.py
```

Then open `http://127.0.0.1:7860` in your browser:
1. **Drag & drop** any `.epub` file to view chapter breakdown and word counts.
2. Select your **Speaker** (`Uncle_Fu`, etc.) and **Style preset** (`storyteller`, `calm_narrator`, `energetic`).
3. Click **"🎧 Test Narrator Voice Sample"** to listen to an audition.
4. Click **"🚀 Generate Audiobook"** with live progress tracking and download the master `.flac` file.

---

## 📁 Architecture

```
qwen3-tts/
├── cli.py                    # Unified CLI entrypoint (parse / preview / generate / web)
├── web_ui.py                 # Gradio Web UI browser application
├── requirements.txt          # Python dependencies
├── core/
│   ├── __init__.py
│   ├── config.py             # Presets, style definitions, and model constants
│   ├── epub_parser.py        # EPUB extractor (metadata, chapters, HTML text cleaning)
│   ├── text_processor.py     # Sentence-preserving chunker and Traditional-to-Simplified converter
│   ├── tts_engine.py         # Qwen3-TTS engine wrapper with audit & silence tightening
│   └── audiobook_builder.py  # Manifest management, chapter / full-book assembly
```

---

## 📜 License

Apache-2.0
