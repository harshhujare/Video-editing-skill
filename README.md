# Agentic Video Studio Skills — Modular Remotion & Code-Driven Video Pipeline

An open-source **11-skill agentic video editing & generation studio** for AI coding assistants (**Google Antigravity**, **Claude Code**, **Cursor**, **Codex CLI**). Turn raw talking-head clips, ElevenLabs voiceovers, or plain text scripts into broadcast-mastered (`-14.0 LUFS`) vertical Reels/Shorts and animated explainers using **Remotion**, **Nano Banana (`image-generator`)**, **Omni-Video**, and **Lemo-Opuscar**.

---

## ✨ What You Can Edit or Generate (5 Modes)

| Mode | Input Required | Primary Skills Used | Best For |
|---|---|---|---|
| **Mode A — Talking-Head + Editorial Cutaways (`editorial-hybrid` / `talking-head`)** | Raw camera clip (`raw_clip.mp4`) | `02-audio-silence-preprocessor` → `03-storyboard-architect` → `04-asset-hunter-swarm` → `05-remotion-minimal-scenes` → `06-adversarial-edit-verifier` → `07-foley-sound-designer` (+ `08-marathi-devanagari-engine`) | Financial advisor Reels/Shorts, case studies, founder commentary |
| **Mode B — Faceless AI Voiceover Explainer (`faceless-explainer`)** | ElevenLabs voiceover (`voiceover.mp3/.wav`) + clean script (`display-script.txt`) | `10-explainer-audio-director` → `03-storyboard-architect` (50/30/20 split + camera handshakes) → `04-asset-hunter-swarm` → `05-remotion-minimal-scenes` → `06-adversarial-edit-verifier` (`--mode explainer`) → `07-foley-sound-designer` | Faceless YouTube Shorts / Instagram Reels, educational storytelling |
| **Mode C — Generative Video B-Roll & 3D Showcase (`generative-broll`)** | Raw clip or voiceover + script | `09-omni-video-broll-generator` (`omni-video-agent` / Pexels) + `05-remotion-minimal-scenes` (`P2_BROLL_TEXT`, `P7`, `P9`) | Cinematic 9:16 B-roll metaphors, 3D object callouts, rotoscoped back-text |
| **Mode D — 100% Code-Driven Short Film (`lemo-opuscar-film`)** | Topic or script + 1 of **99 Lemo-Opuscar styles** | `lemo-opuscar` (HTML5 Canvas / WebGL / Three.js + procedural score & foley, `0` video/image API credits) | Data storytelling, isometric diagrams, whiteboard explainers, archival investigations |
| **Mode E — Creator Style Cloning (`style-dna-extractor`)** | Up to 20 reference videos or a 4-color brand Lookbook | `01-style-dna-extractor` | Extracting custom creator motion templates (`arthur-225-catalog.json`) |

---

## 📦 Included Agent Skills (`.agents/skills/`)

