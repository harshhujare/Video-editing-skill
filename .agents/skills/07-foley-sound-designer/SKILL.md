---
name: foley-sound-designer
description: Executes frame-accurate hybrid sound design using Video-to-Audio synthesis (MMAudio/Woosh) for B-roll Foley, acoustic-engineered UI transients for Remotion keyframes, sidechain vocal EQ carving, and final master export. Use after visual Remotion scenes pass adversarial verification for all sound effects generation, audio mixing, and final master render.
---

# Hybrid Video-to-Audio Foley & Keyframe SFX Engine

## Goal
Eliminate generic, off-beat AI sound effects by splitting audio design into two parallel tracks—Video-to-Audio Foley synthesis for B-roll clips and millisecond-locked acoustic transients for Remotion motion graphics—mixed with dynamic vocal-frequency carving and broadcast loudness normalization.

## Swarm Role Allocation
* **Coordinator Agent:** Enforces the visual verification gate (`adversarial-edit-verifier`), dispatches parallel Foley and UI-SFX workers, integrates `src/AudioTimeline.tsx` into `src/Root.tsx`, and runs the final render.
* **V2A Foley Worker Swarm (MMAudio / Sony Woosh):** Processes every `omni-video-agent` or stock B-roll clip (`public/assets/broll/*.mp4`) using frame-synchronized Video-to-Audio inference to generate realistic physical Foley.
* **UI-Transient Worker Swarm (Woosh-DFlow / ElevenLabs SFX):** Reads animation keyframes from `src/scenes/SceneXX.tsx` and `build/transcript_ms.json`, translates events via acoustic prompt templates, and places pre-lapped transients with pitch and stereo variation.
* **Audio Mix & Verifier Agent:** Applies dynamic sidechain vocal EQ carving (`2.5 kHz` pocket), optional 10-track music previews, and verifies `-14.0 LUFS` (`<= -1.0 dBTP`) broadcast loudness.

## Step-by-Step Execution Protocol

### Step 1: Visual Gate & Input Verification (Coordinator)
1. Confirm `06-adversarial-edit-verifier` has passed and `build/transcript_ms.json` plus either `build/aroll_trimmed.mp4` (Talking-Head Mode, `1080x1920 @ 60fps`) OR `build/voice_master.wav` / `public/assets/audio/voice_master.wav` (Explainer Mode) are locked.
2. Pause/confirm the visual cut before generating or mixing audio stems.

### Step 2: Parallel Video-to-Audio Foley Generation (V2A Workers)
For every B-roll or real-element clip containing physical movement (`public/assets/broll/*.mp4`):
1. Run **MMAudio (`large_44k` / `mmaudio-mcp`)** or **Sony `Woosh-VFlow`** with the video clip as visual conditioning and a strict negative prompt: `"music, melody, singing, speech, talking, crowd chatter, heavy reverb"`.
2. Prompt only for tactile physical textures matching the scene (e.g., *"crisp paper page turn and subtle pen scratch on desk, dry close-mic foley"* or *"soft ambient wind and subtle cloth movement"*).
3. Trim and gain-stage each resulting Foley stem to `-20 dB` RMS in `public/assets/sfx/foley/` so it adds physical realism without distracting from the speaker.

### Step 3: Keyframe-Locked UI & Motion Graphics SFX (UI-Transient Workers)
Scan every `src/scenes/SceneXX.tsx` and `build/transcript_ms.json` entry timestamp, then synthesize or pull crisp, dry transients using **Acoustic Studio Prompts** (always specifying `dry, zero reverb, tight transient, studio close-mic`) into `public/assets/sfx/` according to [sfx-mapping-rules.json](./references/sfx-mapping-rules.json):
1. **Pre-Lap Timing Rule:** Place every UI sound effect **`-35ms` (`-2` frames at `60fps`) BEFORE** the visual peak frame so the human brain perceives instant audiovisual lock.
2. **Acoustic Prompt Translation Table:**
   * `hook_text_enter` / `lower_third_slide` / `cameraSlideWhoosh`: *"Deep warm sub-bass thump at 60Hz paired with a tight, short silk air whoosh, 0.3 seconds, dry studio mix"* (`-15 dB`).
   * `selector_box_lock` / `arrow_draw` / `keywordReveal`: *"Crisp tactile mechanical camera shutter click and subtle muted wooden pop, 0.15 seconds, no echo"* (`-14 dB`).
   * `molecule_pop` / `circle_appear`: *"Soft organic water-droplet marimba pop with warm low-mid body, 0.2 seconds, dry"* (`-15 dB`).
   * `graph_rise` / `pattern_buildup` / `graphStepVertex`: *"Fast ascending digital ratchet ticks accelerating smoothly over 0.8 seconds, clean transient"* (`-17 dB`).
   * `shutter_breakthrough` / `impact`: *"Punchy cinematic low-end impact hit with crisp glass/ceramic crackle transient, tight decay"* (`-11 dB`).
   * `lineDrawLoop` (`P4`, `P5`, `P10`): Textured felt-highlighter or chalk drawing loop (`-12 dB`) synced to `strokeDashoffset` `[startFrame, endFrame]`.
