# Modular Multi-Mode Video Editing & Generation Workspace

This workspace runs an 11-skill, Swarm-enabled Remotion & Code-Driven Video Studio inside Google Antigravity supporting **5 distinct video production modes** and a **Modular Multi-Project Architecture (`projects/<slug>/`)** so any number of videos can be edited or generated without overwriting previous work.

---

## Supported Video Modes (What We Can Edit or Generate)

| Mode | Input Required | Primary Skills Used | Best For |
|---|---|---|---|
| **Mode A — Talking-Head + Editorial Cutaways (`editorial-hybrid` / `talking-head`)** | Raw talking-head camera clip (`projects/<slug>/input/raw_clip.mp4`) | `02-audio-silence-preprocessor` → `03-storyboard-architect` → `04-asset-hunter-swarm` (Nano Banana `image-generator`) → `05-remotion-minimal-scenes` → `06-adversarial-edit-verifier` → `07-foley-sound-designer` (+ `08-marathi-devanagari-engine` for Marathi) | Advisor Reels/Shorts, case studies, personal finance breakdowns, founder commentary |
| **Mode B — Faceless AI Voiceover Explainer (`faceless-explainer`)** | Manual ElevenLabs voiceover (`input/voiceover.{mp3,wav}`) + clean on-screen script (`input/display-script.txt`) | `10-explainer-audio-director` → `03-storyboard-architect` (50/30/20 split + camera handshakes) → `04-asset-hunter-swarm` → `05-remotion-minimal-scenes` → `06-adversarial-edit-verifier` (`--mode explainer`) → `07-foley-sound-designer` | Faceless YouTube Shorts / Instagram Reels, storytelling explainers, educational narratives |
| **Mode C — Generative Video B-Roll & 3D Showcase (`generative-broll`)** | Raw clip or voiceover + script | `09-omni-video-broll-generator` (`omni-video-agent` / Veo / Pexels) + `05-remotion-minimal-scenes` (`P2_BROLL_TEXT`, `P7`, `P9`) | Cinematic 9:16 B-roll metaphors, 3D object callouts, rotoscoped back-text reels |
| **Mode D — Pure Code-Driven Short Film (`lemo-opuscar-film`)** | Topic or script (`input/display-script.txt`) + optional voiceover + 1 of **99 Lemo-Opuscar styles** (`$LIB/styles/<style>/STYLE.md`) | `lemo-opuscar` (`C:/Users/Asus/lemo-opuscar`, 99 styles across Documentary, Painting, Sketch/Whiteboard, Print/Halftone, Swiss Type, Isometric Diagrams, 3D Miniature, Instruments, Data & Maps) | Zero-API-credit animated short films, data storytelling, archival investigations, product teardowns |
| **Mode E — Creator Style Cloning (`style-dna-extractor`)** | Up to 20 reference videos (`training/raw_videos/`) or brand Lookbook | `01-style-dna-extractor` | Extracting new creator motion templates (`arthur-225-catalog.json`) or 4-color brand Lookbooks |

---

## Modular Multi-Project Architecture (`scripts/project.py`)

Never overwrite `input/`, `build/`, `src/scenes/`, or `public/assets/generated/` directly when starting a new video. Use `python scripts/project.py` to manage isolated projects under `projects/<slug>/`:

```bash
# 1. List all projects in the workspace and see which project is currently active:
python scripts/project.py list

# 2. Initialize & activate a new project (auto-saves the current active project first!):
python scripts/project.py init <project-slug> --mode editorial-hybrid --lang mr --fps 30 --source raw-videos/<clip>.mp4 --activate

# 3. Save current active workspace (src/scenes, Root.tsx, AudioTimeline.tsx, build, generated assets, edit_plan.md) into projects/<slug>/:
python scripts/project.py save

# 4. Switch/load any existing project back into the active Remotion workspace:
python scripts/project.py load <project-slug>
```

### How Shared vs. Project-Scoped Files Are Separated
- **Shared Global Library (Reused Across All Projects):**
  - `src/primitives/` & `src/styles/fonts.ts` (shared Remotion components: `CameraRig`, `TextureOverlay`, `SwissEditorial`, `DualFontCaption`, `TrackedSvgPath`, `KineticTypography`)
  - `public/assets/fonts/` (`Mukta`, `Rozha One`, `Inter`, `Playfair Display`, `Khand`, `Noto Sans/Serif Devanagari`)
  - `public/assets/textures/` (`paper_rough_white.png`, `paper_dark_charcoal_grain.png`, `paper_cobalt_blue.png`, etc.)
  - `public/assets/sfx/` (`notched_*.wav` vocal-notched studio transients) & `public/assets/music/`
  - `public/assets/images/` (shared brand logos such as `right_investment_logo.png`)
