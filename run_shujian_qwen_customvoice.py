#!/usr/bin/env python3
"""Resumable renderer for Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice.

Creates an audiobook from a source UTF-8 text without changing its text: each
chunk is an exact substring and concatenating its chunks restores the source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

MODEL_DIR = Path("/Users/hoyinshum/tools/ai/qwen3-tts/Qwen3-TTS-12Hz-1.7B-CustomVoice")
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "Uncle_Fu"
# Never split inside a sentence. Smaller batches make generation progress
# visible and resumable without creating artificial sentence seams.
MAX_CHARS = 200
BREAK_RE = re.compile(r"(?<=[。！？；…])")
# Sources are converted to Simplified Chinese before this renderer is run.
# The model reads source text directly; there is deliberately no per-character
# pronunciation override or Traditional-to-Simplified conversion layer here.

STYLE = (
    "一位四十五至五十五岁的男性说书人。使用标准现代普通话，字正腔圆，清晰区分平翘舌与前后鼻音；"
    "全程按普通话音系与声调发音，不带粤语口音、港式普通话韵律或其他地方口音，不使用粤语词汇或语气助词。"
    "低沉男中音，胸腔共鸣稳定，音色浑厚、带少量自然砂砾感；沉稳，有人情味，有江湖故事感。"
    "普通叙述要自然流畅、有向前推进的节奏，语速中等偏快，不拖字，不刻意压慢，也不平板。"
    "交代场景和人物时清楚稳健；打斗、危急、秘密揭晓、感叹和直接引语时可以明显增强节奏、重音、音高和情绪，"
    "但保持自然，不喊叫，不用戏曲腔。直接引语可模仿角色；引语结束后回到有推进力的低沉旁白。"
    "句内停顿短促，句末自然收束；不要加入长时间沉默或戏剧性空白。"
    "每次朗读必须完整说完收到的全部文字，直到最后一个字和标点；不得在段落中途停止。"
    "不要新增、删减、改写任何文字。"
)


def rendered_text(source_text: str) -> str:
    """The source is already Simplified Chinese; pass it to Qwen unchanged."""
    return source_text


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def split_sentences(text: str) -> list[str]:
    """Split text into sentence units keeping sentence terminators and trailing quotes together."""
    pattern = re.compile(r'([^。！？；…\n]*[。！？；…\n]+[”』」’\'"]*)')
    parts = pattern.findall(text)
    matched_len = sum(len(p) for p in parts)
    if matched_len < len(text):
        remainder = text[matched_len:]
        if remainder:
            parts.append(remainder)
    return parts


def chunk_text(text: str) -> list[str]:
    """Build bounded chunks without splitting inside sentences unless a single sentence exceeds MAX_CHARS."""
    sentences = split_sentences(text)
    chunks: list[str] = []
    current = ""
    for s in sentences:
        if not s:
            continue
        # If adding this complete sentence fits within MAX_CHARS, group it
        if len(current) + len(s) <= MAX_CHARS:
            current += s
            continue

        # Flush current chunk before handling the new sentence
        if current:
            chunks.append(current)
            current = ""

        # If the sentence alone fits within MAX_CHARS, start current with it
        if len(s) <= MAX_CHARS:
            current = s
            continue

        # Only when an individual sentence exceeds MAX_CHARS, split at clause punctuation
        clauses = re.findall(r'([^，、：]*[，、：]+[”』」’\'"]*)', s)
        clause_len = sum(len(c) for c in clauses)
        if clause_len < len(s):
            rem = s[clause_len:]
            if rem:
                clauses.append(rem)

        for c in clauses:
            if not c:
                continue
            if len(current) + len(c) <= MAX_CHARS:
                current += c
            else:
                if current:
                    chunks.append(current)
                    current = ""
                if len(c) <= MAX_CHARS:
                    current = c
                else:
                    chunks.append(c)

    if current:
        chunks.append(current)
    assert "".join(chunks) == text, "Concatenation of chunks must restore the exact original text"
    return chunks


def new_manifest(source: Path, project: Path) -> tuple[dict, list[str]]:
    text = source.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    m = {
        "schema": 5,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source), "source_sha256": sha256(source),
        "source_characters": len(text), "model": MODEL_ID, "speaker": SPEAKER,
        "style_specification": STYLE, "style_sha256": hashlib.sha256(STYLE.encode()).hexdigest(), "max_chars": MAX_CHARS,
        "chunks": [{"index": i, "characters": len(c),
                    "text_sha256": hashlib.sha256(c.encode()).hexdigest(),
                    "rendered_text_sha256": hashlib.sha256(rendered_text(c).encode()).hexdigest(),
                    "audio": f"chunks/{i:05d}.wav", "status": "pending"}
                   for i, c in enumerate(chunks, 1)],
    }
    project.mkdir(parents=True, exist_ok=True)
    (project / "chunks").mkdir(exist_ok=True)
    save_manifest(project, m)
    return m, chunks


def save_manifest(project: Path, m: dict) -> None:
    (project / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def open_project(source: Path, project: Path) -> tuple[dict, list[str]]:
    manifest_path = project / "manifest.json"
    if not manifest_path.exists():
        return new_manifest(source, project)
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    if m.get("schema") != 5:
        raise SystemExit("Existing project was generated by a different pipeline; choose a new output folder.")
    if m.get("style_sha256") != hashlib.sha256(STYLE.encode()).hexdigest():
        raise SystemExit("Narration style differs from the manifest; choose a new output folder to avoid mixing voices.")
    chunks = chunk_text(source.read_text(encoding="utf-8"))
    if m["source_sha256"] != sha256(source) or len(chunks) != len(m["chunks"]):
        raise SystemExit("Source differs from manifest; refusing to mix editions.")
    return m, chunks


def tighten_silences(audio: np.ndarray, sr: int, threshold: float = 0.008) -> np.ndarray:
    """Keep natural punctuation pauses but cap generated dead air at 0.30 s."""
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)
    window = max(1, int(sr * 0.05))
    windows = [audio[i : i + window] for i in range(0, len(audio), window)]
    active = [np.sqrt(np.mean(np.square(w))) >= threshold for w in windows]
    out: list[np.ndarray] = []
    i = 0
    max_silent_windows = 6  # 0.30 seconds
    while i < len(windows):
        if active[i]:
            out.append(windows[i])
            i += 1
            continue
        j = i
        while j < len(windows) and not active[j]:
            j += 1
        # Keep only a short natural pause, including at the beginning/end.
        out.extend(windows[i : min(j, i + max_silent_windows)])
        i = j
    return np.concatenate(out) if out else audio


def audit_wav(path: Path, expected_chars: int | None = None) -> dict:
    audio, sr = sf.read(path, always_2d=False)
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)
    if len(audio) < sr // 3 or not np.isfinite(audio).all():
        raise RuntimeError("invalid or too-short audio")
    peak = float(np.max(np.abs(audio)))
    if peak < 0.002:
        raise RuntimeError("effectively silent audio")
    # A Chinese narration normally needs at least ~0.14 seconds per source
    # character. A shorter result almost always means model early termination.
    duration_seconds = len(audio) / sr
    if expected_chars is not None and duration_seconds < max(1.5, expected_chars * 0.14):
        raise RuntimeError(
            f"truncated narration: {duration_seconds:.2f}s for {expected_chars} characters"
        )
    tail = audio[-min(len(audio), int(sr * .25)):]
    tail_rms = float(np.sqrt(np.mean(np.square(tail))))
    if tail_rms > .20:
        raise RuntimeError(f"unexpectedly loud tail: {tail_rms:.3f}")
    return {"sample_rate": int(sr), "samples": int(len(audio)), "duration_seconds": len(audio)/sr, "peak": peak, "tail_rms": tail_rms}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("project")
    ap.add_argument("--prepare-only", action="store_true")
    ap.add_argument("--approved-audition", action="store_true")
    args = ap.parse_args()
    source, project = Path(args.source), Path(args.project)
    m, chunks = open_project(source, project)
    if args.prepare_only:
        print(f"PREPARED {project / 'manifest.json'} chunks={len(chunks)}")
        return
    if not args.approved_audition:
        raise SystemExit("Pass --approved-audition after reviewing the audition WAV.")
    if not MODEL_DIR.is_dir():
        raise SystemExit(f"Official model missing: {MODEL_DIR}")
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "mps" else torch.float32
    print(f"LOAD model={MODEL_DIR} device={device} dtype={dtype}", flush=True)
    model = Qwen3TTSModel.from_pretrained(str(MODEL_DIR), device_map=device, dtype=dtype)
    total = len(chunks)
    for entry, source_chunk in zip(m["chunks"], chunks):
        text = rendered_text(source_chunk)
        if entry.get("rendered_text_sha256") != hashlib.sha256(text.encode()).hexdigest():
            raise RuntimeError(f"Rendered text mismatch for chunk {entry['index']}; refusing to mix outputs")
        p = project / entry["audio"]
        if p.exists():
            entry["audit"] = audit_wav(p, expected_chars=len(text))
            entry["status"] = "passed"
            save_manifest(project, m)
            print(f"SKIP {entry['index']}/{total} {p.name}", flush=True)
            continue
        print(f"START {entry['index']}/{total} chars={len(text)}", flush=True)
        last_error: Exception | None = None
        for attempt in range(1, 4):
            started = time.monotonic()
            try:
                wavs, sr = model.generate_custom_voice(
                    text=text, language="Chinese", speaker=SPEAKER, instruct=STYLE,
                    do_sample=True, top_p=.88, temperature=.62,
                    repetition_penalty=1.07, max_new_tokens=700,
                )
                processed = tighten_silences(np.asarray(wavs[0]), sr)
                tmp = p.with_suffix(".partial.wav")
                sf.write(tmp, processed, sr, subtype="PCM_16")
                entry["audit"] = audit_wav(tmp, expected_chars=len(text))
                tmp.replace(p)
                entry["status"] = "passed"
                entry["elapsed_seconds"] = round(time.monotonic() - started, 3)
                save_manifest(project, m)
                print(f"PASS {entry['index']}/{total} attempt={attempt} duration={entry['audit']['duration_seconds']:.2f}s", flush=True)
                break
            except Exception as exc:
                last_error = exc
                tmp = p.with_suffix(".partial.wav")
                if tmp.exists():
                    tmp.unlink()
                print(f"RETRY {entry['index']}/{total} attempt={attempt}: {exc}", flush=True)
        else:
            entry["status"] = "failed"
            entry["error"] = str(last_error)
            save_manifest(project, m)
            raise RuntimeError(f"Chunk {entry['index']} failed after 3 attempts: {last_error}")
    audit = {"source_sha256": m["source_sha256"], "total_chunks": total,
             "passed_chunks": sum(x["status"] == "passed" for x in m["chunks"]),
             "generated_duration_seconds": round(sum(x.get("audit", {}).get("duration_seconds", 0) for x in m["chunks"]), 3)}
    if audit["passed_chunks"] != total:
        raise RuntimeError("Refusing to combine an incomplete audiobook")
    combined = project / "audiobook.flac"
    with sf.SoundFile(project / m["chunks"][0]["audio"], "r") as first:
        with sf.SoundFile(combined, "w", samplerate=first.samplerate, channels=first.channels, format="FLAC", subtype="PCM_16") as out:
            for entry in m["chunks"]:
                with sf.SoundFile(project / entry["audio"], "r") as part:
                    if part.samplerate != out.samplerate or part.channels != out.channels:
                        raise RuntimeError(f"Incompatible chunk audio: {entry['audio']}")
                    while True:
                        frames = part.read(65536)
                        if len(frames) == 0:
                            break
                        out.write(frames)
    audit["audiobook"] = str(combined)
    audit["audiobook_bytes"] = combined.stat().st_size
    (project / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"COMPLETE {combined} chunks={audit['passed_chunks']} duration={audit['generated_duration_seconds']:.2f}s", flush=True)

if __name__ == "__main__":
    main()
