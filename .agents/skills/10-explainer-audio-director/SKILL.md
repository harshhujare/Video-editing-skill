---
name: explainer-audio-director
description: Replaces 02-audio-silence-preprocessor for faceless AI voiceover explainers. Ingests a manually generated ElevenLabs voiceover (input/voiceover.mp3 or .wav) and clean display script (input/display-script.txt), sculpts dead-air pauses without ruining dramatic cadence, locks display tokens to millisecond timestamps (Forced Alignment for en/hi, Scribe/Whisper + Dual-Script Sequence Mapper for mr), slices 2.0-3.5s 50/30/20 motion beats, and writes shared camera transition handshakes.
---

# Explainer Audio Director & Beat Choreographer

## Overview

Replaces `02-audio-silence-preprocessor` whenever producing a **faceless AI voiceover explainer** (no talking-head A-roll). Takes a human-directed ElevenLabs audio export (`input/voiceover.mp3` or `input/voiceover.wav`) and its clean on-screen script (`input/display-script.txt`), preserves vocal cadence while tightening unintentional silences, maps clean display tokens (e.g., `₹50,000`, `SIP`, clean Devanagari) onto exact millisecond/frame timestamps (`build/transcript_ms.json` at `60fps`), and outputs `build/explainer_timeline.json` + `artifacts/edit_plan.md` inputs for the rendering swarms.

## Dual-Script Ingest Convention

Drop two files into `input/`:
1. `input/voiceover.mp3` (or `input/voiceover.wav`): Your finished, ear-approved export from ElevenLabs Studio (with phonetic spellings/ellipses/expressive tags baked into the audio performance).
2. `input/display-script.txt`: The exact clean text you want rendered on screen (e.g., `₹50,000`, `SIP`, proper Marathi `ळ` and *anusvara* spellings), with optional `[SCENE]` markers or blank lines where hard visual shifts are desired.

## Swarm Role Allocation

* **Coordinator Agent:** Analyzes narrative rhythm, establishes the 4-color Lookbook theme (`neutral_dark`, `neutral_light`, `accent_bright`, `ink_muted`), enforces the 50/30/20 visual engine split, and assigns matched camera transition handshakes.
* **Worker 1 (Audio Prep & Dual-Script Aligner):** Runs `prep_and_align_explainer.py` to normalize `voiceover.*` into `build/voice_master.wav` (and `public/assets/audio/voice_master.wav`), runs language-appropriate alignment, and maps `display-script.txt` tokens onto exact millisecond + `60fps` frame timestamps in `build/transcript_ms.json`.
* **Worker 2 (Beat Slicer & Transition Choreographer):** Slices the narration into `2.0s`–`3.5s` (`120`–`210` frames at `60fps`) visual beats in `build/explainer_timeline.json` with `enter_transition` and `exit_transition` contracts.
* **Verifier Agent:** Confirms zero timestamp drift, verifies every word in `build/transcript_ms.json` matches `input/display-script.txt` verbatim, runs `verify_marathi_text.py` for Marathi scripts, and confirms adjacent scenes share matching transition contracts.

## Step-by-Step Execution Protocol

### Step 1: Audio Cleanup & Pause Sculpting (Worker 1)

Run:
```bash
python .agents/skills/10-explainer-audio-director/scripts/prep_and_align_explainer.py \
  --audio input/voiceover.mp3 \
  --script input/display-script.txt \
  --language mr \
  --backend scribe \
  --out-wav build/voice_master.wav \
  --public-wav public/assets/audio/voice_master.wav \
  --out-transcript build/transcript_ms.json \
  --out-timeline build/explainer_timeline.json
```

What Step 1 performs automatically:
1. Converts `input/voiceover.*` to `48kHz`, 24-bit WAV (`pcm_s24le`) at `build/voice_master.wav` (and copies to `public/assets/audio/voice_master.wav` for Remotion `<Audio>`).
2. Applies an `80Hz` high-pass filter and normalizes vocal loudness to `-16 LUFS` (`true peak <= -2.0 dBTP`).
3. **Preserve Human Pacing Rule:** Never strip pauses aggressively like a talking-head jump-cut. Trim leading/trailing silence (`30ms` pad) and compress unintentional internal gaps exceeding `650ms` down to `320ms`—keeping intentional dramatic cadence intact.

### Step 2: Language-Aware Dual-Script Alignment (Worker 1)

