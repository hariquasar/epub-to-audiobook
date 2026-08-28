# Qwen3-TTS Audiobook Generator

Production pipeline for generating Chinese audiobooks using Alibaba's `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` on Apple Silicon (MPS).

## Features

- **Sentence-Preserving Chunking**: Ensures splits only occur at natural sentence boundaries (`。！？；…` and closing quotation marks `」` `”`) to prevent truncated or orphaned phrases.
- **Anti-Truncation Duration Audit**: Validates generated audio length against text length (`duration >= chars * 0.14s`) with automatic retries.
- **Silence Tightening**: Automatically caps generated dead air between sentences at 0.30 seconds.
- **Resumable Manifest**: Uses deterministic JSON manifest tracking SHA-256 hashes of text, style prompts, and chunk status to support seamless pause and resume.
- **Apple Silicon MPS Optimization**: Generates in `bfloat16` with native Metal Performance Shaders acceleration.

## Usage

```bash
# 1. Prepare deterministic manifest
python run_shujian_qwen_customvoice.py source.txt output_project --prepare-only

# 2. Run generation
python run_shujian_qwen_customvoice.py source.txt output_project --approved-audition
```
