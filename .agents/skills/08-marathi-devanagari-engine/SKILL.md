---
name: marathi-devanagari-engine
description: Use whenever editing Marathi or code-switched Marathi-English videos to enforce dual-pass orthographic ASR verification, bilingual Devanagari-Latin script locking, Matra-safe bounding boxes, and grapheme-safe Remotion animations.
---

# Marathi Devanagari Typography & ASR Engine

## Overview

Specialized override for `audio-silence-preprocessor`, `storyboard-architect`, `asset-hunter-swarm`, `remotion-minimal-scenes`, and `adversarial-edit-verifier` whenever source footage is in Marathi or bilingual Marathi-English. Eliminates Devanagari ASR misspellings, clipped *Matras/Ukars*, and broken *Jodakshare* ligatures.

## Swarm Role Allocation

- **Coordinator Agent:** Detects Marathi audio, loads `input/glossary-mr.json` (copy from [glossary-mr.template.json](./references/glossary-mr.template.json) if absent), and enforces Marathi chunking and composite font rules across all workers.
- **Worker 1 (Acoustic Timestamp Worker):** Extracts raw word-level millisecond timestamps (`start_ms`, `end_ms`, `start_frame`, `end_frame`).
- **Worker 2 (Multimodal Marathi Proofreader):** Compares raw audio directly against the draft transcript to fix *Rhasva/Dirgha* (`ि/ई`, `ु/ऊ`), *Anusvara* (`ं`), retroflexes (`ण/न`, `ळ/ल`), and *Jodakshare* errors without shifting timestamps.
- **Verifier Agent:** Runs [verify_marathi_text.py](./scripts/verify_marathi_text.py) on transcripts and TSX scenes to reject dotted circles (`◌`), unattached vowel marks, `.split('')`, slanted Devanagari italics, or split postpositions.

## Step-by-Step Execution Protocol

### Step 1: 3-Step Dual-Pass Marathi Transcription & Script Locking

1. **Pass 1 — Acoustic Timing (`audio-silence-preprocessor` override):**
   Run `cut_and_transcribe.py` with forced Marathi acoustic alignment (`--language mr --model large-v3`, or Google Cloud Speech-to-Text V2 `mr-IN` Chirp 2) to generate `build/aroll_trimmed.mp4` (`1080x1920 @ 60fps`) and `build/transcript_ms_draft.json` (`--min-silence-ms 250 --padding-ms 30`).
   ```bash
   python .agents/skills/02-audio-silence-preprocessor/scripts/cut_and_transcribe.py --input input/raw_clip.mp4 --output-video build/aroll_trimmed.mp4 --output-transcript build/transcript_ms_draft.json --language mr --model large-v3 --min-silence-ms 250 --padding-ms 30 --fps 60
   ```
2. **Pass 2 — Multimodal Orthographic, Acoustic Pause & Glossary Correction:**
   Pass the trimmed audio (`build/aroll_trimmed.mp4`), `build/transcript_ms_draft.json`, and `input/glossary-mr.json` to the Proofreader Agent to produce `build/transcript_ms.json`.
   - **Whisper Translation / Skip Guard (Critical):** `faster-whisper` on Marathi (`--language mr`) frequently translates the first 15–25s into English or skips 5–8s mid-clip segments. Always run `ffmpeg -af "silencedetect=noise=-32dB:d=0.10"` on the trimmed audio to get exact acoustic breath pauses AND listen directly to `16kHz` WAV slices via `read_file` to verify 100% of the spoken Marathi clauses and anchor every scene boundary on a real breath pause.
   - Fix phonetic ASR errors (e.g., `म्युच्युअल`, `गॅरंटी`, `आर्थिक`, `चक्रवाढ व्याज`, `महागाई`, `मुद्दलमध्ये`, `आग्रहाखातर`).
   - **Timestamp Lock:** Preserve exact acoustic pause boundaries and monotonically increasing `start_ms`, `end_ms`, `start_frame`, and `end_frame` values.
3. **Pass 3 — Bilingual Script Standardization (Devanagari + Latin Hybrid):**
   - **Marathi words:** Render all Marathi nouns, verbs, adjectives, and postpositions in pure Unicode Devanagari (`गुंतवणूक`, `महागाईनुसार`, `मुद्दलमध्ये`, `वाढ`).
   - **Acronyms, English power terms, and numbers:** Keep universal acronyms (`SIP`, `SWP`, `EMI`, `FD`, `CAGR`), English financial terms used naturally in speech (`Mutual Fund`, `Post Office`, `Retirement`, `Pension`, `Valuation`, `Customer`, `Invest`, `Same`), currency symbols, and numbers (`₹30 लाख`, `₹15L`, `2022`) in crisp Latin script and Arabic numerals (`0-9`).

### Step 2: Compression-Safe Bilingual Font Stack (`Mukta ExtraBold` vs. `Rozha One`)

Configure `@font-face` rules in `src/styles/fonts.ts` so Devanagari (`U+0900-097F`) and Latin (`U+0000-00FF`) render without H.264 compression shimmer or verifier false positives:

