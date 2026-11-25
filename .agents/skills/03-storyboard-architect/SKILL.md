---
name: storyboard-architect
description: Use after audio preprocessing (02-audio-silence-preprocessor or 10-explainer-audio-director) to plan the video edit, match transcript beats to the 10 visual principles (or 50/30/20 Explainer beats), and generate an interactive two-column edit plan artifact for user review.
---

# Storyboard Architect

## Overview

Produce an interactive Two-Column Edit Plan Artifact (`artifacts/edit_plan.md` plus an Antigravity user-facing Artifact) mapping every spoken clause in `build/transcript_ms.json` (and `build/explainer_timeline.json` in Explainer Mode) to a visual principle (`P1`–`P10` or `KINETIC_BREATHER`) and reference folder from [arthur-225-catalog.json](./references/arthur-225-catalog.json) while enforcing human-centric pacing.

## Core Editorial Pacing Rules

### Mode A — Talking-Head Mode (`02-audio-silence-preprocessor`)
1. **The Announcement-vs.-Description Rule (Mandatory):**
   - **Stay on Captioned A-Roll (`P1_CAPTION`)** whenever the speaker introduces a new thesis, announces a new category/number, or pivots topics. Viewers must connect with the speaker's face during structural transitions.
   - **Switch to Visual Scenes (`P2` through `P10`)** the moment the speaker begins illustrating, describing, or giving an example of that category.
2. **0–2.6s Scroll-Stopping Visual Hook (`Scene01`):**
   - When spoken A-roll opens with a slow narrative setup (e.g., *"2022 साली आपले एक Customer Retire झाले"*), anchor a bold, steady translucent editorial hook pill at the top of the frame (`y: 235`, `x: 90..950`, no hard black border) for the **entire opening scene (`2.5s+`)**—never fade it out after 1 second—stating the stakes upfront (e.g., `₹15L vs ₹15L · 4 वर्षांनंतरचा फरक`).
3. **Break Up Long Faceless Stretches (Max 10s Continuous Graphics):**
   - Leaving talking-head A-roll for `15–20+` consecutive seconds during the climax turns an advisor reel into a faceless explainer right where viewer trust matters most.
   - Insert a **`1.5s` A-roll authority punch-in (`scale 1.06`)** on the narrative turn (*"पण आज 4 वर्षांनंतर..."*) before snapping to the climax chart.
   - On verdict/summary comparison scenes (`Scene09`/`Scene10`), use a **2-Zone Vertical Split Layout** (Top 50% side-by-side visual comparison cards at `y: 220..880` + Bottom 35% large rounded wide-frame talking-head A-roll `880×450px` at `y: 895..1345`) instead of a tiny postage-stamp PiP surrounded by blank whitespace.

### Mode B — Faceless AI Explainer Mode (`10-explainer-audio-director`)
When `build/explainer_timeline.json` is present (no talking-head A-roll):
1. **Bypass `P1_CAPTION`:** Do NOT plan talking-head A-roll cuts. Replace A-roll breathers with `KINETIC_BREATHER` full-screen editorial typography cards on the Lookbook `neutral_dark` + `accent_bright` palette during rhetorical questions, narrative pivots, or thesis punches.
2. **2.0 to 3.5 Second Visual Momentum:** Every beat in `build/explainer_timeline.json` must shift visuals every `2.0s`–`3.5s` (`120`–`210` frames at `60fps`). Respect `[SCENE]` breaks from `input/display-script.txt`, and never hold a static frame longer than `3.5s` without an internal animated build.
3. **50/30/20 Visual Engine Ratio:**
   - **50% Full-Screen Remotion Motion (`P4`, `P5`, `P7`, `P8`, `P9`, `P10`):** Numbers, compounding graphs, split comparisons, checklists, and shadowed 3D showcases.
   - **30% Generative / Stylized B-Roll (`P2_BROLL_TEXT` via `09-omni-video-broll-generator`):** Dramatic story metaphors, scenarios, and rotoscoped back-text sequences.
   - **20% Kinetic Typography Breathers (`KINETIC_BREATHER` / `P6_QUOTE_SCENE`):** Minimalist full-screen typography cards that prevent visual fatigue without feeling like a slideshow.
4. **Shared Camera Transition Handshakes (Mandatory):** Write explicit `enter_transition` and `exit_transition` contracts (`zoom_through`, `pan_left`, `pan_up`, `anchor_morph`, or `none`) for every scene so parallel `05-remotion-minimal-scenes` workers stitch into one continuous virtual camera (`scene[i].exit_transition.type === scene[i+1].enter_transition.type`).

### Shared Rules (Both Modes)
1. **Visual Cohesion — The "No Style Soup" Law (Mandatory):**
   - Lock the entire storyboard to **ONE unified visual system** (e.g., *Economist / Monocle Matte Gouache & Ink Editorial Illustrations + Shared Dark-Mode Dataviz + Halftone Dossier Stamp*).
   - Never mix 3D isometric coin plinths, whiteboard marker sketches, photoreal cutouts, wobbly pencil/cloth textures, and glowing fintech spheres inside the same 50-second reel.
   - **No Raw CSS Wireframes:** Never plan plain HTML/CSS bordered rectangles (`2px solid black`) or abstract progress bars as the primary visual of a scene; pair every non-chart graphic beat (`P4`, `P5`, `P6`, `P8`, `P9`) with a cohesive **Nano Banana (`image-generator`)** editorial illustration (`public/assets/generated/asset_0X_*.png`).
