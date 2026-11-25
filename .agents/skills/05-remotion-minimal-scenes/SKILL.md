---
name: remotion-minimal-scenes
description: Use when building modular React/Remotion video scene components from an approved edit plan and fetched assets in parallel Swarm Mode.
---

# Remotion Minimal Scenes

## Overview

Compile every beat in `artifacts/edit_plan.md` into an isolated, frame-accurate Remotion scene component (`src/scenes/SceneXX.tsx`) using shared primitives (`src/primitives/`) and design tokens ([ten-principles-tokens.json](./references/ten-principles-tokens.json)), then assemble them in `src/Root.tsx`.

## Swarm Isolation Architecture

1. **Bootstrap Shared Primitives First (Coordinator):**
   Before spawning scene workers, ensure the Remotion project has shared base primitives in `src/primitives/` and font loading in `src/styles/fonts.ts`:
   - `<CameraRig>`: Applies `translateX`, `translateY`, `scale`, and `rotate` transforms to all children together, plus optional `enterTransition` / `exitTransition` handshake contracts (`zoom_through`, `pan_left`, `pan_up`, `anchor_morph`) for seamless cross-scene camera flow.
   - `<TextureOverlay>`: Renders the paper/cloth/grain PNG with `opacity` strictly between `0.12` and `0.22` (`mixBlendMode: 'multiply'` on light paper, `'screen'` on dark `#0D0F12`).
   - `<DualFontCaption>` & `<KineticWordGroup>`: Renders `<= 5` words per card using `Inter` + `Playfair Display Bold Italic` (or bilingual Marathi composite fonts) with spring reveals synced to `build/transcript_ms.json`.
   - `<TrackedSvgPath>`: Animates `strokeDashoffset` in `#1E5EFF` (`strokeWidth: 6`) and exposes `(x, y)` tip coordinates for `<CameraRig>`.

2. **One Named Worker Per Scene (`swarm`):**
   - Spawn one worker per scene (`@scene-01`, `@scene-02`, etc.) using Antigravity `swarm` (`action: "add"`, `workspace: "share"` if workers run builds independently, or `workspace: "inherit"` with strict single-file ownership).
   - **Strict Ownership:** Each worker may ONLY write to its assigned `src/scenes/SceneXX.tsx` file and read from `src/primitives/`, `public/assets/`, `build/transcript_ms.json`, and `build/explainer_timeline.json`. Never edit another scene's file or `src/Root.tsx` from a scene worker.
   - The Coordinator merges/assembles all `SceneXX.tsx` components into `src/Root.tsx` once all scene workers finish.

## Mandatory Global Laws (All Workers)

1. **Texture Binding Law:**
   NEVER mount `<TextureOverlay />` outside an animated `<CameraRig>`. In every animated scene (`P2`–`P10` and `KINETIC_BREATHER`), wrap BOTH the scene artwork/typography AND `<TextureOverlay />` inside the same `<CameraRig>` container so paper grain tracks organically with camera pans, zooms, and transition handshakes.
   ```tsx
   <CameraRig
     x={camX}
     y={camY}
     scale={camScale}
     enterTransition={{ type: 'zoom_through', durationFrames: 18 }}
     exitTransition={{ type: 'pan_left', durationFrames: 18 }}
   >
     <SceneArtwork />
     <DualFontCaption words={group} />
     <TextureOverlay src={staticFile('assets/textures/paper_rough_white.png')} opacity={0.18} />
   </CameraRig>
   ```

2. **Shared Camera Transition Handshake Law (Explainer Mode):**
   When `build/explainer_timeline.json` or `artifacts/edit_plan.md` specifies `enter_transition` / `exit_transition`, every scene worker MUST pass those exact `enterTransition` and `exitTransition` contracts into its root `<CameraRig>` (and include a `// Principle: <PRINCIPLE_ID>` + `// Transitions: enter=<type> exit=<type>` header comment) so adjacent scenes share matching motion vectors.

