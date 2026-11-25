---
name: adversarial-edit-verifier
description: Use automatically after Remotion scene workers finish coding and before presenting a draft video, to audit for orphan words, static textures, jump-cut glitches, short holds, missing quote marks, and (in Explainer Mode) mismatched camera transition handshakes.
---

# Adversarial Edit Verifier

## Overview

Run an automated static code audit and rendered-frame boundary inspection across all `src/scenes/SceneXX.tsx` files and `src/Root.tsx` to eliminate the classic AI editing defects prior to human review—in both **Talking-Head Mode** and **Faceless AI Explainer Mode**.

## The Mandatory Verification Checks

1. **Orphan Caption Word Check (Fixes Revision 1):**
   - Scan every caption group in `src/scenes/SceneXX.tsx`. Flag any caption card or `<Sequence>` lasting fewer than `24 frames` (`400ms` at `60fps`) or isolating a single trailing word (e.g., `"psychologically"`).
   - **Fix:** Merge the trailing word into the preceding caption block so the complete phrase stays together.

2. **Transition Continuity & Handshake Check (Fixes Revision 2 & Explainer Handshakes):**
   - Inspect 5 frames before and after every `<Sequence>` boundary. Verify camera slide-ins and cross-cuts have matching motion vectors and zero empty/solid-black frames.
   - **Explainer Mode Handshake:** Verify every adjacent scene pair `(SceneXX, SceneXX+1)` shares a matching `exitTransition.type === next.enterTransition.type` contract (either inside `<CameraRig enterTransition={...} exitTransition={...}>` or matching `build/explainer_timeline.json`).

3. **Texture-to-Camera Binding Check (Fixes Revision 3):**
   - Inspect every animated scene (`P2`–`P10` and `KINETIC_BREATHER`). Confirm `<TextureOverlay />` is nested *inside* `<CameraRig>` (not mounted as a static sibling/root background) and its `opacity` is strictly within `0.12`–`0.22`.

4. **A-Roll Jump-Cut Frame Check (Talking-Head Mode Only — Fixes Revision 4):**
   - Inspect every cut point returning to or leaving `P1_CAPTION` A-roll to ensure no 1-to-3 frame flash frames or mid-blink freeze frames occur at scene switches.
   - *Bypassed automatically in `--mode explainer` (which replaces `P1_CAPTION` with `KINETIC_BREATHER`).*

5. **Minimum Visual Hold Duration Check (Fixes Revision 5):**
   - Verify complex illustrations (`P5_LINE_ILLUSTRATION`, `P7_CENTER_ILLUSTRATION`) remain visible for at least `90 frames` (`1.5s`) after their entry animation settles.

6. **Principle 6 Quotation Marks Check (Fixes Revision 6):**
   - Verify every scene tagged `P6_QUOTE_SCENE` explicitly renders BOTH opening (`“` / `&ldquo;`) and closing (`”` / `&rdquo;`) decorative quotation marks around the centered text block.

## Execution Steps

1. **Archive Stale Scenes Before Auditing:** Ensure `src/scenes/` only contains the active `Scene01.tsx..SceneXX.tsx` files for the current video (move leftover `Scene*.tsx` from older projects into `build/archive_prev_scenes/`).
2. **Run Static & Boundary Verifier (`--mode talking-head` vs `--mode explainer`):**
   Always pass `--mode talking-head` explicitly for Mode A videos (so `auto` mode does not falsely require explainer camera transition handshakes on `P1_CAPTION` A-roll scenes):
   ```bash
   # Talking-Head Mode (Mode A):
   python .agents/skills/06-adversarial-edit-verifier/scripts/inspect_frames.py --scenes-dir src/scenes --root-file src/Root.tsx --mode talking-head --check all

   # Faceless AI Explainer Mode (Mode B):
   python .agents/skills/06-adversarial-edit-verifier/scripts/inspect_frames.py --scenes-dir src/scenes --root-file src/Root.tsx --mode explainer --timeline build/explainer_timeline.json --check all
   ```
3. **Marathi / Devanagari Check (if applicable):** Run `python .agents/skills/08-marathi-devanagari-engine/scripts/verify_marathi_text.py --transcript build/transcript_ms.json --scenes-dir src/scenes` to catch dotted circles (`◌`), `.split('')`, Devanagari italics, and tight `lineHeight < 1.42`.
4. **Mandatory 12-Scene Visual QA Contact Sheet & Full-Res Still Inspection (Before Full Video Render):**
   Bundle once (`npx remotion bundle src/index.ts --out-dir=build/remotion_bundle_qa`), render 1 representative settled still per scene (`npx remotion still build/remotion_bundle_qa MainVideo ... --frame=<midFrame>`), tile into a `4×3` grid (`ffmpeg -vf "scale=360:640,tile=4x3"`), and inspect both the grid and full-resolution key stills via `read_file` for these 5 visual defects:
   - **Speaker Face vs. Caption Occlusion in Split Views (`Scene10`):** In wide rounded A-roll split views, verify `objectPosition` (`'50% 42%'`) frames the speaker's eyes, nose, and mouth cleanly *above* the frosted caption pill (`top: 1232`).
   - **Dataviz Stamp & Badge Collisions (`Scene09`):** Confirm the tilted `₹0 वाढ` halftone stamp (`top: 620, left: 435`) and `asset_05_frozen_passbook.png` badge (`right: 40, bottom: 162`) never overlap the `Post Office · ₹15 लाख (FLAT)` callout box.
   - **Generated Illustration Edge Artifacts (`Scene06`):** Check the inner edges of generated illustrations for unwanted border decorations or corner sparkle marks; crop via `scale(1.08)` or Pillow edge crop and keep `gap >= 44px` between left/right payout pills so center scale finials stay uncovered.
   - **Closing Backdrop Text Contrast (`Scene12`):** When using a closing backdrop with bright bottom architectural detail (e.g., `asset_06_closing_backdrop.png` gold staircase), verify the quote, circular logo, CTA pill, and AMFI disclaimer all sit in the dark cobalt upper/middle zone (`y: 235..1060`) well above the staircase.
   - **Zero Wireframe Boxes & Safe Zones:** Confirm zero `2px solid black` wireframe borders, <=20% dead blank space, and all UI elements inside Reels/Shorts safe zones (`y: 220..1380`, `x: 80..960`).
5. **Remediation Loop:** Patch any visual or static failure in `src/scenes/SceneXX.tsx`, re-render the affected still to confirm the fix, and re-run `inspect_frames.py` + `verify_marathi_text.py` until **0 errors** remain.