- **A-Roll & Graphic Caption Pills (`36px–46px` over moving video or dark-frosted pills):**
  - Body (`600`): `Mukta SemiBold` (`Mukta-SemiBold.ttf`) + `Inter`. Never use `300`/`400` Light on Devanagari `< 56px`—mobile compression breaks the *Shirorekha*.
  - Emphasis Keyword (`**BOLD**`, `800`): **`Mukta ExtraBold` (`Mukta-ExtraBold.ttf`)**. **NEVER use `Rozha One` inside A-roll caption pills**—its razor-thin Didone hairlines and Matras shimmer and break up under Instagram/Reels H.264 compression over moving video.
- **Large Solid-Canvas Headlines (`66px–118px`) & `P6_QUOTE_SCENE` Closing Cards:**
  - Use **`Rozha One` (`RozhaOne-Regular.ttf`, weight `400`, zero italic)** for large Devanagari display titles (`लाख`, `दरमहा Pension + महागाईनुसार मुद्दल वाढ`) paired with **`Playfair Display Bold Italic`** for Latin numerals/terms (`₹30`).
- **No Inline `fontStyle: 'italic'` & Global `lineHeight >= 1.42` in Scene TSX Files:**
  - Register `PlayfairDisplay-BoldItalic.ttf` as its own font family (`family: 'Playfair Display Bold Italic', style: 'normal'`) in `src/styles/fonts.ts` so scene `.tsx` files never contain inline `fontStyle: 'italic'` (which `verify_marathi_text.py` flags whenever Devanagari exists in the same file).
  - Keep **every** numeric `lineHeight` in any Devanagari `.tsx` file **`>= 1.42`** (even on decorative Latin quote marks `“` / `”`—use `lineHeight: 1.42` with negative `marginBottom: -92` / `marginTop: -92` instead of `lineHeight: 0.65`, because `verify_marathi_text.py` audits all `lineHeight` numbers in Devanagari files).

### Step 3: Grammatical Phrase Chunking (4 to 5 Words Per Card)

1. Limit caption cards (`P1_CAPTION`, `P2_BROLL_TEXT`, and dual-font overlays) to **4 to 5 words** and **maximum 28 grapheme clusters** per card.
2. **SOV Grammatical Lock:** Never split a noun from its attached *Vibhakti Pratyaya* postposition (`-साठी`, `-मध्ये`, `-कडून`, `-पेक्षा`) or split a compound verb (`करून घ्या`, `वाढू शकते`) across two cards.
3. **Keyword Selection:** Assign `font_special` to the core anchor—financial/emotional nouns (`महागाई`, `पेंशन`, `चक्रवाढ व्याज`), warnings (`धोका`, `चूक`, `नुकसान`), or Latin/numeral metrics (`₹50 लाख`, `12%`).

### Step 4: Matra-Safe Bounding Boxes & Rotoscoped Back-Text

1. **Line Height & Vertical Padding:**
   - Enforce `lineHeight: 1.42` minimum on all multi-line Marathi lockups.
   - Add `paddingTop: 20` and `paddingBottom: 20` inside every wrapper using `overflow: 'hidden'` (including reveal masks) so upper *Matras/Velantis* (`ि, ी, े, ै, ो, ौ, ं`) and lower *Ukars/Rafars* (`ु, ू, ृ`) are never clipped.
2. **Rotoscoped Back-Text (`P2` / `P9` Layered Cutouts):**
   - When placing oversized Marathi display type (`150px`–`200px` in `Khand Bold` or `Rozha One`) behind a centered speaker cutout, position the top *Shirorekha* (`शिरोरेषा`) clearly **above** the speaker's shoulders so only the bottom ~25% of the glyphs dip behind the torso.

### Step 5: Grapheme-Safe Remotion Text Animation (`Intl.Segmenter`)

Never use `.split('')` or character-index slicing on Devanagari strings (it breaks ligatures into raw halants + dotted circles `◌`). Always iterate over extended grapheme clusters:

```tsx
export function splitMarathiAksharas(text: string): string[] {
  const segmenter = new Intl.Segmenter('mr', { granularity: 'grapheme' });
  return Array.from(segmenter.segment(text), (s) => s.segment);
}
```

## Verification (Mandatory Gate Before Presenting Drafts)

1. Run the Marathi Unicode & TSX verifier alongside `inspect_frames.py`:
   ```bash
   python .agents/skills/08-marathi-devanagari-engine/scripts/verify_marathi_text.py --transcript build/transcript_ms.json --scenes-dir src/scenes
   ```
2. Confirm **0 dotted circles (`◌`)**, **0 orphaned vowel marks**, **0 `.split('')` calls**, **0 Devanagari italics**, and **`lineHeight >= 1.42`**.
3. Present `artifacts/edit_plan.md` (two-column Marathi script) and sample caption frames to the user for regional phrasing and orthographic sign-off before full-video rendering.