3. **Dual-Font Caption Layout & Reels/Shorts Safe-Zone Law (`P1`–`P10` & `KINETIC_BREATHER`):**
   - Maximum **5 words** visible per caption card.
   - **Reels / Shorts Safe Zones (`1080×1920` — Mandatory):**
     - **A-Roll & Graphic Caption Pills:** Anchor at `y: 1215–1235`, `maxWidth: 820px`, centered (clears bottom handle/caption UI `y: 1400–1920` and right action icons `x > 960`). Style as sleek dark-frosted pills (`backgroundColor: 'rgba(13, 15, 18, 0.78)'`, `backdropFilter: 'blur(14px)'`, `border: '1px solid rgba(255,255,255,0.14)'`, `borderRadius: 16px`, `padding: '20px 30px'`, soft shadow `0 20px 50px rgba(13,15,18,0.30)`).
     - **Top Hook Banners & Timeline Pills:** Place at `y: 225–240`, `left: 90`, `width: 860px` (`x <= 950`) as borderless translucent pills (`rgba(245,243,238,0.92)` or `rgba(20,24,32,0.82)`). Keep `Scene01` hook headers steady at opacity `1` for the full opening scene (`2.5s+`).
     - **Regulatory Disclaimers:** Place at `y: 1345–1358` (or `y: 1045` in the upper/mid dark zone when bright bottom artwork occupies the lower 30%, as in `Scene12` staircase backdrops).
   - **No Raw Wireframe CSS Boxes or >20% Dead Space:** Never render `2px solid black` wireframe borders, hard neo-brutalist offset shadows (`box-shadow: 4px 4px 0 #000`), or empty blank backgrounds. Use full-bleed `9:16` editorial illustrations (`Scene02`, `Scene12`) or large rounded hero cards (`width: 860–880px`, `height: 830–920px`, `borderRadius: 24–28px`, soft ambient shadow `0 24px 60px rgba(13,15,18,0.12)`).
   - **No Orphan Flash Frames:** Never split the final word of a clause into its own `< 24` frame card or `<Sequence>`; merge it into the active sentence block.
   - **Marathi Override (`marathi-devanagari-engine`):** Use `Mukta SemiBold (600)` + **`Mukta ExtraBold (800)`** on all caption pills (never `Rozha One` on moving video captions—its thin hairlines shimmer under H.264 compression). Reserve `Rozha One` strictly for `66px+` solid-canvas headlines and `P6_QUOTE_SCENE`. Enforce `lineHeight >= 1.42` on every numeric `lineHeight` style in Devanagari `.tsx` files, `paddingTop/Bottom: 20px`, zero inline `fontStyle: 'italic'`, and `Intl.Segmenter('mr', { granularity: 'grapheme' })`.
   - **Archive Stale Scenes First & Match Native Source FPS:** Move any leftover `src/scenes/Scene*.tsx` files from previous projects into `build/archive_prev_scenes/` before creating new scenes. When source A-roll is `30fps`, support native `30fps` composition rendering (`aroll_trimmed_30fps.mp4`, `<OffthreadVideo muted startFrom={...} />` with sub-pixel `translate3d` scale transforms) to prevent 30→60fps frame-doubling judder.

## Implementation Specs for the 10 Principles + Kinetic Breather