Lock `input/display-script.txt` to `build/voice_master.wav` to generate `build/transcript_ms.json` (`[{ word, start_ms, end_ms, start_frame, end_frame }]` at `60fps`):
* **English or Hindi (`--language en` or `hi`):** Use ElevenLabs Forced Alignment (`POST /v1/forced-alignment`, `--backend forced-alignment` with `ELEVENLABS_API_KEY`) passing `build/voice_master.wav` and the cleaned `display-script.txt` directly for exact word/character timestamps.
* **Marathi or Code-Switched Marathi-English (`--language mr`):**
  1. Extract raw spoken word timestamps via **ElevenLabs Scribe** (`--backend scribe`, `language_code: "mr"`, `timestamps_granularity: "word"`) or local Whisper / `ai4bharat/indicwav2vec_v1_marathi` (`--backend whisper` or `--asr-json <file>`).
  2. Run the **Display-Script Sequence Mapper** inside `prep_and_align_explainer.py` (dynamic programming + phonetic normalization) to snap every spoken phonetic span (e.g., `"पन्नास हजार रुपये"` or `"एस आय पी"`) to its clean display token (`"₹50,000"`, `"SIP"`), inheriting the exact `start_ms` of the first phonetic word and `end_ms` of the last.
  3. **Verify:** Every word in `build/transcript_ms.json` matches `input/display-script.txt` verbatim—zero raw ASR spelling errors allowed on screen.

### Step 3: 50/30/20 Beat Slicing & Camera Transition Handshakes (Worker 2 + Coordinator)

Slice `build/transcript_ms.json` into sequential visual beats (`Scene01`..`SceneN`) in `build/explainer_timeline.json`:
1. **Respect Manual Scene Breaks:** Any `[SCENE]` marker or blank line inside `input/display-script.txt` forces a hard beat boundary.
2. **2.0 to 3.5 Second Momentum:** Split longer clauses at natural syntactic boundaries (`120`–`210` frames at `60fps`; never splitting Marathi *Vibhakti* postpositions or leaving `< 24`-frame orphan words).
3. **50/30/20 Visual Engine Split:**
   * **50% Remotion Full-Screen Motion (`remotion_motion` -> `P4_LINE_TEXT`, `P5_LINE_ILLUSTRATION`, `P7_CENTER_ILLUSTRATION`, `P8_SIDE_ILLUSTRATION`, `P9_OBJECT_CALLOUT`, `P10_DARK_GRAPH`):** Numbers, compounding graphs, split comparisons, checklists, and shadowed 3D callouts.
   * **30% Generative Storytelling Clips (`omni_broll` -> `P2_BROLL_TEXT` via `09-omni-video-broll-generator`):** High-emotion metaphors, scenarios, and rotoscoped back-text sequences.
   * **20% Kinetic Typography Breathers (`kinetic_breather` -> `KINETIC_BREATHER` / `P6_QUOTE_SCENE`):** Minimalist full-screen statements in the `neutral_dark` + `accent_bright` Lookbook palette during rhetorical questions, narrative pivots, or thesis punches (replacing talking-head `P1_CAPTION` A-roll cuts).
4. **Shared Camera Transition Handshakes:** Assign matched `exit_transition` and `enter_transition` contracts (`zoom_through`, `pan_left`, `pan_up`, `anchor_morph`, or `none`) between adjacent scenes (`scene[i].exit_transition.type === scene[i+1].enter_transition.type`) so parallel `05-remotion-minimal-scenes` workers produce one continuous virtual camera.

### Step 4: Two-Column Storyboard Gate

Hand off `build/explainer_timeline.json` and `build/transcript_ms.json` to `03-storyboard-architect` to generate `artifacts/edit_plan.md` (with visual engine, `omni-video-agent` prompts, and transition contracts on the left, and exact `display-script.txt` lines + millisecond/frame spans on the right). Pause for user approval before launching parallel asset and scene swarms.

## Constraints

* Never regenerate or alter the user's manual ElevenLabs voiceover via TTS API.
* Never display raw Scribe/Whisper text on screen when `input/display-script.txt` is present; always map and render the verified `display-script.txt` tokens.
* Never mount `P1_CAPTION` talking-head A-roll scenes in Explainer Mode unless explicit camera footage is provided.
* Always lock timeline math to `60fps` (`1080x1920`) and ensure adjacent scene transition handshakes match (`exit_transition.type === next.enter_transition.type`).
