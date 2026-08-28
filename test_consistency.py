import json
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

from run_shujian_qwen_customvoice import chunk_text, tighten_silences

MODEL_DIR = Path("/Users/hoyinshum/tools/ai/qwen3-tts/Qwen3-TTS-12Hz-1.7B-CustomVoice")
SPEAKER = "Uncle_Fu"

STYLE = (
    "一位四十五至五十五岁的男性说书人。使用标准现代普通话，字正腔圆，清晰区分平翘舌与前后鼻音；"
    "音色低沉浑厚，全程保持高度一致、稳定的说书人声线与音调，不要频繁切换音色。"
    "叙述自然流畅，有向前推进的节奏，语速中等偏快，不拖字，不刻意压慢。"
    "句内停顿短促，句末自然收束，不要加入长时间空白。"
    "每次朗读必须完整说完收到的全部文字，直到最后一个字和标点；不得在段落中途停止。"
    "不要新增、删减、改写任何文字。"
)

device = "mps" if torch.backends.mps.is_available() else "cpu"
dtype = torch.bfloat16 if device == "mps" else torch.float32
print("Loading model...")
model = Qwen3TTSModel.from_pretrained(str(MODEL_DIR), device_map=device, dtype=dtype)

manifest = json.load(open("/Users/hoyinshum/tools/ai/qwen3-tts/shujian_qwen_customvoice_dynamic2_上/manifest.json"))
chunks = [c["characters"] for c in manifest["chunks"][:3]]

# Read actual chunk text
source_text = Path("/Users/hoyinshum/tools/ai/qwen3-tts/書劍恩仇錄上_全文.txt").read_text(encoding="utf-8")
chunk_texts = chunk_text(source_text)[:3]

out_dir = Path("/Users/hoyinshum/tools/ai/qwen3-tts/consistency_test")
out_dir.mkdir(exist_ok=True)

for i, text in enumerate(chunk_texts, 1):
    print(f"Generating test chunk {i} ({len(text)} chars)...")
    torch.manual_seed(42)  # Reset seed for acoustic baseline consistency
    wavs, sr = model.generate_custom_voice(
        text=text,
        language="Chinese",
        speaker=SPEAKER,
        instruct=STYLE,
        do_sample=True,
        top_p=0.80,
        temperature=0.30,
        repetition_penalty=1.05,
        max_new_tokens=1200,
    )
    audio = tighten_silences(np.asarray(wavs[0]), sr)
    # Peak normalize to -1.0 dB
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.90
    out_path = out_dir / f"consistent_{i:02d}.wav"
    sf.write(out_path, audio, sr, subtype="PCM_16")
    print(f"Saved {out_path} duration={len(audio) / sr:.2f}s peak={np.max(np.abs(audio)):.2f}")

print("Done! Test audio files generated in", out_dir)