- **`P1_CAPTION` (Talking-Head A-Roll + Captions):** Render muted `aroll_trimmed_30fps.mp4` (or `60fps` master) full screen (`1080x1920`) with smooth sub-pixel `translate3d(0,0,0) scale(...)` push-in (audio plays continuously from `aroll_dialogue.wav` in `AudioTimeline.tsx`). Anchor `<ArollCaptionBar>` at `top: 1215` (`maxWidth: 820px`).
- **`KINETIC_BREATHER` (Explainer Kinetic Typography Breather):** Full-screen editorial typography card replacing A-roll cuts during rhetorical questions or twists. Render `<KineticWordGroup>` centered over a subtly animated `neutral_dark` (`#0D0F12`) canvas with `accent_bright` keyword highlights, wrapped inside `<CameraRig>` alongside `<TextureOverlay src={staticFile('assets/textures/paper_dark_charcoal_grain.png')} opacity={0.18} mode="screen" />`.
- **`P2_BROLL_TEXT` (Textured B-Roll):** Mount the pre-vignetted clip `public/assets/broll/<scene_id>.mp4` inside `<CameraRig>` (subtle `1.00 -> 1.05` push-in). Center `<DualFontCaption>` optically (`top: 46%`).
- **`P3_PAINTING` (Painting Slide-In):** Place the Wikimedia painting inside a feathered brush-stroke mask (`paint_brush_mask.png`) over `paper_rough_white.png`. Animate a fast camera slide-in (`cubic-bezier(0.16, 1, 0.3, 1)` over `18` frames).
- **`P4_LINE_TEXT` (Concrete Parity / Tracked Visual Metaphor):** Instead of abstract CSS progress bars, fill the center canvas (`width: 880px`, `height: 855px`, `borderRadius: 28px`) with a concrete editorial illustration (e.g., `asset_04_equal_payout.png` balanced brass scale with subtle `±5px` vertical float and `scale(1.08)` edge crop) and place synchronized pulsing payout pills directly above the left and right pans with `gap >= 44px` so the center finial remains uncovered.
- **`P5_LINE_ILLUSTRATION` (Progression / 2-Zone Verdict Split):** For comparison verdicts (`Scene10`), use a **2-Zone Vertical Split Layout**: Top zone (`y: 222..872`, `width: 880px`) with two side-by-side rounded comparison cards (`borderRadius: 24px`, `340px`-high illustrated thumbnail headers from `asset_02` and `asset_03`) + Bottom zone (`y: 895..1345`, `width: 880px`, `height: 450px`, `borderRadius: 28px`) featuring wide-frame talking-head A-roll (`objectPosition: '50% 42%'` so the speaker's face sits cleanly above `<ArollCaptionBar top={1232} />`).
- **`P6_QUOTE_SCENE` (Full-Bleed Editorial Closing Backdrop + Branded CTA Hold):** Mount full-bleed `asset_06_closing_backdrop.png` (`scale 1.00 -> 1.05` slow drift) + `<TextureOverlay opacity={0.14} mode="multiply" />` inside `<CameraRig>`. Render BOTH oversized opening `“` and closing `”` marks (`156px`, `lineHeight: 1.42` with negative margins `-92px`) framing the centered `Rozha One` quote, plus the circular brand logo (`right_investment_logo.png`), brushed-gold/cream CTA pill, and AMFI disclaimer—all positioned in the deep cobalt upper/mid zone (`y: 235..1060`) cleanly above any bright bottom architectural illustration.
- **`P7_CENTER_ILLUSTRATION` (Abstract Center Piece):** Place illustration across the center frame inside `<CameraRig>`. Hold `>= 90` frames (`60fps`) after entry settles.
- **`P8_SIDE_ILLUSTRATION` (Split Allocation + Hero Illustration Card):** Top 50/50 split reference strip (`y: 222`, docking the dimmed `asset_02` thumbnail chip alongside the active cobalt chip) + large `860×830px` rounded hero illustration card (`asset_03_father_daughter_mf.png`, `objectPosition: '50% 88%'` to frame characters and coin sprout cleanly) with a warm emerald pill badge (`"मुलीच्या आग्रहाखातर"`) animating in on the narrative cue.
- **`P9_OBJECT_CALLOUT` (Full-Bleed or Hero Card Editorial Object):** Either full-bleed `9:16` editorial illustration (`asset_01_retirement_corpus.png` with Ken Burns `1.00 -> 1.07` zoom and upper negative-space `₹30 लाख` count-up at `y: 235..530`) or large `860×920px` rounded hero card (`asset_02_post_office.png` with top-centered pill badge `POST OFFICE · ₹15 लाख`).
- **`P10_DARK_GRAPH` (Shared Taller `760px` Dark Charcoal Dataviz Grid):** Use a shared `<SharedDarkDatavizGrid />` component (`top: 315`, `left: 90`, `width: 880px`, **`height: 760px`**, `borderRadius: 24px`) on `#0D0F12` across consecutive comparison scenes (`Scene08` → `Scene09`) so axes never jump. On the flatline contrast beat (`Scene09`), dim the growth curve to `22%` ghost opacity, draw the crimson `#D62828` flatline, slam `<HalftoneStamp label="₹0 वाढ" />` at `top: 620, left: 435` (clearing the flatline label), and fade in the `210×210` dark-mode `asset_05_frozen_passbook.png` badge (`right: 40, bottom: 162`).

## Verification

- Typecheck the Remotion project (`npx tsc --noEmit`) with zero errors.
- Hand off all `src/scenes/SceneXX.tsx` files to `06-adversarial-edit-verifier` before rendering drafts.
