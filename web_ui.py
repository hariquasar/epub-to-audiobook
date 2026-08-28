"""Gradio Web Interface for Universal EPUB Audiobook Generator (BYOM Architecture)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import gradio as gr
import soundfile as sf

from core import (
    STYLE_PRESETS,
    AudiobookBuilder,
    BaseTTSEngine,
    create_tts_engine,
    parse_epub,
)

# Engine cache
_ENGINES: dict[str, BaseTTSEngine] = {}


def get_engine(engine_type: str) -> BaseTTSEngine:
    global _ENGINES
    if engine_type not in _ENGINES:
        _ENGINES[engine_type] = create_tts_engine(engine_type)
    return _ENGINES[engine_type]


def inspect_epub(epub_file: Optional[str]) -> str:
    """Read uploaded EPUB file and return summary table of chapters."""
    if not epub_file:
        return "Please upload an EPUB file."

    try:
        book = parse_epub(epub_file)
        lines = [
            f"### 📖 {book.title}",
            f"- **Author**: {book.author}",
            f"- **Language**: {book.language}",
            f"- **Total Chapters**: {len(book.chapters)}",
            f"- **Total Characters**: {book.total_characters:,}",
            "",
            "| Chapter | Title | Characters | Preview |",
            "|---|---|---|---|",
        ]
        for c in book.chapters[:20]:
            snippet = c.text.replace("\n", " ")[:40]
            lines.append(f"| {c.index} | {c.title} | {c.character_count:,} | {snippet}... |")
        if len(book.chapters) > 20:
            lines.append(f"| ... | and {len(book.chapters) - 20} more chapters | ... | ... |")
        return "\n".join(lines)
    except Exception as exc:
        return f"❌ Error reading EPUB: {exc}"


def preview_voice(text: str, engine_choice: str, speaker: str, style_preset: str) -> Optional[str]:
    """Generate a quick voice audition."""
    if not text.strip():
        text = "清乾隆十八年六月，陕西扶风延绥镇总兵衙门内院，一个十四岁的女孩儿跳跳蹦蹦的走向教书先生书房。"
    try:
        engine = get_engine(engine_choice)
        audio, sr, audit = engine.synthesize(
            text=text,
            speaker=speaker,
            style_preset=style_preset,
        )
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, audio, sr, subtype="PCM_16")
        return tmp.name
    except Exception as exc:
        gr.Warning(f"Error generating preview: {exc}")
        return None


def generate_audiobook(
    epub_file: Optional[str],
    engine_choice: str,
    speaker: str,
    style_preset: str,
    custom_style: str,
    max_chars: int,
    progress=gr.Progress(),
) -> tuple[Optional[str], str]:
    """Process the uploaded EPUB and build full audiobook."""
    if not epub_file:
        return None, "Please upload an EPUB file first."

    try:
        epub_path = Path(epub_file)
        output_dir = Path("./audiobook_outputs") / epub_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        engine = get_engine(engine_choice)
        builder = AudiobookBuilder(
            output_dir=output_dir,
            engine=engine,
            speaker=speaker,
            style_preset=style_preset,
            custom_style=custom_style if custom_style.strip() else None,
            max_chars=max_chars,
        )

        def progress_tracker(curr: int, total: int, status_msg: str):
            progress(curr / max(total, 1), desc=status_msg)

        final_flac = builder.build_from_epub(epub_path, progress_callback=progress_tracker)
        return str(final_flac), f"✅ Completed! Master audiobook saved to: {final_flac}"
    except Exception as exc:
        return None, f"❌ Failed to generate audiobook: {exc}"


def update_speaker_choices(engine_choice: str):
    if engine_choice == "edge":
        return gr.Dropdown(
            choices=[
                "zh-CN-YunxiNeural",
                "zh-CN-YunjianNeural",
                "zh-CN-XiaoxiaoNeural",
                "zh-HK-HiuGaaiNeural",
                "zh-TW-HsiaoChenNeural",
                "en-US-GuyNeural",
                "en-US-JennyNeural",
            ],
            value="zh-CN-YunxiNeural",
        )
    else:
        return gr.Dropdown(
            choices=["Uncle_Fu", "Aiden", "Seraphina"],
            value="Uncle_Fu",
        )


def create_ui() -> gr.Blocks:
    with gr.Blocks(title="Universal EPUB Audiobook Studio", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🎙️ Universal EPUB Audiobook Studio (BYOM)
            Upload any **EPUB eBook** and generate complete, high-fidelity audiobooks with your choice of TTS engine:
            - **Local Qwen3-TTS**: High-emotion storytelling with Apple Silicon GPU (MPS) acceleration.
            - **Cloud EdgeTTS**: High-speed, multi-lingual crystal clear narration.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                epub_input = gr.File(
                    label="Upload EPUB eBook",
                    file_types=[".epub"],
                    type="filepath",
                )

                engine_select = gr.Radio(
                    label="TTS Engine Backend (Bring Your Own Model)",
                    choices=[("Local Qwen3-TTS (1.7B)", "qwen3"), ("Cloud EdgeTTS (Multi-Lingual)", "edge")],
                    value="qwen3",
                )

                speaker_select = gr.Dropdown(
                    label="Narrator Speaker / Voice",
                    choices=["Uncle_Fu", "Aiden", "Seraphina"],
                    value="Uncle_Fu",
                )

                style_preset = gr.Dropdown(
                    label="Narration Style Preset",
                    choices=list(STYLE_PRESETS.keys()),
                    value="storyteller",
                )

                custom_style = gr.Textbox(
                    label="Custom Style Prompt (Optional Override)",
                    placeholder="Leave empty to use the selected style preset...",
                    lines=3,
                )

                max_chars_slider = gr.Slider(
                    label="Max Characters Per Sentence-Safe Chunk",
                    minimum=100,
                    maximum=350,
                    value=200,
                    step=10,
                )

                preview_btn = gr.Button("🎧 Test Narrator Voice Sample", variant="secondary")
                preview_audio = gr.Audio(label="Voice Sample Audition", type="filepath")

                generate_btn = gr.Button("🚀 Generate Audiobook", variant="primary", size="lg")

            with gr.Column(scale=1):
                epub_info = gr.Markdown("Upload an EPUB file to inspect chapter structure and character counts.")
                status_text = gr.Textbox(label="Status / Output", interactive=False)
                output_audio = gr.File(label="Download Master Audiobook (.flac)")

        # Event triggers
        epub_input.change(fn=inspect_epub, inputs=[epub_input], outputs=[epub_info])
        engine_select.change(fn=update_speaker_choices, inputs=[engine_select], outputs=[speaker_select])
        preview_btn.click(
            fn=preview_voice,
            inputs=[custom_style, engine_select, speaker_select, style_preset],
            outputs=[preview_audio],
        )
        generate_btn.click(
            fn=generate_audiobook,
            inputs=[epub_input, engine_select, speaker_select, style_preset, custom_style, max_chars_slider],
            outputs=[output_audio, status_text],
        )

    return demo


def launch_app(host: str = "127.0.0.1", port: int = 7860):
    demo = create_ui()
    demo.launch(server_name=host, server_port=port, share=False)


if __name__ == "__main__":
    launch_app()
