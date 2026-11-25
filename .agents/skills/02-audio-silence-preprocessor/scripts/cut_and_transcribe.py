#!/usr/bin/env python3
"""
Cut dead-air silences from raw talking-head video with exact millisecond padding,
concatenate into a locked 60fps 1080x1920 master A-roll, and generate
millisecond + frame-accurate word timestamps.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SILENCE_START_RE = re.compile(r"silence_start:\s*([0-9.]+)")
SILENCE_END_RE = re.compile(r"silence_end:\s*([0-9.]+)")


def probe_duration(video_path: Path) -> float:
    res = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return float(res.stdout.strip())


def detect_silences(
    video_path: Path, noise_db: str, min_silence_s: float
) -> list[tuple[float, float]]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(video_path),
        "-af",
        f"silencedetect=noise={noise_db}:d={min_silence_s:.3f}",
        "-f",
        "null",
        "-",
    ]
    res = subprocess.run(
        cmd, text=True, capture_output=True, encoding="utf-8", errors="replace"
    )
    silences: list[tuple[float, float]] = []
    current_start: float | None = None
    for line in res.stderr.splitlines():
        m_start = SILENCE_START_RE.search(line)
        if m_start:
            current_start = float(m_start.group(1))
            continue
        m_end = SILENCE_END_RE.search(line)
        if m_end and current_start is not None:
            silences.append((current_start, float(m_end.group(1))))
            current_start = None

    if current_start is not None:
        silences.append((current_start, probe_duration(video_path)))
    return silences


def compute_speech_intervals(
    duration_s: float, silences: list[tuple[float, float]], padding_s: float
) -> list[tuple[float, float]]:
    if not silences:
        return [(0.0, duration_s)]

    raw_speech: list[tuple[float, float]] = []
    cursor = 0.0
    for s_start, s_end in silences:
        if s_start > cursor:
            raw_speech.append((cursor, s_start))
        cursor = max(cursor, s_end)
    if cursor < duration_s:
        raw_speech.append((cursor, duration_s))

    padded: list[tuple[float, float]] = []
    for start, end in raw_speech:
        p_start = max(0.0, start - padding_s)
        p_end = min(duration_s, end + padding_s)
        if p_end - p_start < 0.04:
            continue
        if padded and p_start <= padded[-1][1]:
            padded[-1] = (padded[-1][0], max(padded[-1][1], p_end))
        else:
            padded.append((p_start, p_end))

    return padded or [(0.0, duration_s)]


def render_trimmed_aroll(
    input_video: Path,
    output_video: Path,
    intervals: list[tuple[float, float]],
    fps: int,
    width: int,
    height: int,
) -> None:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        seg_files: list[Path] = []
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},fps={fps},format=yuv420p"
        )
        for idx, (start, end) in enumerate(intervals):
            seg_path = tmp_dir / f"seg_{idx:04d}.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-ss",
                    f"{start:.4f}",
                    "-to",
                    f"{end:.4f}",
                    "-i",
                    str(input_video),
                    "-vf",
                    vf,
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "16",
                    "-c:a",
                    "aac",
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    "-b:a",
                    "192k",
                    str(seg_path),
                ],
                check=True,
            )
            seg_files.append(seg_path)

        concat_list = tmp_dir / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{p.as_posix()}'" for p in seg_files),
            encoding="utf-8",
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_video),
            ],
            check=True,
        )


def align_words(
    video_path: Path, fps: int, language: str = "auto", model_size: str = "base"
) -> list[dict[str, Any]]:
    words: list[dict[str, Any]] = []
    lang_arg = None if language == "auto" else language

    def add_word(text: str, start_s: float, end_s: float) -> None:
        clean = text.strip()
        if not clean:
            return
        start_ms = int(round(start_s * 1000))
        end_ms = max(start_ms + 1, int(round(end_s * 1000)))
        words.append(
            {
                "word": clean,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "start_frame": int(round((start_ms / 1000.0) * fps)),
                "end_frame": max(
                    int(round((start_ms / 1000.0) * fps)) + 1,
                    int(round((end_ms / 1000.0) * fps)),
                ),
            }
        )

    # Prefer WhisperX forced phoneme alignment, then faster-whisper, then openai-whisper.
    try:
        import whisperx  # type: ignore

        device = "cpu"
        audio = whisperx.load_audio(str(video_path))
        model = whisperx.load_model(
            model_size, device, compute_type="int8", language=lang_arg
        )
        result = model.transcribe(audio, batch_size=8, language=lang_arg)
        align_lang = lang_arg or result["language"]
        align_model, metadata = whisperx.load_align_model(
            language_code=align_lang, device=device
        )
        aligned = whisperx.align(
            result["segments"], align_model, metadata, audio, device
        )
        for seg in aligned.get("segments", []):
            for w in seg.get("words", []):
                if "start" in w and "end" in w:
                    add_word(w["word"], float(w["start"]), float(w["end"]))
        return words
    except ImportError:
        pass

    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(
            str(video_path), word_timestamps=True, language=lang_arg
        )
        for seg in segments:
            for w in getattr(seg, "words", []) or []:
                add_word(w.word, float(w.start), float(w.end))
        return words
    except ImportError:
        pass

    try:
        import whisper  # type: ignore

        model = whisper.load_model(model_size)
        kwargs: dict[str, Any] = {"word_timestamps": True}
        if lang_arg:
            kwargs["language"] = lang_arg
        result = model.transcribe(str(video_path), **kwargs)
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                add_word(w["word"], float(w["start"]), float(w["end"]))
        return words
    except ImportError:
        print(
            "Warning: No Whisper backend (whisperx, faster-whisper, whisper) installed. "
            "Writing empty transcript_ms.json.",
            file=sys.stderr,
        )
        return []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove silences with 30ms padding and generate millisecond word alignment."
    )
    parser.add_argument("--input", required=True, help="Raw input A-roll MP4 path.")
    parser.add_argument(
        "--output-video", default="build/aroll_trimmed.mp4", help="Trimmed MP4 output."
    )
    parser.add_argument(
        "--output-transcript",
        default="build/transcript_ms.json",
        help="Millisecond word transcript JSON output.",
    )
    parser.add_argument("--silence-threshold", default="-38dB")
    parser.add_argument("--min-silence-ms", type=int, default=180)
    parser.add_argument("--padding-ms", type=int, default=30)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--language", default="auto", help="ISO language code (e.g., mr, en, auto).")
    parser.add_argument("--model", default="base", help="Whisper model name (e.g., base, large-v3).")
    parser.add_argument("--skip-transcribe", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    out_video = Path(args.output_video).resolve()
    out_transcript = Path(args.output_transcript).resolve()
    out_transcript.parent.mkdir(parents=True, exist_ok=True)

    duration_s = probe_duration(input_path)
    silences = detect_silences(
        input_path, args.silence_threshold, args.min_silence_ms / 1000.0
    )
    intervals = compute_speech_intervals(
        duration_s, silences, args.padding_ms / 1000.0
    )
    print(f"Detected {len(silences)} silences -> kept {len(intervals)} padded speech intervals.")

    render_trimmed_aroll(
        input_path, out_video, intervals, args.fps, args.width, args.height
    )
    print(f"Rendered trimmed A-roll: {out_video}")

    words = (
        []
        if args.skip_transcribe
        else align_words(out_video, args.fps, args.language, args.model)
    )
    out_transcript.write_text(json.dumps(words, indent=2), encoding="utf-8")
    print(f"Wrote {len(words)} aligned words to {out_transcript}")


if __name__ == "__main__":
    main()
