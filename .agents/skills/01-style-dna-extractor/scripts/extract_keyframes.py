#!/usr/bin/env python3
"""
Extract word-level transcripts, scene boundaries, and 3x3 keyframe contact sheets
from reference videos for Style DNA training.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_cmd(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture,
        encoding="utf-8",
        errors="replace",
    )


def probe_video(video_path: Path) -> dict[str, Any]:
    res = run_cmd(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
    )
    data = json.loads(res.stdout)
    duration = float(data["format"]["duration"])
    v_stream = next(s for s in data["streams"] if s["codec_type"] == "video")
    num, den = v_stream.get("r_frame_rate", "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    return {
        "duration_s": duration,
        "duration_ms": int(round(duration * 1000)),
        "fps": fps,
        "width": int(v_stream["width"]),
        "height": int(v_stream["height"]),
    }


def transcribe_video(video_path: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = out_dir / "transcript.json"

    words: list[dict[str, Any]] = []
    engine = "none"

    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(video_path), word_timestamps=True)
        for seg in segments:
            for w in getattr(seg, "words", []) or []:
                words.append(
                    {
                        "word": w.word.strip(),
                        "start_ms": int(round(w.start * 1000)),
                        "end_ms": int(round(w.end * 1000)),
                    }
                )
        engine = "faster-whisper"
    except ImportError:
        try:
            import whisper  # type: ignore

            model = whisper.load_model("base")
            result = model.transcribe(str(video_path), word_timestamps=True)
            for seg in result.get("segments", []):
                for w in seg.get("words", []):
                    words.append(
                        {
                            "word": w["word"].strip(),
                            "start_ms": int(round(w["start"] * 1000)),
                            "end_ms": int(round(w["end"] * 1000)),
                        }
                    )
            engine = "openai-whisper"
        except ImportError:
            print(
                "Warning: Neither faster-whisper nor openai-whisper is installed. "
                "Writing empty placeholder transcript.json.",
                file=sys.stderr,
            )

    payload = {
        "video": str(video_path),
        "engine": engine,
        "words": words,
    }
    transcript_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return transcript_path


def detect_scene_timestamps(
    video_path: Path, threshold: float, duration_s: float, min_len_s: float = 0.6
) -> list[tuple[float, float]]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(video_path),
        "-filter:v",
        f"select='gt(scene,{threshold})',showinfo",
        "-f",
        "null",
        "-",
    ]
    res = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    cuts: list[float] = [0.0]
    for line in res.stderr.splitlines():
        if "pts_time:" in line:
            for token in line.split():
                if token.startswith("pts_time:"):
                    try:
                        t = float(token.split(":", 1)[1])
                        if t - cuts[-1] >= min_len_s and duration_s - t >= min_len_s:
                            cuts.append(t)
                    except ValueError:
                        pass
    cuts.append(duration_s)
    return [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]


def words_in_range(transcript_path: Path, start_ms: int, end_ms: int) -> str:
    if not transcript_path.exists():
        return ""
    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    matched = [
        w["word"]
        for w in data.get("words", [])
        if w["end_ms"] >= start_ms and w["start_ms"] <= end_ms
    ]
    return " ".join(matched).strip()


def export_contact_sheet(
    video_path: Path, start_s: float, end_s: float, out_png: Path
) -> None:
    span = max(end_s - start_s, 0.2)
    sample_fps = 9.0 / span
    vf = (
        f"fps={sample_fps:.6f},"
        "scale=360:-1,"
        "tile=3x3:padding=6:margin=6:color=0x111111"
    )
    run_cmd(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start_s:.3f}",
            "-to",
            f"{end_s:.3f}",
            "-i",
            str(video_path),
            "-vf",
            vf,
            "-frames:v",
            "1",
            str(out_png),
        ]
    )


def extract_scenes(video_path: Path, out_dir: Path, threshold: float) -> None:
    info = probe_video(video_path)
    segments = detect_scene_timestamps(video_path, threshold, info["duration_s"])
    transcript_path = out_dir / "transcript.json"

    scenes_dir = out_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    for idx, (start_s, end_s) in enumerate(segments, start=1):
        seg_dir = scenes_dir / f"seg_{idx:03d}"
        seg_dir.mkdir(parents=True, exist_ok=True)

        start_ms = int(round(start_s * 1000))
        end_ms = int(round(end_s * 1000))
        duration_ms = max(end_ms - start_ms, 1)
        duration_frames_60 = max(1, int(math.ceil((duration_ms / 1000.0) * 60.0)))

        contact_png = seg_dir / "keyframes.png"
        export_contact_sheet(video_path, start_s, end_s, contact_png)

        metadata = {
            "source_video": video_path.name,
            "segment_index": idx,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_ms": duration_ms,
            "duration_frames_60fps": duration_frames_60,
            "principle_id": "UNCLASSIFIED",
            "camera_motion": "UNCLASSIFIED",
            "camera_bound_texture": True,
            "trigger_phrase": words_in_range(transcript_path, start_ms, end_ms),
            "keyframes_sheet": str(contact_png),
        }
        (seg_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

    print(f"Extracted {len(segments)} scene segments into {scenes_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Style DNA keyframes and transcripts.")
    parser.add_argument("--video", required=True, help="Path to reference MP4 video.")
    parser.add_argument("--out-dir", required=True, help="Output directory for this video.")
    parser.add_argument(
        "--mode",
        choices=["transcribe", "scenes", "all"],
        default="all",
        help="Pipeline step to run.",
    )
    parser.add_argument(
        "--scene-threshold",
        type=float,
        default=0.28,
        help="FFmpeg scene change detection threshold (0.1 - 0.6).",
    )
    args = parser.parse_args()

    video_path = Path(args.video).resolve()
    out_dir = Path(args.out_dir).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if args.mode in ("transcribe", "all"):
        path = transcribe_video(video_path, out_dir)
        print(f"Wrote transcript to {path}")
    if args.mode in ("scenes", "all"):
        extract_scenes(video_path, out_dir, args.scene_threshold)


if __name__ == "__main__":
    main()
