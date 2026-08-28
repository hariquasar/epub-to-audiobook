"""Bring Your Own Model (BYOM) Multi-Backend TTS Engine Interface.

Supports:
- Local Qwen3-TTS (CustomVoice / VoiceDesign)
- EdgeTTS (High-quality cloud TTS for multi-lingual narration)
- OpenAI-compatible TTS APIs (Kokoro, ElevenLabs, vLLM, standard endpoints)
"""

from __future__ import annotations

import asyncio
import io
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import soundfile as sf
import torch

from .config import (
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_MODEL_DIR,
    DEFAULT_SPEAKER,
    MAX_SILENCE_SECONDS,
    MIN_SECONDS_PER_CHAR,
    STYLE_PRESETS,
)


def tighten_silences(
    audio: np.ndarray,
    sr: int,
    threshold: float = 0.008,
    max_silence_s: float = MAX_SILENCE_SECONDS,
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

    if expected_chars is not None and expected_chars > 0:
        min_expected = max(0.6, expected_chars * MIN_SECONDS_PER_CHAR)
        if duration_seconds < min_expected:
            raise RuntimeError(
                f"Truncated narration detected: {duration_seconds:.2f}s for {expected_chars} characters (expected >= {min_expected:.2f}s)"
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


class BaseTTSEngine(ABC):
    """Abstract base class for all TTS backend models."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        speaker: Optional[str] = None,
        instruct: Optional[str] = None,
        style_preset: str = "storyteller",
        **kwargs,
    ) -> Tuple[np.ndarray, int, dict]:
        """Synthesize text into (waveform, sample_rate, audit_dict)."""
        pass


class QwenTTSEngine(BaseTTSEngine):
    """Local Qwen3-TTS engine on Apple Silicon MPS or CPU."""

    def __init__(self, model_dir: Path | str = DEFAULT_MODEL_DIR, device: Optional[str] = None):
        self.model_dir = Path(model_dir)
        if not self.model_dir.is_dir():
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")

        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        self.dtype = torch.bfloat16 if self.device == "mps" else torch.float32

        print(f"[QwenTTSEngine] Loading model from {self.model_dir} on {self.device} ({self.dtype})...")
        from qwen_tts import Qwen3TTSModel

        self.model = Qwen3TTSModel.from_pretrained(str(self.model_dir), device_map=self.device, dtype=self.dtype)
        print("[QwenTTSEngine] Model loaded.")

    def synthesize(
        self,
        text: str,
        speaker: Optional[str] = None,
        instruct: Optional[str] = None,
        style_preset: str = "storyteller",
        seed: Optional[int] = 42,
        temperature: float = 0.62,
        top_p: float = 0.88,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        normalize_peak: bool = True,
        **kwargs,
    ) -> Tuple[np.ndarray, int, dict]:
        spk = speaker or DEFAULT_SPEAKER
        ins = instruct or STYLE_PRESETS.get(style_preset, STYLE_PRESETS["storyteller"])

        if seed is not None:
            torch.manual_seed(seed)

        wavs, sr = self.model.generate_custom_voice(
            text=text,
            language="Chinese",
            speaker=spk,
            instruct=ins,
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


class EdgeTTSEngine(BaseTTSEngine):
    """Cloud TTS Engine powered by Microsoft Edge Voices."""

    def __init__(self, voice: str = "zh-CN-YunxiNeural"):
        self.default_voice = voice

    def synthesize(
        self,
        text: str,
        speaker: Optional[str] = None,
        rate: str = "+0%",
        volume: str = "+0%",
        **kwargs,
    ) -> Tuple[np.ndarray, int, dict]:
        import edge_tts

        voice = speaker or self.default_voice

        async def _generate():
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            buffer.seek(0)
            return buffer

        loop = asyncio.new_event_loop()
        buf = loop.run_until_complete(_generate())
        loop.close()

        data, sr = sf.read(buf, always_2d=False)
        processed = tighten_silences(np.asarray(data), sr)
        peak = float(np.max(np.abs(processed)))
        if peak > 0:
            processed = (processed / peak * 0.90).astype(np.float32)

        audit = audit_audio(processed, sr, expected_chars=len(text))
        return processed, sr, audit


def create_tts_engine(engine_type: str = "qwen3", **kwargs) -> BaseTTSEngine:
    """Factory to instantiate any supported TTS backend."""
    engine_type = engine_type.lower()
    if engine_type in ("qwen3", "qwen", "customvoice"):
        return QwenTTSEngine(**kwargs)
    elif engine_type in ("edge", "edge-tts", "cloud"):
        return EdgeTTSEngine(**kwargs)
    else:
        raise ValueError(f"Unknown TTS engine type: '{engine_type}'. Supported: 'qwen3', 'edge'")


# Backward-compatible alias
TTSEngine = QwenTTSEngine