1. **[`01-style-dna-extractor`](.agents/skills/01-style-dna-extractor/SKILL.md):** Deconstructs reference short-form videos and Lookbooks into a reusable catalog of 10 visual principles (`P1_CAPTION` through `P10_DARK_GRAPH`).
2. **[`02-audio-silence-preprocessor`](.agents/skills/02-audio-silence-preprocessor/SKILL.md):** Removes dead-air silences with `30ms` room-tone padding, exports native-FPS A-roll (`30fps` or `60fps`) plus continuous `48kHz` master dialogue (`aroll_dialogue.wav`), and aligns word timestamps.
3. **[`03-storyboard-architect`](.agents/skills/03-storyboard-architect/SKILL.md):** Plans a Two-Column Edit Plan Artifact (`artifacts/edit_plan.md`) enforcing the Announcement-vs.-Description rule, the **No Style Soup / No Raw CSS Wireframe Law**, spatial continuity across comparative graphs, Reels/Shorts safe zones (`y: 220–1380`, `x: 80–960`), regulatory disclaimers, and `+2.0s` branded CTA holds.
4. **[`04-asset-hunter-swarm`](.agents/skills/04-asset-hunter-swarm/SKILL.md):** Generates cohesive *Economist / Monocle*-style gouache-and-ink illustrations via Nano Banana (`image-generator`) with strict zero-text prompts and staggered rate-limit protection, alongside Wikimedia paintings, textures, and fonts.
5. **[`05-remotion-minimal-scenes`](.agents/skills/05-remotion-minimal-scenes/SKILL.md):** Builds modular Remotion scene components (`src/scenes/SceneXX.tsx`) using shared primitives (`<CameraRig>`, `<TextureOverlay>`, `<ArollCaptionBar>`, `<SharedDarkDatavizGrid>`, `<HalftoneStamp>`).
6. **[`06-adversarial-edit-verifier`](.agents/skills/06-adversarial-edit-verifier/SKILL.md):** Static AST + rendered-frame verifier (`inspect_frames.py`) plus a mandatory 12-scene visual QA grid gate catching orphan words, static textures, face/caption collisions, stamp overlaps, and missing `P6` quote marks before full render.
7. **[`07-foley-sound-designer`](.agents/skills/07-foley-sound-designer/SKILL.md):** Frame-accurate `-35ms` pre-lapped UI transients high-passed at `90 Hz` with a `-4.5 dB` vocal-pocket notch at `3 kHz` (`-18` to `-24 dB` below dialogue), `350–450ms` climax silence drops, and two-pass linear `loudnorm` (`-14.0 LUFS`, `<= -1.0 dBTP`).
8. **[`08-marathi-devanagari-engine`](.agents/skills/08-marathi-devanagari-engine/SKILL.md):** Specialized Marathi & bilingual Devanagari-Latin override with acoustic breath-pause verification, H.264 compression-safe font pairing (`Mukta SemiBold/ExtraBold` on captions, `Rozha One` on `66px+` solid canvases), `lineHeight >= 1.42` + `20px` Matra padding, `Intl.Segmenter` grapheme splitting, and `verify_marathi_text.py`.
9. **[`09-omni-video-broll-generator`](.agents/skills/09-omni-video-broll-generator/SKILL.md):** Palette-locked `9:16` generative B-roll and 3D object callouts via `omni-video-agent`.
10. **[`10-explainer-audio-director`](.agents/skills/10-explainer-audio-director/SKILL.md):** Dual-script alignment (`voiceover.mp3` + `display-script.txt`), dramatic pause sculpting, 50/30/20 beat slicing, and continuous virtual-camera transition handshakes for faceless explainers.
11. **[`lemo-opuscar`](.agents/skills/lemo-opuscar/SKILL.md) & [`sound-effects`](.agents/skills/sound-effects/SKILL.md):** 99 pure-code film styles and ElevenLabs SFX synthesis integration.

---

## 🚀 Quick Start

### Option A: Use only the Skills in your own project
Copy `.agents/skills/` into your workspace's `.agents/skills/` (or `~/.gemini/config/skills/` / `.claude/skills/`):

```bash
git clone https://github.com/harshhujare/Video-editing-skill.git
cp -r Video-editing-skill/.agents/skills/* /path/to/your-project/.agents/skills/
```

### Option B: Clone the full Modular Multi-Project Studio

```bash
git clone https://github.com/harshhujare/Video-editing-skill.git
cd Video-editing-skill
npm install
```

Use the built-in **Modular Project Manager (`scripts/project.py`)** so every video stays isolated under `projects/<slug>/`:

```bash
# 1. Initialize & activate a new Talking-Head / Editorial Hybrid video:
python scripts/project.py init my-first-reel --mode editorial-hybrid --lang mr --fps 30 --source path/to/raw_clip.mp4 --activate

# 2. Or initialize a Faceless AI Voiceover Explainer:
python scripts/project.py init my-explainer --mode faceless-explainer --lang en --fps 60 --source path/to/voiceover.mp3 --script path/to/display-script.txt --activate

# 3. List all projects in the studio:
python scripts/project.py list

# 4. Save active progress or switch between projects at any time:
python scripts/project.py save
python scripts/project.py load my-first-reel
```

---

## 🛠️ System Requirements
- **Node.js 20+** & **Remotion 4.x** (`npm install`)
- **FFmpeg 7+** (with `libx264` and `loudnorm` filter)
- **Python 3.11+** (`faster-whisper`, `Pillow`)
