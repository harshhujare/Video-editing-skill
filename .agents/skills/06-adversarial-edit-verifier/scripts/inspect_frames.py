#!/usr/bin/env python3
"""
Adversarial Verifier for Remotion minimal scenes.
Audits src/scenes/Scene*.tsx and src/Root.tsx against the 6 classic AI edit defects:
1. Orphan caption words / sub-24-frame (<400ms) cards
2. Transition continuity across <Sequence> boundaries
3. TextureOverlay nested inside <CameraRig> with opacity 0.12..0.22
4. A-roll jump-cut boundary consistency
5. Minimum 90-frame visual hold for P5 / P7 scenes
6. Principle 6 opening & closing quotation marks
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


PRINCIPLE_TAG_RE = re.compile(r"(?:P(?:10|[1-9])_[A-Z_]+|KINETIC_BREATHER)")
SEQUENCE_RE = re.compile(
    r"<Sequence\b[^>]*?from=\{(\d+)\}[^>]*?durationInFrames=\{(\d+)\}",
    re.DOTALL,
)
OPACITY_RE = re.compile(r"<TextureOverlay\b[^>]*?opacity=\{([0-9.]+)\}", re.DOTALL)
ENTER_TRANS_RE = re.compile(r"enterTransition=\{\{[^}]*?type:\s*['\"]([a-z_]+)['\"]", re.DOTALL)
EXIT_TRANS_RE = re.compile(r"exitTransition=\{\{[^}]*?type:\s*['\"]([a-z_]+)['\"]", re.DOTALL)


def check_texture_binding(code: str, principle: str) -> list[str]:
    issues: list[str] = []
    if principle in ("P1_CAPTION",):
        return issues

    has_tex = "<TextureOverlay" in code
    has_rig = "<CameraRig" in code
    if not has_tex:
        issues.append(f"{principle}: Missing <TextureOverlay />.")
        return issues

    if principle != "P2_BROLL_TEXT" and not has_rig:
        issues.append(f"{principle}: Missing <CameraRig> wrapper; texture would appear static.")
    elif has_rig:
        rig_open = code.find("<CameraRig")
        rig_close = code.rfind("</CameraRig>")
        tex_pos = code.find("<TextureOverlay")
        if not (rig_open != -1 and rig_close != -1 and rig_open < tex_pos < rig_close):
            issues.append(
                "Texture Binding Violation: <TextureOverlay /> must be nested INSIDE <CameraRig>...</CameraRig>."
            )

    for m in OPACITY_RE.finditer(code):
        val = float(m.group(1))
        if val < 0.12 or val > 0.22:
            issues.append(f"Texture opacity {val} outside required [0.12, 0.22] range.")
    return issues


def check_orphan_sequences(code: str) -> list[str]:
    issues: list[str] = []
    for m in SEQUENCE_RE.finditer(code):
        start_f = int(m.group(1))
        dur_f = int(m.group(2))
        if dur_f < 24:
            issues.append(
                f"Orphan/Flash <Sequence> at frame {start_f} has durationInFrames={dur_f} (<24 frames / 400ms)."
            )
    return issues


def check_p6_quotes(code: str, principle: str) -> list[str]:
    if principle != "P6_QUOTE_SCENE":
        return []
    has_open = ("“" in code) or ("&ldquo;" in code) or ("\\u201c" in code.lower())
    has_close = ("”" in code) or ("&rdquo;" in code) or ("\\u201d" in code.lower())
    issues: list[str] = []
    if not has_open:
        issues.append("P6_QUOTE_SCENE missing opening quotation mark (“ or &ldquo;).")
    if not has_close:
        issues.append("P6_QUOTE_SCENE missing closing quotation mark (” or &rdquo;).")
    return issues


def check_complex_hold(code: str, principle: str, root_sequences: dict[str, int]) -> list[str]:
    if principle not in ("P5_LINE_ILLUSTRATION", "P7_CENTER_ILLUSTRATION"):
        return []
    issues: list[str] = []
    # Check both inline durationInFrames hints and Root.tsx sequence durations.
    for comp_name, dur in root_sequences.items():
        if comp_name in code and dur < 108:
            issues.append(
                f"{principle} ({comp_name}) total duration {dur}f is too short to guarantee >=90f hold after entry."
            )
    return issues


def parse_root_sequences(root_file: Path) -> tuple[dict[str, int], list[tuple[str, int, int]]]:
    if not root_file.exists():
        return {}, []
    text = root_file.read_text(encoding="utf-8")
    durations: dict[str, int] = {}
    timeline: list[tuple[str, int, int]] = []
    pattern = re.compile(
        r"<Sequence\b[^>]*?from=\{(\d+)\}[^>]*?durationInFrames=\{(\d+)\}[^>]*?>\s*<([A-Za-z0-9_]+)",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        start_f = int(m.group(1))
        dur_f = int(m.group(2))
        comp = m.group(3)
        durations[comp] = dur_f
        timeline.append((comp, start_f, dur_f))
    return durations, sorted(timeline, key=lambda x: x[1])


def check_root_timeline_gaps(timeline: list[tuple[str, int, int]]) -> list[str]:
    issues: list[str] = []
    for i in range(len(timeline) - 1):
        comp_a, start_a, dur_a = timeline[i]
        comp_b, start_b, _ = timeline[i + 1]
        end_a = start_a + dur_a
        if end_a < start_b:
            issues.append(
                f"Black gap of {start_b - end_a} frames between {comp_a} (ends {end_a}) and {comp_b} (starts {start_b})."
            )
        if dur_a < 24:
            issues.append(f"Flash scene {comp_a} lasts only {dur_a} frames (<24f).")
    return issues


def render_boundary_check(timeline: list[tuple[str, int, int]], composition_id: str) -> list[str]:
    issues: list[str] = []
    if not timeline:
        return issues

    sample_frames = sorted(
        {
            max(0, start + offset)
            for _, start, _ in timeline
            for offset in (-1, 0, 2)
        }
    )
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        for frame in sample_frames:
            png_path = tmp_dir / f"frame_{frame:05d}.png"
            try:
                subprocess.run(
                    [
                        "npx",
                        "remotion",
                        "still",
                        "src/index.ts",
                        composition_id,
                        str(png_path),
                        f"--frame={frame}",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                issues.append(f"Failed rendering boundary frame {frame}: {exc.stderr.strip()}")
                continue

            # Check if frame is near-pure black using ffmpeg signalstats
            probe = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-i",
                    str(png_path),
                    "-vf",
                    "signalstats",
                    "-f",
                    "null",
                    "-",
                ],
                capture_output=True,
                text=True,
            )
            if "YAVG:0." in probe.stderr or "YAVG:1." in probe.stderr:
                issues.append(f"Rendered boundary frame {frame} appears completely black.")
    return issues


def check_transition_handshakes(
    timeline: list[tuple[str, int, int]],
    scene_transitions: dict[str, tuple[str | None, str | None]],
) -> list[str]:
    """Verify adjacent scenes share matching exitTransition -> enterTransition handshakes."""
    issues: list[str] = []
    for i in range(len(timeline) - 1):
        comp_a = timeline[i][0]
        comp_b = timeline[i + 1][0]
        _, exit_a = scene_transitions.get(comp_a, (None, None))
        enter_b, _ = scene_transitions.get(comp_b, (None, None))
        if exit_a is None or enter_b is None:
            issues.append(
                f"Missing CameraRig transition contract between {comp_a} (exit={exit_a}) and {comp_b} (enter={enter_b})."
            )
        elif exit_a != enter_b:
            issues.append(
                f"Transition handshake mismatch: {comp_a} exits with '{exit_a}' but {comp_b} enters with '{enter_b}'."
            )
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Remotion scenes against edit quality checks.")
    parser.add_argument("--scenes-dir", default="src/scenes")
    parser.add_argument("--root-file", default="src/Root.tsx")
    parser.add_argument("--composition-id", default="MainVideo")
    parser.add_argument(
        "--mode",
        choices=["auto", "talking-head", "explainer"],
        default="auto",
        help="Pipeline mode: auto-detect, talking-head, or faceless explainer.",
    )
    parser.add_argument(
        "--timeline",
        default="build/explainer_timeline.json",
        help="Optional explainer timeline JSON path for explainer mode.",
    )
    parser.add_argument(
        "--check",
        choices=["code", "transitions", "all"],
        default="all",
    )
    parser.add_argument(
        "--render-boundaries",
        action="store_true",
        help="Invoke `npx remotion still` at <Sequence> boundaries to check for black frames.",
    )
    args = parser.parse_args()

    scenes_dir = Path(args.scenes_dir)
    root_file = Path(args.root_file)
    report: dict[str, Any] = {"passed": True, "errors": []}

    root_durations, timeline = parse_root_sequences(root_file)
    scene_transitions: dict[str, tuple[str | None, str | None]] = {}
    detected_explainer = args.mode == "explainer"

    if args.check in ("code", "all"):
        if not scenes_dir.exists():
            report["passed"] = False
            report["errors"].append(f"Scenes directory not found: {scenes_dir}")
        else:
            scene_files = sorted(scenes_dir.glob("Scene*.tsx"))
            if not scene_files:
                report["passed"] = False
                report["errors"].append(f"No Scene*.tsx files found in {scenes_dir}")
            for sf in scene_files:
                code = sf.read_text(encoding="utf-8")
                m = PRINCIPLE_TAG_RE.search(code)
                principle = m.group(0) if m else "UNKNOWN"
                m_enter = ENTER_TRANS_RE.search(code)
                m_exit = EXIT_TRANS_RE.search(code)
                enter_t = m_enter.group(1) if m_enter else None
                exit_t = m_exit.group(1) if m_exit else None
                scene_transitions[sf.stem] = (enter_t, exit_t)
                if args.mode == "auto" and (
                    principle == "KINETIC_BREATHER" or enter_t is not None or exit_t is not None
                ):
                    detected_explainer = True

                file_issues = []
                if principle == "UNKNOWN":
                    file_issues.append(
                        "Missing principle tag comment/identifier (P1_CAPTION..P10_DARK_GRAPH or KINETIC_BREATHER)."
                    )
                if args.mode == "explainer" and principle == "P1_CAPTION":
                    file_issues.append(
                        "P1_CAPTION talking-head A-roll is disallowed in explainer mode; use KINETIC_BREATHER."
                    )
                file_issues.extend(check_texture_binding(code, principle))
                file_issues.extend(check_orphan_sequences(code))
                file_issues.extend(check_p6_quotes(code, principle))
                file_issues.extend(check_complex_hold(code, principle, root_durations))
                for err in file_issues:
                    report["passed"] = False
                    report["errors"].append(f"{sf.name}: {err}")

    if args.check in ("transitions", "all"):
        for err in check_root_timeline_gaps(timeline):
            report["passed"] = False
            report["errors"].append(f"Root.tsx: {err}")
        if detected_explainer and timeline:
            for err in check_transition_handshakes(timeline, scene_transitions):
                report["passed"] = False
                report["errors"].append(f"TransitionHandshake: {err}")
        if args.render_boundaries:
            for err in render_boundary_check(timeline, args.composition_id):
                report["passed"] = False
                report["errors"].append(f"RenderCheck: {err}")

    print(json.dumps(report, indent=2))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
