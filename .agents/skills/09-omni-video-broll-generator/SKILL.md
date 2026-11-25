---
name: omni-video-broll-generator
description: Use instead of or alongside stock B-roll scraping when custom 9:16 cinematic B-roll, 3D object showcases, or rotoscope-ready character plates are needed via omni-video-agent.
---

# Omni-Video Generative B-Roll & 3D Asset Swarm

## Overview

Replace generic stock footage by dispatching parallel `omni-video-agent` workers (1 worker per generative B-roll, 3D object, or character plate beat in `artifacts/edit_plan.md`). Every generated clip is conformed to `1080x1920 @ 60fps`, color-locked to [ten-principles-tokens.json](../05-remotion-minimal-scenes/references/ten-principles-tokens.json) (or a custom Lookbook), framed with clean negative space for English/Marathi typography, and given a `+300ms` (`18-frame`) tail handle for smooth Remotion transitions.

## Swarm Role Allocation

- **Coordinator Agent:** Parses `artifacts/edit_plan.md`, computes target durations (`duration_ms = end_ms - start_ms + 300`), and builds structured `omni-video-agent` payloads using [omni-prompt-templates.json](./references/omni-prompt-templates.json).
- **Omni-Video Worker Swarm (1 Worker Per Scene):** Calls `omni-video-agent` (`generate_video` / `generate_with_subjects` / `animate_image` with `aspect_ratio: "9:16"`, `delivery: "uri"`), conforms output to `public/assets/broll/<scene_id>.mp4` (`1080x1920 @ 60fps`), and optionally runs bounding-box tracking or foreground matte extraction.
- **Verifier Agent:** Audits start, midpoint, and end frames for hallucinated text, anatomy distortion, palette drift (`> 15%`), and typography safe-zone clutter; triggers `edit_video` (stateful `previous_interaction_id`) or re-rolls on failure.

## Step-by-Step Execution Protocol

### Step 1: Translate Storyboard Beats into Palette-Locked Prompts

For every generative visual beat in `artifacts/edit_plan.md`, build the `omni-video-agent` prompt using this 5-part formula (see [omni-prompt-templates.json](./references/omni-prompt-templates.json)):

1. **Aspect Ratio & Framing Prefix:**
   Call `generate_video` with `aspect_ratio: "9:16"` and prefix the prompt with:
   `Vertical 9:16 (1080x1920), cinematic commercial footage, shallow depth of field.`
2. **Principle-Specific Compositional Framing:**
   - **`P2_BROLL_TEXT` (Textured B-Roll):** Medium-wide shot with a darker, low-contrast center third (`y: 750–1150`) to guarantee high-contrast legibility for centered English or Marathi captions.
   - **`P8_SIDE_ILLUSTRATION` (Side Split):** Frame the hero subject strictly in the left 45% (or right 45%) of the vertical frame, leaving the opposite 55% in smooth out-of-focus dark bokeh (`#0D0F12`) for side-by-side typography.
   - **`P7_CENTER_ILLUSTRATION` / Rotoscoped Back-Text:** Center the hero subject from waist up against a clean dark textured background with strong hair/shoulder rim light so foreground matte extraction cleanly separates the subject behind oversized `Rozha One` / `Khand Bold` back-text.
   - **`P9_OBJECT_CALLOUT` (3D Object Showcase):** Macro 3D studio object floating dead center (`x: 540, y: 960`) over a dark matte surface with directional cast shadow and subtle edge depth-of-field dust particles.
3. **Color Palette Lock:**
   Inject the active palette from `ten-principles-tokens.json` (charcoal `#0D0F12` shadows, cobalt `#1E5EFF` or warm paper `#F5F3EE` highlights, zero off-palette neon clutter) or custom Lookbook swatches when provided.
4. **Cultural & Domain Authenticity (Marathi Context):**
   When `marathi-devanagari-engine` is active, specify authentic Indian subjects, environments, and props (e.g., *"Contemporary Indian professional in a Pune office"*, *"Indian retiree relaxing confidently"*).
   **Mandatory Negative Constraint:** Always include `"NO in-camera text, NO signage, NO subtitles, NO watermarks"`. All typography must be rendered as crisp Remotion vector layers.
5. **Camera Motion Curve:**
   Match camera movement to the Remotion transition (`slow dolly push-in`, `subtle parallax orbit`, or `whip-pan entry/exit`).

### Step 2: Parallel Generation & Multi-Card Batching

1. Dispatch 1 worker per generative scene beat (`@omni-scene-02`, `@omni-scene-05`, etc.).
2. For rapid multi-card hooks (e.g., 3 consecutive character action clips in 4 seconds), spawn sub-workers (`scene_03a`, `scene_03b`, `scene_03c`) using `generate_with_subjects` with a shared reference image for character consistency.
3. Conform every downloaded clip to `1080x1920`, `60fps`, `yuv420p` with a `+300ms` (`18-frame`) tail handle:
   - For `P2_BROLL_TEXT` scenes, run `python .agents/skills/04-asset-hunter-swarm/scripts/prep_broll_vignette.py --input <raw_omni.mp4> --output public/assets/broll/<scene_id>.mp4` to bake in the desaturated vignette and 15% paper grain.

### Step 3: Optional Tracking & Foreground Matte Extraction

When a scene uses tracked selector boxes, animated arrows, or moving rotoscoped back-text:

1. **Bounding-Box Tracking (`public/assets/scenes/<scene_id>/tracking-coords.json`):**
   Run YOLOv11 / ByteTrack on the conformed clip to export per-frame `[x, y, width, height]` coordinates for `<SelectorBox />` and `<AnimatedArrow />`.
2. **Rotoscope Foreground Matte (`public/assets/scenes/<scene_id>/foreground-matte.webm`):**
   Run SAM-2 Video on the conformed clip to export a transparent alpha-channel foreground layer so oversized Marathi `Rozha One` / `Khand` typography can sit *behind* the moving subject.

### Step 4: Adversarial Quality & Palette Gate

1. Extract and inspect start, midpoint, and end frames of every generated clip.
2. Reject and either iterate statefully via `edit_video(previous_interaction_id=..., edit_prompt=...)` or regenerate if:
   - Any hallucinated background text, gibberish signage, or deformed anatomy appears.
   - Color balance deviates noticeably from the workspace palette.
   - Bright clutter sits inside the designated typography safe zone (threatening Marathi *Matra* or English caption legibility).
