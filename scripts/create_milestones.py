#!/usr/bin/env python3
"""Helper script to create GitHub Milestones and Issues for epub-to-audiobook."""

import subprocess
import sys

MILESTONES = [
    {
        "title": "v0.1.0 - Core Engine & BYOM Multi-Backend (Current Release)",
        "description": "Foundational release: EPUB parsing, sentence-preserving chunking (0% comma splits), Qwen3-TTS & EdgeTTS backends, 300ms tail buffer, anti-truncation audit, M4B chapter export, CLI & Gradio Web UI.",
        "due_date": "2026-09-05T00:00:00Z",
    },
    {
        "title": "v0.2.0 - Psychoacoustics & ACX Audio Mastering Standards",
        "description": "Audible ACX & AES TD1004 mastering compliance (-20 dB RMS, -3 dBTP True Peak limiter, < -60 dB noise floor), EBU R128 loudness normalizer, and zero-shot voice cloning from 3s reference audio.",
        "due_date": "2026-09-20T00:00:00Z",
    },
    {
        "title": "v0.3.0 - Computational Narratology & Multi-Speaker Dramatization",
        "description": "Context-aware prosody modeling (Interspeech/ACL research), automatic character dialogue extraction, narrator/character voice assignment, parallel batch processing queue, and Docker containerization.",
        "due_date": "2026-10-10T00:00:00Z",
    },
    {
        "title": "v0.4.0 - Time-Aligned Transcripts & HCI Enhancements",
        "description": "Word/sentence-level synchronized WebVTT/LRC transcript generation for read-along listening, speed-invariant pitch scaling optimization (1.25x–2.0x playback), and chapter art embedding.",
        "due_date": "2026-10-25T00:00:00Z",
    },
    {
        "title": "v0.5.0 - Progressive Streaming & Continuous Playback (Upload & Keep Listening)",
        "description": "Zero-wait instant listening: upload any EPUB and start listening immediately in the browser via chunk pre-buffering, live WebSocket/HTTP stream, seamless auto-play chapter queue, and background pre-generation ahead of playback cursor.",
        "due_date": "2026-11-08T00:00:00Z",
    },
    {
        "title": "v1.0.0 - Production Readiness & Open Cloud APIs",
        "description": "OpenAI /v1/audio/speech standard API compatibility server, Audiobookshelf direct library sync, full test coverage > 90%, and end-to-end multi-lingual translation-narration pipeline.",
        "due_date": "2026-11-30T00:00:00Z",
    },
]

REPO = "hariquasar/epub-to-audiobook"


def main():
    print(f"Creating milestones for {REPO}...")
    for m in MILESTONES:
        cmd = [
            "gh",
            "api",
            f"/repos/{REPO}/milestones",
            "-X",
            "POST",
            "-f",
            f"title={m['title']}",
            "-f",
            f"description={m['description']}",
            "-f",
            f"due_on={m['due_date']}",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"✅ Created Milestone: {m['title']}")
            else:
                print(f"⚠️ Milestone '{m['title']}': {res.stderr.strip() or res.stdout.strip()}")
        except FileNotFoundError:
            print("❌ GitHub CLI 'gh' not found. Please install gh and run 'gh auth login'.")
            sys.exit(1)


if __name__ == "__main__":
    main()
