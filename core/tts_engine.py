"""TTS Engine interface for Qwen3-TTS with silence tightening and quality auditing."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
from qwen_tts import Qwen3TTSModel

from .config import (
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_MODEL_DIR,
    DEFAULT_SPEAKER,
    MAX_SILENCE_SECONDS,
    MIN_SECONDS_PER_CHAR,
    STYLE_PRESETS,
)


def tighten_silences(
    audio: np.ndarray, sr: int, threshold: float = 0.008, max_silence_s: float = MAX_SILENCE_SECONDS
) -> np.ndarray:
    """Keep natural punctuation pauses but cap generated dead air at max_silence_s."""
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)

    window = max(1, int(sr * 0.05))  # 50ms window
    windows = [audio[i : i + window] for i in range(0, len(audio), window)]
    active = [np.sqrt(np.mean(np.square(w))) >= threshold for w in windows]

    out: list[np.ndarray] = []
    i = 0
    max_silent_windows = max(1, int(max_silence_s / 0.05))

    while i < len(windows):
        if active[i]:
            out.append(windows[i])
            i += 1
            continue
        j = i
        while j < len(windows) and not active[j]:
            j += 1
        # Keep only a short natural pause
        out.extend(windows[i : min(j, i + max_silent_windows)])
        i = j

    return np.concatenate(out) if out else audio


def audit_audio(audio: np.ndarray, sr: int, expected_chars: Optional[int] = None) -> dict:
    """Verify audio integrity, loudness, and non-truncation."""
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)

    duration_seconds = len(audio) / sr
    if duration_seconds < 0.3 or not np.isfinite(audio).all():
        raise RuntimeError("Invalid, NaN/Inf, or too-short audio")

    peak = float(np.max(np.abs(audio)))
    if peak < 0.002:
        raise RuntimeError("Effectively silent audio output")

    # Anti-truncation duration audit
    if expected_chars is not None and duration_seconds < max(1.5, expected_chars * MIN_SECONDS_PER_CHAR):
        raise RuntimeError(
            f"Truncated narration detected: {duration_seconds:.2f}s for {expected_chars} characters (expected >= {expected_chars * MIN_SECONDS_PER_CHAR:.2f}s)"
        )

    tail = audio[-min(len(audio), int(sr * 0.25)) :]
    tail_rms = float(np.sqrt(np.mean(np.square(tail))))
    if tail_rms > 0.20:
        raise RuntimeError(f"Unexpectedly loud tail noise: {tail_rms:.3f}")

    return {
        "sample_rate": int(sr),
        "samples": int(len(audio)),
        "duration_seconds": round(duration_seconds, 3),
        "peak": round(peak, 4),
        "tail_rms": round(tail_rms, 4),
    }


class TTSEngine:
    """Wrapper around Qwen3TTSModel for reproducible, high-quality narration generation."""

    def __init__(self, model_dir: Path | str = DEFAULT_MODEL_DIR, device: Optional[str] = None):
        self.model_dir = Path(model_dir)
        if not self.model_dir.is_dir():
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")

        if device is None:
            self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            self.device = device

        self.dtype = torch.bfloat16 if self.device == "mps" else torch.float32
        print(f"[TTSEngine] Loading Qwen3-TTS from {self.model_dir} on {self.device} ({self.dtype})...")
        self.model = Qwen3TTSModel.from_pretrained(str(self.model_dir), device_map=self.device, dtype=self.dtype)
        print("[TTSEngine] Model loaded successfully.")

    def synthesize(
        self,
        text: str,
        speaker: str = DEFAULT_SPEAKER,
        instruct: Optional[str] = None,
        style_preset: str = "storyteller",
        seed: Optional[int] = 42,
        temperature: float = 0.62,
        top_p: float = 0.88,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        normalize_peak: bool = True,
    ) -> Tuple[np.ndarray, int, dict]:
        """Synthesize text to audio waveform with silence tightening, auditing, and normalization."""
        if instruct is None:
            instruct = STYLE_PRESETS.get(style_preset, STYLE_PRESETS["storyteller"])

        if seed is not None:
            torch.manual_seed(seed)

        wavs, sr = self.model.generate_custom_voice(
            text=text,
            language="Chinese",
            speaker=speaker,
            instruct=instruct,
            do_sample=True,
            top_p=top_p,
            temperature=temperature,
            repetition_penalty=1.07,
            max_new_tokens=max_new_tokens,
        )

        raw_audio = np.asarray(wavs[0])
        processed = tighten_silences(raw_audio, sr)

        if normalize_peak:
            peak = float(np.max(np.abs(processed)))
            if peak > 0:
                processed = (processed / peak * 0.90).astype(np.float32)

        audit = audit_audio(processed, sr, expected_chars=len(text))
        return processed, sr, audit