- **Project-Isolated Files (`projects/<slug>/`, swapped into active workspace by `project.py load`):**
  - `projects/<slug>/input/` (`raw_clip.mp4`, `voiceover.mp3`, `display-script.txt`, `glossary-mr.json`)
  - `projects/<slug>/artifacts/edit_plan.md`
  - `projects/<slug>/build/` (`aroll_trimmed.mp4`, `transcript_ms.json`, `explainer_timeline.json`, QA grids)
  - `projects/<slug>/assets/{aroll,audio,generated,broll}/` (synced to `public/assets/{aroll,audio,generated,broll}/`)
  - `projects/<slug>/src/` (`Root.tsx`, `AudioTimeline.tsx`, `scenes/Scene01..SceneXX.tsx`)
  - `projects/<slug>/output/<slug>_final.mp4` + `Final-edited-video/<slug>_final.mp4`

---

## Pipeline Order (Per Project)

1. **Initialize Project:** Run `python scripts/project.py init <slug> --mode <mode> --lang <mr|hi|en> --fps <30|60> --source <media> --activate`.
2. **Audio & Script Preprocessing:**
   - **Mode A (`talking-head` / `editorial-hybrid`):** `02-audio-silence-preprocessor` -> trims silences with 30ms padding into `build/aroll_trimmed.mp4` (and `public/assets/aroll/aroll_trimmed_30fps.mp4` for 30fps sources), extracts continuous `public/assets/audio/aroll_dialogue.wav`, and generates `build/transcript_ms.json`.
   - **Mode B (`faceless-explainer`):** `10-explainer-audio-director` -> sculpts pauses in `input/voiceover.*` into `public/assets/audio/voice_master.wav`, aligns `input/display-script.txt` into `build/transcript_ms.json`, and slices `2.0s`–`3.5s` beats in `build/explainer_timeline.json`.
3. **Interactive Storyboard Planning:** `03-storyboard-architect` -> generates the Two-Column Edit Plan (`artifacts/edit_plan.md`), enforcing a single cohesive visual system (zero style soup, zero raw CSS wireframes), Reels/Shorts safe zones (`y: 220–1380`, `x: 80–960`), and pauses for user approval.
4. **Asset & Editorial Illustration Generation:** `04-asset-hunter-swarm` -> generates text-free Nano Banana (`image-generator`) editorial illustrations in `public/assets/generated/` (staggered in pairs) and/or `09-omni-video-broll-generator` B-roll clips.
5. **Scene Coding:** `05-remotion-minimal-scenes` -> codes `src/scenes/Scene01.tsx..SceneXX.tsx` using `src/primitives/` and assembles `src/Root.tsx`.
6. **Adversarial & Visual QA Gate:** `06-adversarial-edit-verifier` -> runs `npx tsc --noEmit`, `inspect_frames.py` (`--mode talking-head` or `--mode explainer`), `verify_marathi_text.py`, and inspects a full-res 12-scene visual QA grid before full rendering.
7. **Foley, Two-Pass Loudness Master & Snapshot:** `07-foley-sound-designer` -> generates `src/AudioTimeline.tsx` (with `350–450ms` climax silence drops and `3 kHz` vocal-notched SFX at `-18` to `-24 dB`), renders the video, runs two-pass linear `loudnorm` (`-14.0 LUFS`, `<= -1.0 dBTP`), saves to `/Final-edited-video/<slug>_final.mp4`, and runs `python scripts/project.py save <slug>`.

## Non-Negotiable Rules

- **Native-FPS or 60fps Deterministic Math:** Use native `30fps` when source talking-head footage is `30fps` (eliminating 30→60fps frame-doubling judder and halving render time) or deterministic `60fps` for pure motion/explainer compositions (`1080x1920`).
- **Swarm File Isolation:** Scene workers edit ONLY their assigned `src/scenes/SceneXX.tsx`. Only the Coordinator edits `src/Root.tsx`.
- **Camera-Bound Textures:** Every animated scene (`P2`–`P10` and `KINETIC_BREATHER`) must nest `<TextureOverlay />` inside `<CameraRig>`.
- **Zero Raw ASR Leakage in Explainer Mode:** When `input/display-script.txt` is provided, never display raw Scribe/Whisper text on screen; always render the aligned `display-script.txt` tokens.

after completing the video render, save the final output video to /Final-edited-video
