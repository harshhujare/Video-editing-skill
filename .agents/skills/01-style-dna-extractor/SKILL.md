---
name: style-dna-extractor
description: Use when training the workspace on a creator's editing style, analyzing reference short-form videos, or extracting animation keyframe contact sheets from a Figma style board.
---

# Style DNA Extractor

## Overview

Deconstruct up to 20 reference videos and a categorized Figma board into a structured reference catalog ([arthur-225-catalog.json](../03-storyboard-architect/references/arthur-225-catalog.json)) and individual animation keyframe folders mapped to the 10 visual principles.

## Prerequisites

- Reference videos placed in `training/raw_videos/` (`.mp4` files, up to 20).
- Exported Figma style board frames placed in `training/figma_board/`.
- Read [figma-10-principles.md](./references/figma-10-principles.md) before classifying extracted scenes.
- **Explainer Lookbook Mode (Faceless Videos):** When no talking-head A-roll exists, extract a 4-color Lookbook palette (`neutral_dark`, `neutral_light`, `accent_bright`, `ink_muted`) and motion curves from a brand hex palette or reference explainer video instead of a speaker's environment.

## Execution Architecture (Swarm Mode)

1. **Coordinator Initialization:**
   - Verify `training/raw_videos/` contains the reference MP4 files and `training/figma_board/` contains the annotated board exports.
   - Use Antigravity `swarm` (`action: "add"`, `workspace: "inherit"`, `tasks: [...]`) to spawn one parallel Ingestion Worker per video (`@ingest-worker-01` through `@ingest-worker-20`). Assign each worker a single video path and output folder to avoid write collisions.

2. **Worker Step-by-Step Procedure:**
   - **Step 1 — Audio & Word Alignment:**
     Run:
     ```bash
     python .agents/skills/01-style-dna-extractor/scripts/extract_keyframes.py --video <video_path> --out-dir training/extracted/<video_stem> --mode transcribe
     ```
     This generates millisecond-accurate word timestamps (`transcript.json`).
   - **Step 2 — Scene & Animation Detection:**
     Run:
     ```bash
     python .agents/skills/01-style-dna-extractor/scripts/extract_keyframes.py --video <video_path> --out-dir training/extracted/<video_stem> --mode scenes --scene-threshold 0.28
     ```
     This detects scene cuts and splits the video into isolated animated segments.
   - **Step 3 — Keyframe Sheet Generation:**
     For each detected segment, `extract_keyframes.py` exports a 3x3 keyframe contact sheet (`keyframes.png`) capturing entry, midpoint, and exit frames, plus `metadata.json` logging:
     - `duration_frames` (normalized at 60fps) and `duration_ms`
     - `start_ms` / `end_ms` and matched `trigger_phrase` from `transcript.json`
     - `camera_motion` placeholder (`pan`, `slide-in`, `zoom`, `track`, `static`) to be confirmed visually by the worker
   - **Step 4 — Principle Classification:**
     Inspect each `keyframes.png` alongside [figma-10-principles.md](./references/figma-10-principles.md) and assign `principle_id` (`P1_CAPTION` through `P10_DARK_GRAPH`) plus visual notes (font hierarchy, palette, texture binding, easing curve) in `metadata.json`.

3. **Coordinator Consolidation:**
   - Collect all worker outputs from `training/extracted/` into `references/animations/anim_001` .. `anim_XXX/`.
   - Merge every `metadata.json` entry into `.agents/skills/03-storyboard-architect/references/arthur-225-catalog.json`.

## Verification

- Every animation folder inside `references/animations/anim_XXX/` contains both `keyframes.png` and valid `metadata.json` with a non-empty `principle_id` and `trigger_phrase`.
- `arthur-225-catalog.json` parses cleanly with `python -m json.tool` and covers all 10 principles.
