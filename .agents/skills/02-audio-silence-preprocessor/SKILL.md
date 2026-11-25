---
name: audio-silence-preprocessor
description: Use when a raw talking-head video clip is provided for editing and needs dead-air silence removal with 30ms padding plus millisecond word-level timestamp alignment.
---

# Audio & Silence Preprocessor

## Overview

Transform raw talking-head video (`input/raw_clip.mp4`) into a jump-cut, silence-free master A-roll (`build/aroll_trimmed.mp4`) locked at `60fps` (`1080x1920`) paired with a frame- and millisecond-accurate word transcript (`build/transcript_ms.json`).

## Step-by-Step Instructions

1. **Detect Silences and Pad Speech Segments (30ms Buffer):**
   Run (note `--silence-threshold=-38dB` uses `=` so `argparse` does not parse `-38dB` as a flag):
   ```bash
   python .agents/skills/02-audio-silence-preprocessor/scripts/cut_and_transcribe.py --input input/raw_clip.mp4 --output-video build/aroll_trimmed.mp4 --output-transcript build/transcript_ms.json --silence-threshold=-38dB --min-silence-ms 180 --padding-ms 30 --fps 60
   ```
   - Keeps **30 milliseconds** of room tone before the first phoneme and after the last phoneme of every spoken segment so jump cuts sound crisp without clipping consonants.
   - Merges adjacent speech segments whose padded bounds overlap.

2. **Normalize Master A-Roll & Extract Continuous Dialogue Track for Remotion:**
   - The script automatically scales/crops to `1080x1920` (vertical 9:16) and outputs `build/aroll_trimmed.mp4` (`yuv420p`, `aac` audio at `48kHz`).
   - **Native-FPS A-Roll Copy (Anti-Judder Rule):** When the raw camera footage is `30fps` and the final Reel is rendered at native `30fps`, also export `public/assets/aroll/aroll_trimmed_30fps.mp4` (`-vf "fps=30,format=yuv420p" -an`) to avoid 30→60fps frame-doubling micro-judder and halve Remotion render time.
   - **Continuous Master Dialogue WAV (Mandatory for Mode A):** Always extract a continuous `48kHz` stereo dialogue WAV into `public/assets/audio/aroll_dialogue.wav`:
     ```bash
     ffmpeg -y -hide_banner -loglevel error -i build/aroll_trimmed.mp4 -vn -c:a pcm_s16le -ar 48000 -ac 2 public/assets/audio/aroll_dialogue.wav
     ```
     Mounting `aroll_dialogue.wav` continuously in `src/AudioTimeline.tsx` while muting `<OffthreadVideo muted startFrom={...} />` prevents audio dropouts during graphic cutaways and eliminates clicks at A-roll sequence boundaries.

3. **Generate Millisecond & Frame Word Timestamps (Plus Acoustic Breath Anchors):**
   - Runs WhisperX forced phoneme alignment (or `faster-whisper` / `openai-whisper` fallback) on `build/aroll_trimmed.mp4`.
   - For Marathi or code-switched Indian languages where Whisper may translate clauses to English or skip mid-clip segments, run `ffmpeg -af "silencedetect=noise=-32dB:d=0.10"` alongside direct audio slice inspection (`08-marathi-devanagari-engine` Pass 2) to anchor every clause boundary on true acoustic breath pauses.
   - Writes `build/transcript_ms.json`:
     ```json
     [
       { "word": "There's", "start_ms": 0, "end_ms": 240, "start_frame": 0, "end_frame": 14 },
       { "word": "four", "start_ms": 240, "end_ms": 480, "start_frame": 14, "end_frame": 29 }
     ]
     ```

## Verification

- Inspect `build/transcript_ms.json` to confirm:
  - Non-empty word array with monotonically increasing `start_ms` and `start_frame`.
  - Zero inter-word dead-air gaps exceeding `60ms` (30ms tail + 30ms lead padding) unless intentionally preserved.
- Probe `build/aroll_trimmed.mp4` with `ffprobe` to verify `1080x1920`, `60/1` fps, and matching audio/video stream durations.