2. **Spatial Continuity on Comparative Graphs (`Scene[i] → Scene[i+1]`):**
   - When comparing two trajectories across consecutive scenes (e.g., Mutual Fund growth `₹15L → ₹20L` followed by Post Office flatline `₹15L → ₹15L`), keep **both scenes on the exact same coordinate grid, axes, and `#0D0F12` dark background** (dimming the first curve to a `22%` ghost reference while drawing the second curve and slamming the `₹0 वाढ` stamp on the same axes). Never jump from a dark-mode graph to light archive paper mid-comparison.
3. **Pattern Matching Logic:**
   - Quantitative or directional repetition (e.g., "up and up and up", "slow and steady", percentages/compounding) -> `P10_DARK_GRAPH` (use a tall `760px` chart container so there is no dead black void)
   - Geographical, romantic, or philosophical storytelling (e.g., "barista in San Diego") -> `P3_PAINTING`
   - Biographical mention of a specific person (e.g., "my dad worked 42 years", father & daughter investing) -> `P7_CENTER_ILLUSTRATION` or `P8_SIDE_ILLUSTRATION` (backed by a cohesive Nano Banana editorial illustration)
   - Visceral action metaphors (e.g., "take career down to the studs") -> `P2_BROLL_TEXT`
   - Personal milestones or physical objects (e.g., retirement corpus desk, heritage postbox) -> `P9_OBJECT_CALLOUT` (full-bleed or large `860×900px` rounded editorial card)
   - Equal/parallel comparison beats (e.g., "same monthly pension in both places") -> `P4_LINE_TEXT` (concrete visual metaphor such as a balanced brass scale with synchronized pulsing payout pills above the pans—never abstract ticking lines)
   - Multi-part abstract values or verdict comparisons -> `P5_LINE_ILLUSTRATION`
   - Final philosophical punchline or thesis takeaway -> `P6_QUOTE_SCENE` (with both opening `“` and closing `”` quotes over a full-bleed editorial backdrop, plus **`+1.5s` to `+2.0s` branded CTA end-card hold** after voice ends)
   - Rhetorical question, twist, or faceless narrative pivot -> `KINETIC_BREATHER`

4. **Anti-Orphan Grouping & Frame-Budget Feasibility Rule:**
   - Group words into semantic clauses of **2 to 5 seconds** (`120` to `300` frames at `60fps`; `60` to `150` frames at `30fps`).
   - Within each scene, captions display **5 words or fewer** per card (for Marathi, follow `08-marathi-devanagari-engine` `4–5` words / `<= 28` graphemes, never splitting *Vibhakti* postpositions). Never allow the final trailing word of a clause to spill into an isolated sub-400msscene; absorb it into the preceding card.
   - **Frame-Budget Feasibility:** Check total scene frames before assigning holds. Complex `P5` and `P7` scenes lasting `>= 3.6s` hold for `>= 90f @ 60fps`; fast transition scenes (`2.3s–2.7s`, e.g., `Scene03` single-branch reveal) should be tagged `P9_OBJECT_CALLOUT` with a single clean hero card reveal and `35–45f` settle hold rather than impossible 15-part staggered coin drops.
5. **Reels/Shorts Safe Zones & Regulatory Compliance (AMFI/SEBI):**
   - Keep all UI headers, illustrations, captions, logos, and disclaimers strictly inside `y: 220–1380` and `x: 80–960` (`1080×1920`).
   - Whenever a script compares fixed/sovereign returns against market-linked instruments (Mutual Fund SIP/SWP), include a crisp `18–19px` disclaimer footer (`Mutual Fund investments are subject to market risks. Past performance is not guaranteed.`) across all performance chart, verdict, and closing CTA scenes.

## Step-by-Step Instructions

1. Read `build/transcript_ms.json` (and `build/explainer_timeline.json` if running in Explainer Mode) and align beats on exact `start_frame` / `end_frame` boundaries.
2. Query [arthur-225-catalog.json](./references/arthur-225-catalog.json) to match each beat to the closest reference `anim_XXX` template.
3. Generate the Two-Column Storyboard as both `artifacts/edit_plan.md` (workspace copy for downstream JSON parsing) AND a user-facing **Antigravity Artifact** (`RequestFeedback: true`) formatted as a Markdown table:
   - **Left Column (`Scene & Reference`):** Scene ID (`Scene01`..), Principle ID (`P1`–`P10` or `KINETIC_BREATHER`), Reference ID (`anim_XXX`), visual engine (`remotion_motion` / `omni_broll` / `kinetic_breather`), required external assets (painting query / `omni-video-agent` prompt / cutout subject / graph data), and `enter_transition` -> `exit_transition` contract.
   - **Right Column (`Timecoded Script`):** `[start_ms - end_ms]` (`[start_frame - end_frame]`), exact `display-script.txt` / transcript clause, and `**BOLD**` markers on the 1–2 keywords per group designated for emphasis typography (`Playfair Display Bold Italic` for Latin, `Rozha One` / `Khand` for Devanagari).
4. **Human-in-the-Loop Gate:** Stop and ask the user to review the Artifact and leave inline feedback or approve before triggering `04-asset-hunter-swarm`, `09-omni-video-broll-generator`, or `05-remotion-minimal-scenes`.