3. **Anti-Machine-Gun Variation Rule:** Whenever 2 or more identical events fire within 3 seconds (`180` frames at `60fps`), automatically vary each subsequent hit by `+0.6` semitones (`playbackRate` increment `~0.035`) and pan them across the stereo field (`-18%` Left, `0%` Center, `+18%` Right).

### Step 4: Vocal-Pocket EQ Carving, Foley Gain Staging & Dramatic Silence Drops
1. **Continuous Master Dialogue Track (Mode A Talking-Head Law):**
   Never rely on unmuted `<OffthreadVideo>` clips for dialogue when cutting between talking-head A-roll and graphic scenes. Extract `public/assets/audio/aroll_dialogue.wav` (`48kHz` stereo) from `build/aroll_trimmed.mp4`, set `muted` on every `<OffthreadVideo startFrom={...} muted />` across all scenes, and mount `<Audio src={staticFile('assets/audio/aroll_dialogue.wav')} volume={1.0} />` continuously from `from={0}` in `src/AudioTimeline.tsx`.
2. **Pre-Baked `3 kHz` Vocal-Pocket Notch & `-18` to `-24 dB` Foley Mix:**
   - Process every active SFX file (`soft_click_L/C/R.wav`, `molecule_pop_L/C/R.wav`, `graph_step_tick.wav`, `minimal_whoosh.wav`, `raw_stamp_thud.wav`, `raw_growth_plonk.wav`) through FFmpeg `highpass=f=90,equalizer=f=3000:t=q:w=1.2:g=-4.5` into `public/assets/sfx/notched_*.wav`.
   - Mix all procedural foley hits strictly at **`-18 dB` to `-24 dB` below dialogue (`volume: 0.07` to `0.10`, stamp thud `0.14` in the silent pocket)** so Marathi consonants (`1.5 kHz – 4 kHz`) are never masked.
   - Pre-lap every SFX hit by **`-35ms`** (`-2` frames at `60fps`, `-1` frame at `30fps`).
3. **Dramatic Silence Drop Before Climax Stamp (`350–450ms` Rule):**
   - A `100ms` (6-frame) music drop sounds like an audio glitch rather than an intentional dramatic pause.
   - For climax twists or verdict stamp slams (e.g., *"एक रुपयाचीही वाढ झाली नाहीये"* → `₹0 वाढ` stamp slam), pull `bgmVolume` completely to **`0.0` for `350–450ms` (`12–15 frames` @ `30fps`, `21–27 frames` @ `60fps`)** leading into the impact, fire `notched_raw_stamp_thud.wav` cleanly inside the silent pocket, hold silence through the stamp decay, and bring BGM back subtly (`0.065`) on the next scene.

### Step 5: Music Ducking, Two-Pass Linear Loudness Master & Final Export
1. **Music Bed & End-Card Swell:** Duck BGM to `-23 dB` (`volume: 0.071`) under speech, swell gently to `0.13` during the `+2.0s` branded CTA end-card hold after voice finishes, and fade cleanly to `0.0` over the final `0.5s`.
2. **Two-Pass Linear Loudness Normalization (`-14.0 LUFS`, `<= -1.0 dBTP` — Mandatory):**
   Single-pass `loudnorm=I=-14.0:TP=-1.0` can overshoot true peak to `-0.9 dBTP` after AAC encoding. Always run **two-pass linear `loudnorm`** with `TP=-1.2`:
   - **Pass 1 (Measure):** `ffmpeg -hide_banner -i output/raw.mp4 -af "loudnorm=I=-14.0:TP=-1.2:LRA=7:print_format=json" -f null -`
   - **Pass 2 (Linear Master):** `ffmpeg -y -i output/raw.mp4 -c:v copy -af "loudnorm=I=-14.0:TP=-1.2:LRA=7:linear=true:measured_I=...:measured_TP=...:measured_LRA=...:measured_thresh=...:offset=..." -ar 48000 -ac 2 -c:a aac -b:a 192k -movflags +faststart output/final_master.mp4`
3. Copy the verified master into `/Final-edited-video` per workspace rules and verify `-14.0 ± 0.2 LUFS` and `input_tp <= -1.0 dBTP`.

## Verification
- Verify `output/final_master.mp4` exists, has `1080x1920 @ 60fps` video and `48kHz` stereo audio via `ffprobe`.
- Verify integrated loudness is `-14.0 LUFS` (`±0.5 LU`) and true peak `<= -1.0 dBTP` via `ffmpeg -af loudnorm=print_format=summary` / `volumedetect`.

## Constraints
* Never allow MMAudio or Woosh to generate background music inside an SFX stem; always pass `"music, melody, singing"` in `negative_prompt`.
* Never place a UI SFX hit at `0ms` or `+ms` relative to a visual peak keyframe; always pre-lap by `-35ms` (`-2` frames at `60fps`) for perceptual tightness.
* Never pass 2D Remotion typography/vector animations into a Video-to-Audio model; use keyframe-locked UI transients instead.
