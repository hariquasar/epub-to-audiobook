"""Gradio Web Interface for Universal EPUB Audiobook Generator (BYOM & Genre-Aware)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import gradio as gr
import soundfile as sf

from core import (
    FICTION_PRESETS,
    NONFICTION_PRESETS,
    AudiobookBuilder,
    BaseTTSEngine,
    create_tts_engine,
    parse_epub,
)

# Engine cache
_ENGINES: dict[str, BaseTTSEngine] = {}


def liquid_glass_css() -> str:
    """Return the tokenized Liquid Glass layer used by the Gradio studio."""
    return """
    :root {
      --ink: #122033;
      --text-primary: #102039;
      --text-secondary: #4e627e;
      --line: rgba(255, 255, 255, 0.72);
      --glass: rgba(255, 255, 255, 0.50);
      --glass-strong: rgba(255, 255, 255, 0.72);
      --accent: #0a6ee8;
      --accent-deep: #0758bd;
      --shadow: 0 20px 60px rgba(20, 61, 110, 0.16), 0 2px 8px rgba(31, 68, 112, 0.08);
    }
    .gradio-container {
      min-height: 100vh;
      color: var(--text-primary);
      background:
        radial-gradient(circle at 4% 2%, rgba(144, 211, 255, .75), transparent 29rem),
        radial-gradient(circle at 96% 10%, rgba(212, 180, 255, .58), transparent 28rem),
        radial-gradient(circle at 50% 100%, rgba(164, 243, 219, .58), transparent 31rem),
        linear-gradient(135deg, #e9f5ff 0%, #f5f3ff 52%, #e9faf3 100%);
    }
    .app-shell { max-width: 1180px; margin: 0 auto; padding: 32px 20px 48px; }
    .hero { margin: 0 0 24px; padding: 30px 32px; border: 1px solid var(--line); border-radius: 28px; background: var(--glass); box-shadow: var(--shadow); backdrop-filter: blur(28px) saturate(145%); -webkit-backdrop-filter: blur(28px) saturate(145%); }
    .eyebrow { margin: 0 0 9px; color: #0758bd; font-size: .76rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
    .hero h1 { margin: 0; color: var(--ink); font-size: clamp(2rem, 4vw, 3.4rem); letter-spacing: -.045em; line-height: 1.03; }
    .hero p { max-width: 650px; margin: 14px 0 0; color: var(--text-secondary); font-size: 1.03rem; line-height: 1.6; }
    .glass-panel { height: 100%; padding: 22px; border: 1px solid var(--line); border-radius: 24px; background: var(--glass); box-shadow: var(--shadow); backdrop-filter: blur(24px) saturate(135%); -webkit-backdrop-filter: blur(24px) saturate(135%); }
    .section-label { margin: 0 0 6px; color: var(--ink); font-size: 1.08rem; font-weight: 720; }
    .section-copy { margin: 0 0 18px; color: var(--text-secondary); font-size: .92rem; line-height: 1.5; }
    .upload-zone { min-height: 148px; border: 1px dashed rgba(10, 110, 232, .52); border-radius: 18px; background: rgba(255,255,255,.42); }
    .upload-zone:hover { background: rgba(255,255,255,.7); border-color: var(--accent); }
    .primary-action button { min-height: 52px; border: 0; border-radius: 16px; background: linear-gradient(135deg, var(--accent), #48a4ff); box-shadow: 0 10px 22px rgba(10, 110, 232, .25); color: white; font-weight: 700; transition: transform 160ms ease, box-shadow 160ms ease; }
    .primary-action button:hover { transform: translateY(-1px); box-shadow: 0 14px 28px rgba(10, 110, 232, .32); }
    .secondary-action button { min-height: 44px; border: 1px solid rgba(10, 110, 232, .28); border-radius: 14px; background: var(--glass-strong); color: #0758bd; font-weight: 650; }
    .gradio-container label, .gradio-container .block-title { color: var(--ink) !important; font-weight: 650 !important; }
    .gradio-container input, .gradio-container textarea, .gradio-container .wrap { border-color: rgba(72, 104, 143, .22) !important; background: rgba(255,255,255,.62) !important; }
    .gradio-container button:focus-visible, .gradio-container input:focus-visible, .gradio-container textarea:focus-visible { outline: 3px solid rgba(10, 110, 232, .52) !important; outline-offset: 2px; }
    .output-status textarea { color: var(--text-primary) !important; }
    @media (max-width: 760px) { .app-shell { padding: 18px 12px 32px; } .hero { padding: 24px 20px; border-radius: 22px; } .glass-panel { padding: 18px; border-radius: 20px; } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; animation: none !important; } }
    """


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
        text = "这是一个通用的有声书测试样本。欢迎使用自备模型有声书制作工作台，体验流畅自然的多语种旁白与说书人音色。"
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
    genre_choice: str,
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
        return str(final_flac), f"✅ Completed [{genre_choice.upper()}]! Master audiobook saved to: {final_flac}"
    except Exception as exc:
        return None, f"❌ Failed to generate audiobook: {exc}"


def update_genre_styles(genre: str):
    """Dynamically switch style presets based on genre."""
    if genre == "nonfiction":
        return gr.Dropdown(
            choices=list(NONFICTION_PRESETS.keys()),
            value="nonfiction_business",
            label="Narration Style (Non-Fiction / 商业科普经管)",
        )
    else:
        return gr.Dropdown(
            choices=list(FICTION_PRESETS.keys()),
            value="fiction_storyteller",
            label="Narration Style (Fiction / 虚构小说武侠)",
        )


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
            # 🎙️ Universal EPUB Audiobook Studio (BYOM & Genre-Aware)
            Upload any **EPUB eBook** and generate complete, high-fidelity audiobooks with specialized tuning for **Fiction (小说)** and **Non-Fiction (商业/社科/科普)**.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                epub_input = gr.File(
                    label="Upload EPUB eBook",
                    file_types=[".epub"],
                    type="filepath",
                )

                genre_select = gr.Radio(
                    label="📚 Book Genre (书籍类型)",
                    choices=[
                        ("Fiction (小说 / 故事 / 武侠)", "fiction"),
                        ("Non-Fiction (商业 / 经管 / 历史 / 知识)", "nonfiction"),
                    ],
                    value="fiction",
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
                    label="Narration Style (Fiction / 虚构小说武侠)",
                    choices=list(FICTION_PRESETS.keys()),
                    value="fiction_storyteller",
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
                output_audio = gr.File(label="Download Master Audiobook (.flac / .m4b)")

        # Event triggers
        epub_input.change(fn=inspect_epub, inputs=[epub_input], outputs=[epub_info])
        genre_select.change(fn=update_genre_styles, inputs=[genre_select], outputs=[style_preset])
        engine_select.change(fn=update_speaker_choices, inputs=[engine_select], outputs=[speaker_select])
        preview_btn.click(
            fn=preview_voice,
            inputs=[custom_style, engine_select, speaker_select, style_preset],
            outputs=[preview_audio],
        )
        generate_btn.click(
            fn=generate_audiobook,
            inputs=[
                epub_input,
                genre_select,
                engine_select,
                speaker_select,
                style_preset,
                custom_style,
                max_chars_slider,
            ],
            outputs=[output_audio, status_text],
        )

    return demo


def launch_app(host: str = "127.0.0.1", port: int = 7860):
    demo = create_ui()
    demo.launch(server_name=host, server_port=port, share=False)


if __name__ == "__main__":
    launch_app()
