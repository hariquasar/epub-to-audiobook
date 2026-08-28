"""Audiobook assembly pipeline and manifest manager."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional

import soundfile as sf

from .config import DEFAULT_MAX_CHARS, DEFAULT_SPEAKER, STYLE_PRESETS
from .epub_parser import parse_epub
from .text_processor import chunk_text, to_simplified
from .tts_engine import TTSEngine


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class AudiobookBuilder:
    """End-to-end pipeline to generate complete audiobooks from EPUB or plain text."""

    def __init__(
        self,
        output_dir: Path | str,
        engine: Optional[TTSEngine] = None,
        speaker: str = DEFAULT_SPEAKER,
        style_preset: str = "storyteller",
        custom_style: Optional[str] = None,
        max_chars: int = DEFAULT_MAX_CHARS,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir = self.output_dir / "chunks"
        self.chunks_dir.mkdir(exist_ok=True)

        self.engine = engine
        self.speaker = speaker
        self.style = custom_style or STYLE_PRESETS.get(style_preset, STYLE_PRESETS["storyteller"])
        self.max_chars = max_chars

    def build_from_epub(
        self,
        epub_path: Path | str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Path:
        """Process an EPUB file into a full audiobook with chapter checkpoints."""
        parsed_book = parse_epub(epub_path)
        print(
            f"[AudiobookBuilder] Parsed '{parsed_book.title}' by {parsed_book.author} ({len(parsed_book.chapters)} chapters, {parsed_book.total_characters} characters)"
        )

        # Prepare full text chunks per chapter
        all_chunks: List[dict] = []
        global_chunk_idx = 1

        for chapter in parsed_book.chapters:
            simplified_text = to_simplified(chapter.text)
            chunks = chunk_text(simplified_text, max_chars=self.max_chars)
            for c_text in chunks:
                all_chunks.append(
                    {
                        "index": global_chunk_idx,
                        "chapter_index": chapter.index,
                        "chapter_title": chapter.title,
                        "characters": len(c_text),
                        "text": c_text,
                        "text_sha256": sha256_str(c_text),
                        "audio": f"chunks/{global_chunk_idx:05d}.wav",
                        "status": "pending",
                    }
                )
                global_chunk_idx += 1

        manifest_path = self.output_dir / "manifest.json"
        manifest = {
            "schema": 6,
            "title": parsed_book.title,
            "author": parsed_book.author,
            "source_epub": str(epub_path),
            "speaker": self.speaker,
            "style": self.style,
            "style_sha256": sha256_str(self.style),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_chunks": len(all_chunks),
            "chunks": all_chunks,
        }

        # Load existing manifest if resuming
        if manifest_path.exists():
            try:
                old_m = json.loads(manifest_path.read_text(encoding="utf-8"))
                if old_m.get("title") == parsed_book.title and len(old_m.get("chunks", [])) == len(all_chunks):
                    # Reuse existing passed chunks
                    manifest = old_m
                    print(f"[AudiobookBuilder] Resuming existing project: {manifest_path}")
            except Exception:
                pass

        self._save_manifest(manifest)

        # Ensure engine is loaded
        if self.engine is None:
            self.engine = TTSEngine()

        total = len(manifest["chunks"])
        print(f"[AudiobookBuilder] Rendering {total} chunks...")

        for entry in manifest["chunks"]:
            idx = entry["index"]
            audio_path = self.output_dir / entry["audio"]
            chunk_text_str = entry["text"]

            if audio_path.exists() and entry.get("status") == "passed":
                print(f"[AudiobookBuilder] SKIP {idx}/{total} (Already completed)")
                if progress_callback:
                    progress_callback(idx, total, f"Skip {idx}/{total}")
                continue

            print(
                f"[AudiobookBuilder] START {idx}/{total} chars={len(chunk_text_str)} [{entry.get('chapter_title', '')}]"
            )
            last_err = None

            for attempt in range(1, 4):
                started = time.monotonic()
                try:
                    audio, sr, audit = self.engine.synthesize(
                        text=chunk_text_str,
                        speaker=self.speaker,
                        instruct=self.style,
                    )
                    tmp = audio_path.with_suffix(".partial.wav")
                    sf.write(tmp, audio, sr, subtype="PCM_16")
                    tmp.replace(audio_path)

                    entry["status"] = "passed"
                    entry["audit"] = audit
                    entry["elapsed_s"] = round(time.monotonic() - started, 2)
                    self._save_manifest(manifest)

                    print(
                        f"[AudiobookBuilder] PASS {idx}/{total} dur={audit['duration_seconds']:.2f}s ({entry['elapsed_s']}s render)"
                    )
                    if progress_callback:
                        progress_callback(idx, total, f"Generated chunk {idx}/{total}")
                    break
                except Exception as exc:
                    last_err = exc
                    tmp = audio_path.with_suffix(".partial.wav")
                    if tmp.exists():
                        tmp.unlink()
                    print(f"[AudiobookBuilder] RETRY {idx}/{total} attempt={attempt}: {exc}")
            else:
                entry["status"] = "failed"
                entry["error"] = str(last_err)
                self._save_manifest(manifest)
                raise RuntimeError(f"Chunk {idx} failed after 3 attempts: {last_err}")

        # Combine into master audiobook FLAC and M4B with chapters
        final_flac = self._combine_flac(manifest)
        final_m4b = self._export_m4b(manifest, final_flac)
        print(f"[AudiobookBuilder] Completed! Master files:\n  FLAC: {final_flac}\n  M4B : {final_m4b}")
        return final_m4b or final_flac

    def _save_manifest(self, manifest: dict) -> None:
        (self.output_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _export_m4b(self, manifest: dict, flac_path: Path) -> Optional[Path]:
        """Generate Apple Books / Audiobookshelf compatible .m4b with chapter markers."""
        import shutil
        import subprocess

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            print("[AudiobookBuilder] FFmpeg not found, skipping M4B chapter export.")
            return None

        # Build chapter timing
        chapters_timing: list[dict] = []
        current_chapter_idx = None
        current_title = ""
        current_start_ms = 0
        running_ms = 0

        for entry in manifest["chunks"]:
            dur_s = entry.get("audit", {}).get("duration_seconds", 0)
            if not dur_s and (self.output_dir / entry["audio"]).exists():
                info = sf.info(str(self.output_dir / entry["audio"]))
                dur_s = info.duration

            dur_ms = int(dur_s * 1000)
            chap_idx = entry.get("chapter_index", 1)
            chap_title = entry.get("chapter_title", f"Chapter {chap_idx}")

            if current_chapter_idx != chap_idx:
                if current_chapter_idx is not None:
                    chapters_timing.append(
                        {
                            "title": current_title,
                            "start": current_start_ms,
                            "end": running_ms,
                        }
                    )
                current_chapter_idx = chap_idx
                current_title = chap_title
                current_start_ms = running_ms

            running_ms += dur_ms

        if current_chapter_idx is not None:
            chapters_timing.append(
                {
                    "title": current_title,
                    "start": current_start_ms,
                    "end": running_ms,
                }
            )

        # Write FFMETADATA1 file
        meta_lines = [
            ";FFMETADATA1",
            f"title={manifest.get('title', 'Audiobook')}",
            f"artist={manifest.get('author', 'Unknown')}",
            f"album={manifest.get('title', 'Audiobook')}",
            "genre=Audiobook",
        ]
        for ch in chapters_timing:
            meta_lines.extend(
                [
                    "[CHAPTER]",
                    "TIMEBASE=1/1000",
                    f"START={ch['start']}",
                    f"END={ch['end']}",
                    f"title={ch['title']}",
                ]
            )

        meta_file = self.output_dir / "metadata.txt"
        meta_file.write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

        m4b_path = self.output_dir / "audiobook.m4b"
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(flac_path),
            "-i",
            str(meta_file),
            "-map_metadata",
            "1",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-f",
            "mp4",
            str(m4b_path),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return m4b_path
        except Exception as exc:
            print(f"[AudiobookBuilder] FFmpeg M4B conversion warning: {exc}")
            return None

    def _combine_flac(self, manifest: dict) -> Path:
        """Combine all passed chunks into a single master FLAC file."""
        combined_path = self.output_dir / "audiobook.flac"
        first_audio = self.output_dir / manifest["chunks"][0]["audio"]

        with sf.SoundFile(str(first_audio), "r") as first:
            with sf.SoundFile(
                str(combined_path),
                "w",
                samplerate=first.samplerate,
                channels=first.channels,
                format="FLAC",
                subtype="PCM_16",
            ) as out:
                for entry in manifest["chunks"]:
                    p = self.output_dir / entry["audio"]
                    with sf.SoundFile(str(p), "r") as part:
                        while True:
                            frames = part.read(65536)
                            if len(frames) == 0:
                                break
                            out.write(frames)

        audit = {
            "title": manifest.get("title", "Audiobook"),
            "total_chunks": len(manifest["chunks"]),
            "audiobook": str(combined_path),
            "size_bytes": combined_path.stat().st_size,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        (self.output_dir / "audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return combined_path
