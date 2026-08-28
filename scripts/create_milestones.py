#!/usr/bin/env python3
"""Helper script to create GitHub Milestones and Issues for epub-to-audiobook."""

import subprocess
import sys

MILESTONES = [
    {
        "title": "v0.1.0 - Core Engine & BYOM Multi-Backend (Current Release)",
        "description": "Foundational release supporting EPUB parsing, sentence-safe chunking, Qwen3-TTS & EdgeTTS backends, CLI & Gradio Web UI.",
        "due_date": "2026-09-05T00:00:00Z",
    },
    {
        "title": "v0.2.0 - Advanced Audio Packaging & Voice Cloning",
        "description": "Support for Apple Books / Audiobookshelf M4B chapter metadata, EBU R128 loudness normalization, and reference voice cloning.",
        "due_date": "2026-09-20T00:00:00Z",
    },
    {
        "title": "v0.3.0 - Multi-Speaker Dialogue & Batch Processing",
        "description": "Automatic character dialogue extraction, multi-speaker role assignment, parallel processing queue, and Docker deployment.",
        "due_date": "2026-10-10T00:00:00Z",
    },
    {
        "title": "v1.0.0 - Production Readiness & Open Cloud APIs",
        "description": "Production-grade OpenAPI server, complete multi-lingual support, Audiobookshelf direct library sync, and test coverage > 90%.",
        "due_date": "2026-11-01T00:00:00Z",
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
