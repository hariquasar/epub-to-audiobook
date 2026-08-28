#!/usr/bin/env python3
"""CLI interface for Universal EPUB Audiobook Generator (BYOM Architecture)."""

from __future__ import annotations

import argparse
from pathlib import Path

from core import (
    DEFAULT_MAX_CHARS,
    DEFAULT_SPEAKER,
    STYLE_PRESETS,
    AudiobookBuilder,
    create_tts_engine,
    parse_epub,
)


def cmd_parse(args: argparse.Namespace) -> None:
    """Parse and inspect an EPUB file without running TTS."""
    epub_path = Path(args.epub)
    book = parse_epub(epub_path)

    print("\n=======================================================")
    print(f"📖 Title   : {book.title}")
    print(f"✍️  Author  : {book.author}")
    print(f"🌐 Language: {book.language}")
    print(f"📑 Chapters: {len(book.chapters)}")
    print(f"📝 Total Chars: {book.total_characters:,}")
    print("=======================================================\n")

    for c in book.chapters:
        snippet = c.text.replace("\n", " ")[:60]
        print(f"[{c.index:02d}] {c.title:<24} | {c.character_count:>6,} chars | {snippet}...")


def cmd_preview(args: argparse.Namespace) -> None:
    """Generate a quick voice audition sample."""
    engine = create_tts_engine(args.engine)
    text = (
        args.text
        or "这是一个通用的有声书测试样本。欢迎使用自备模型有声书制作工作台，体验流畅自然的多语种旁白与说书人音色。"
    )
    out_path = Path(args.output)

    print(f"Generating preview with engine '{args.engine}' for text: {text}")
    audio, sr, audit = engine.synthesize(
        text=text,
        speaker=args.speaker,
        style_preset=args.style,
    )
    import soundfile as sf

    sf.write(str(out_path), audio, sr, subtype="PCM_16")
    print(f"✅ Preview saved to: {out_path} ({audit['duration_seconds']:.2f}s, sr={sr})")


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate an audiobook from an EPUB file."""
    epub_path = Path(args.epub)
    output_dir = Path(args.output or f"./output_{epub_path.stem}")

    engine = create_tts_engine(args.engine)
    builder = AudiobookBuilder(
        output_dir=output_dir,
        engine=engine,
        speaker=args.speaker,
        style_preset=args.style,
        max_chars=args.max_chars,
    )
    final_file = builder.build_from_epub(epub_path)
    print(f"\n🎉 Audiobook generated successfully: {final_file}\n")


def cmd_web(args: argparse.Namespace) -> None:
    """Launch the Gradio Web UI."""
    from web_ui import launch_app

    launch_app(host=args.host, port=args.port)


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal EPUB Audiobook Generator (BYOM)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Parse command
    p_parse = subparsers.add_parser("parse", help="Inspect and list chapters in an EPUB file")
    p_parse.add_argument("epub", help="Path to the .epub file")
    p_parse.set_defaults(func=cmd_parse)

    # Preview command
    p_prev = subparsers.add_parser("preview", help="Generate a quick voice sample")
    p_prev.add_argument("--engine", default="qwen3", choices=["qwen3", "edge"], help="TTS Engine backend")
    p_prev.add_argument("--text", default=None, help="Text to synthesize for preview")
    p_prev.add_argument("--speaker", default=DEFAULT_SPEAKER, help="Speaker / Voice name")
    p_prev.add_argument("--style", default="storyteller", choices=list(STYLE_PRESETS.keys()), help="Style preset")
    p_prev.add_argument("--output", default="audition.wav", help="Output WAV path")
    p_prev.set_defaults(func=cmd_preview)

    # Generate command
    p_gen = subparsers.add_parser("generate", help="Generate complete audiobook from EPUB")
    p_gen.add_argument("epub", help="Path to the .epub file")
    p_gen.add_argument("--engine", default="qwen3", choices=["qwen3", "edge"], help="TTS Engine backend")
    p_gen.add_argument("--output", "-o", default=None, help="Output directory path")
    p_gen.add_argument("--speaker", default=DEFAULT_SPEAKER, help="Speaker / Voice name")
    p_gen.add_argument("--style", default="storyteller", choices=list(STYLE_PRESETS.keys()), help="Style preset")
    p_gen.add_argument(
        "--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="Max characters per chunk (default: 200)"
    )
    p_gen.set_defaults(func=cmd_generate)

    # Web UI command
    p_web = subparsers.add_parser("web", help="Launch the web browser interface")
    p_web.add_argument("--host", default="127.0.0.1", help="Host IP to bind")
    p_web.add_argument("--port", type=int, default=7860, help="Port to bind")
    p_web.set_defaults(func=cmd_web)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
