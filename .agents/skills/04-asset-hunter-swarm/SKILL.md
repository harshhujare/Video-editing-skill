---
name: asset-hunter-swarm
description: Use immediately after the user approves the Edit Plan Artifact to fetch Wikimedia classical paintings, Pexels stock B-roll, cutout objects, textures, and Google Fonts in parallel.
---

# Asset Hunter Swarm

## Overview

Populate `public/assets/` with high-resolution, pre-processed visual assets and fonts defined in `artifacts/edit_plan.md` using parallel Antigravity subagents before Remotion scene coding begins.

## Execution Architecture (Parallel Subagents)

First, parse `artifacts/edit_plan.md` into `build/asset_manifest.json` listing every required painting, B-roll clip, cutout object, texture, and font. Then launch three parallel workers (`invoke_subagent` for browser/scraping tasks and parallel workers for local/API tasks):

1. **`@paintings-and-photos-worker` (Browser Subagent — `browser`):**
   - For every `P3_PAINTING` scene, search Wikimedia Commons (`commons.wikimedia.org`) or public-domain museum archives using Antigravity's browser agent to download high-resolution (`>= 1500px` width) oil paintings matching the scene's subject. Save to `public/assets/paintings/<scene_id>.jpg`.
   - For every `P9_OBJECT_CALLOUT` requiring real-world photos of objects or the speaker, fetch high-resolution public-domain images and run background removal (`rembg i input.jpg output.png` or alpha cutout) to save clean transparent PNGs in `public/assets/images/<scene_id>.png`.

2. **`@broll-worker` (API & FFmpeg Subagent):**
   - For every `P2_BROLL_TEXT` scene, query Pexels Video API (using `PEXELS_API_KEY` from environment, or browser download fallback) for high-contrast vertical/4K clips matching the action keyword—OR delegate custom/Marathi-authentic B-roll & 3D scenes to `omni-video-broll-generator` (`omni-video-agent`). Save raw downloads to `build/raw_broll/`.
   - Immediately pre-process every clip into `public/assets/broll/<scene_id>.mp4` using:
     ```bash
     python .agents/skills/04-asset-hunter-swarm/scripts/prep_broll_vignette.py --input build/raw_broll/<clip>.mp4 --output public/assets/broll/<scene_id>.mp4
     ```
     (Or `bash .agents/skills/04-asset-hunter-swarm/scripts/prep_broll_vignette.sh <input.mp4> <output.mp4>` on POSIX/Git Bash.)
     This bakes in `-25%` saturation, `+10%` contrast, outer-20% radial blur + dark vignette, and a `15%` paper grain overlay at `1080x1920` `60fps`.

3. **`@typography-and-textures-worker` (Local Asset Worker):**
   - Download `Inter` (Regular 400, Bold 700) and `Playfair Display` (Italic 400, Bold Italic 700) `.ttf`/`.woff2` files from Google Fonts into `public/assets/fonts/`.
   - **If Marathi / Bilingual (`marathi-devanagari-engine`):** Also fetch Devanagari fonts into `public/assets/fonts/` (`Mukta-SemiBold.ttf`, `Mukta-ExtraBold.ttf`, `RozhaOne-Regular.ttf`, `NotoSansDevanagari-Bold.ttf`, `NotoSerifDevanagari-Bold.ttf`).
   - Ensure all core textures exist in `public/assets/textures/` (`paper_light.png`, `paper_rough_white.png`, `paper_cobalt_blue.png`, `paper_dark_charcoal_grain.png`, `cloth_rough.png`, `paint_brush_mask.png`).
   - **Verify Brand Logo Filename on Disk:** Check `public/assets/images/` and `input/images/` for the exact brand logo filename (e.g., `right_investment_logo.png`) before coding closing CTA scenes—never assume an unverified logo filename.

4. **`@editorial-illustration-worker` (Nano Banana `image-generator` Subagent — Replaces Raw CSS Wireframe Boxes):**
   - For every graphic scene (`P4`, `P5`, `P6`, `P8`, `P9`) that would otherwise rely on plain HTML/CSS bordered boxes or progress bars, generate cohesive editorial illustrations in `public/assets/generated/asset_0X_<name>.png`.
   - **Locked Art Direction Prefix (Prepend to EVERY Call):**
     > `"Luxury editorial magazine illustration in The Economist and Monocle style, tactile warm fine-art paper grain, rich matte gouache with crisp clean ink-line shading, authentic contemporary Indian financial storytelling aesthetic, cohesive color palette of warm cream (#F5F3EE), deep cobalt blue (#1E5EFF), emerald green (#15803D), muted crimson (#C8363A), and brushed gold. Soft directional studio lighting, clean uncluttered composition."`
   - **Strict No-Text Suffix (Append to EVERY Call):**
     > `"CRITICAL: ZERO text, zero letters, zero numbers, zero currency symbols, zero Devanagari characters, zero watermarks, zero labels anywhere in the image."`
   - **Rate-Limit & Aspect-Ratio Discipline (Hard Lesson):**
     - Do **NOT** launch 6 `image-generator` subagents simultaneously (triggers instant HTTP 429 burst `RESOURCE_EXHAUSTED`). Dispatch in staggered pairs (2 at a time).
     - `generate_image` supports `9:16`, `3:4` (use `3:4` whenever `4:5` portrait is requested), `1:1`, `4:3`, and `16:9`, and writes `.jpg` files to the conversation artifact directory. Convert every generated image to canonical `.png` inside `public/assets/generated/` using Pillow, crop 4–5% off edges if any corner watermark/sparkle appears, and **visually inspect every image with `read_file`** to verify zero garbled text before coding Remotion scenes.
     - If both `image-generator` and the fallback `GEMINI_API_KEY` REST endpoint hit quota exhaustion (`HTTP 429`), immediately report the exact quota block and provide copy-paste prompts so the user can drop the remaining files into `public/assets/generated/`.

## Verification

- Verify every file path listed in `build/asset_manifest.json` exists on disk and is non-empty.
- Probe `public/assets/broll/*.mp4` with `ffprobe` to confirm `1080x1920`, `60fps`, `yuv420p`.
- Verify `public/assets/images/*.png` files have a valid RGBA alpha channel (`rembg` cutout transparency).
