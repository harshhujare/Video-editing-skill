#!/usr/bin/env python3
"""
Explainer Audio Director & Dual-Script Aligner.
1. Normalizes a manual ElevenLabs voiceover to 48kHz 24-bit WAV (-16 LUFS, 80Hz HPF)
   while sculpting unintentional silences >650ms down to 320ms (preserving human cadence).
2. Aligns clean display-script.txt tokens onto exact millisecond/60fps frame timestamps
   via ElevenLabs Forced Alignment (en/hi), ElevenLabs Scribe, local Whisper, or pre-saved ASR JSON.
3. Slices beats into 2.0s-3.5s segments respecting [SCENE] breaks with a 50/30/20 visual
   engine allocation and matched camera transition handshakes.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
import uuid
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


SILENCE_START_RE = re.compile(r"silence_start:\s*([0-9.]+)")
SILENCE_END_RE = re.compile(r"silence_end:\s*([0-9.]+)")
SCENE_MARKER_RE = re.compile(r"^\s*\[SCENE(?::[^\]]*)?\]\s*$", re.IGNORECASE)
TRANSITION_CYCLE = ("zoom_through", "pan_left", "pan_up", "anchor_morph")

DEVANAGARI_APPROX = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ru",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "अं": "am",
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "च": "ch", "छ": "chh",
    "ज": "j", "झ": "jh", "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s",
    "ह": "h", "ळ": "l",
    "ा": "a", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ru",
    "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ं": "n", "ः": "h", "्": "",
    "ॉ": "o", "ॅ": "e",
}


def probe_duration(audio_path: Path) -> float:
    """Return media duration in seconds via ffprobe."""
    res = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return float(res.stdout.strip())


def detect_silences(
    audio_path: Path, noise_db: str = "-38dB", min_silence_s: float = 0.25
) -> list[tuple[float, float]]:
    """Detect silence intervals in seconds using ffmpeg silencedetect."""
    res = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", str(audio_path),
            "-af", f"silencedetect=noise={noise_db}:d={min_silence_s:.3f}",
            "-f", "null", "-",
        ],
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    silences: list[tuple[float, float]] = []
    current_start: float | None = None
    for line in res.stderr.splitlines():
        m_start = SILENCE_START_RE.search(line)
        if m_start:
            current_start = float(m_start.group(1))
            continue
        m_end = SILENCE_END_RE.search(line)
        if m_end and current_start is not None:
            silences.append((current_start, float(m_end.group(1))))
            current_start = None
    if current_start is not None:
        silences.append((current_start, probe_duration(audio_path)))
    return silences


def sculpt_silence_intervals(
    duration_s: float,
    silences: list[tuple[float, float]],
    edge_pad_s: float = 0.03,
    max_gap_s: float = 0.65,
    target_gap_s: float = 0.32,
) -> list[tuple[float, float]]:
    """
    Preserve human vocal cadence:
    - Trim leading/trailing silence (keeping edge_pad_s buffer).
    - Keep internal pauses <= max_gap_s untouched.
    - Compress internal pauses > max_gap_s down to target_gap_s (split symmetrically
      around adjacent speech boundaries so consonants are never clipped).
    """
    if duration_s <= 0:
        return []
    if not silences:
        return [(0.0, duration_s)]

    raw_speech: list[tuple[float, float]] = []
    cursor = 0.0
    for s_start, s_end in sorted(silences):
        s_start = max(0.0, s_start)
        s_end = min(duration_s, s_end)
        if s_start > cursor:
            raw_speech.append((cursor, s_start))
        cursor = max(cursor, s_end)
    if cursor < duration_s:
        raw_speech.append((cursor, duration_s))

    if not raw_speech:
        return [(0.0, duration_s)]

    intervals: list[tuple[float, float]] = []
    half_target = target_gap_s / 2.0

    for idx, (sp_start, sp_end) in enumerate(raw_speech):
        is_merged_with_prev = False
        if idx == 0:
            left = max(0.0, sp_start - edge_pad_s)
        else:
            prev_end = raw_speech[idx - 1][1]
            if (sp_start - prev_end) <= max_gap_s:
                is_merged_with_prev = True
                left = intervals[-1][0]
            else:
                left = max(prev_end, sp_start - half_target)

        if idx == len(raw_speech) - 1:
            right = min(duration_s, sp_end + edge_pad_s)
        else:
            next_start = raw_speech[idx + 1][0]
            gap_after = next_start - sp_end
            right = sp_end if gap_after <= max_gap_s else min(next_start, sp_end + half_target)

        if is_merged_with_prev:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], right))
        elif intervals and left <= intervals[-1][1]:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], right))
        elif right - left >= 0.04:
            intervals.append((left, right))

    return intervals or [(0.0, duration_s)]


def render_prepped_voice(
    input_audio: Path,
    out_wav: Path,
    public_wav: Path | None,
    noise_db: str = "-38dB",
    max_gap_ms: int = 650,
    target_gap_ms: int = 320,
) -> Path:
    """Sculpt silences, apply 80Hz HPF + -16 LUFS loudnorm, and export 48kHz 24-bit WAV."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    duration_s = probe_duration(input_audio)
    silences = detect_silences(input_audio, noise_db=noise_db, min_silence_s=0.25)
    intervals = sculpt_silence_intervals(
        duration_s,
        silences,
        edge_pad_s=0.03,
        max_gap_s=max_gap_ms / 1000.0,
        target_gap_s=target_gap_ms / 1000.0,
    )

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        seg_files: list[Path] = []
        for idx, (start, end) in enumerate(intervals):
            seg_path = tmp_dir / f"seg_{idx:04d}.wav"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", f"{start:.4f}", "-to", f"{end:.4f}",
                    "-i", str(input_audio),
                    "-af", "highpass=f=80",
                    "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le",
                    str(seg_path),
                ],
                check=True,
            )
            seg_files.append(seg_path)

        concat_wav = tmp_dir / "concat.wav"
        if len(seg_files) == 1:
            shutil.copyfile(seg_files[0], concat_wav)
        else:
            concat_list = tmp_dir / "concat.txt"
            concat_list.write_text(
                "\n".join(f"file '{p.as_posix()}'" for p in seg_files),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "concat", "-safe", "0", "-i", str(concat_list),
                    "-c", "copy", str(concat_wav),
                ],
                check=True,
            )

        subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(concat_wav),
                "-af", "loudnorm=I=-16.0:TP=-2.0:LRA=7",
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le",
                str(out_wav),
            ],
            check=True,
        )

    if public_wav is not None:
        public_wav.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out_wav, public_wav)

    return out_wav


def parse_display_script(script_text: str) -> tuple[list[list[str]], list[str]]:
    """
    Parse display-script.txt into manual scene groups (split on [SCENE] or blank lines)
    plus the flat ordered list of clean display tokens.
    """
    groups: list[list[str]] = []
    current: list[str] = []

    for raw_line in script_text.splitlines():
        line = raw_line.strip()
        if not line or SCENE_MARKER_RE.match(line):
            if current:
                groups.append(current)
                current = []
            continue
        cleaned_line = re.sub(r"\[SCENE(?::[^\]]*)?\]", " ", line, flags=re.IGNORECASE)
        tokens = [t.strip() for t in cleaned_line.split() if t.strip()]
        current.extend(tokens)

    if current:
        groups.append(current)

    flat = [w for grp in groups for w in grp]
    return groups, flat


def _phonetic_key(token: str) -> str:
    """Normalize Latin/Devanagari tokens into an approximate ASCII phonetic key."""
    norm = unicodedata.normalize("NFC", token).strip().lower()
    norm = re.sub(r"[^\w\u0900-\u097F₹%]", "", norm)
    if not norm:
        return ""
    out: list[str] = []
    for ch in norm:
        if ch in DEVANAGARI_APPROX:
            out.append(DEVANAGARI_APPROX[ch])
        elif ch == "₹":
            out.append("rs")
        elif ch == "%":
            out.append("pct")
        else:
            out.append(ch)
    return "".join(out)


RUPEE_SUFFIX_WORDS = {"रुपये", "रूपये", "रूपय", "रुपय", "रूपे", "रुपे", "rupees", "rupee"}
SCALE_UNIT_WORDS = {"लाख", "कोटी", "हजार", "करोड"}

LOCKED_BIGRAMS = {
    ("pocket", "money"),
    ("सुरू", "करतो"),
    ("करत", "नाही"),
    ("तयार", "होतो"),
    ("टाकत", "नाही"),
    ("राहू", "देतो"),
    ("fight", "मारतो"),
    ("पुढे", "आहे"),
    ("interesting", "आहे"),
    ("खूप", "interesting"),
    ("काय", "होतं"),
    ("असतात", "माहितीये"),
    ("किती", "पैसे"),
}


def _strip_punct(tok: str) -> str:
    return re.sub(r"[^\w\u0900-\u097F₹%]", "", unicodedata.normalize("NFC", tok)).lower()


def _token_similarity(display_tok: str, asr_span_tokens: list[str]) -> float:
    """Score alignment between one display token and 1..K ASR phonetic tokens."""
    d_raw = re.sub(r"[^\w\u0900-\u097F]", "", display_tok).lower()
    cleaned_asr = [re.sub(r"[^\w\u0900-\u097F]", "", t).lower() for t in asr_span_tokens]
    a_raw = "".join(cleaned_asr)

    # Reward absorbing a spoken rupee suffix ("रूपय"/"रुपये") into ₹-amounts or scale units ("लाख"/"कोटी").
    if (
        len(asr_span_tokens) == 2
        and cleaned_asr[1] in RUPEE_SUFFIX_WORDS
        and ("₹" in display_tok or d_raw in SCALE_UNIT_WORDS)
    ):
        if d_raw and d_raw == cleaned_asr[0]:
            return 1.25
        if "₹" in display_tok and re.search(r"[0-9a-z\u0900-\u097F]", cleaned_asr[0]):
            return 0.90

    if d_raw and d_raw == a_raw:
        return 1.0 + 0.1 * (len(asr_span_tokens) == 1)

    d_key = _phonetic_key(display_tok)
    a_key = "".join(_phonetic_key(t) for t in asr_span_tokens)

    # Numeric/acronym expansion bonus (e.g., "₹50,000" <-> 2-3 words, "SIP" <-> "एस आय पी").
    if re.search(r"[0-9₹%]", display_tok) and len(asr_span_tokens) >= 1:
        if re.search(r"[a-z0-9]", a_key) and len(asr_span_tokens) <= 4:
            if len(asr_span_tokens) in (2, 3):
                return 0.65 if cleaned_asr[-1] in RUPEE_SUFFIX_WORDS else 0.55
            return 0.45
    if re.fullmatch(r"[A-Z]{2,6}[.,!?:;\"'”’]*", display_tok):
        letters = re.sub(r"[^A-Za-z]", "", display_tok).lower()
        if len(asr_span_tokens) == len(letters):
            return 0.72
        if len(asr_span_tokens) == 1 and SequenceMatcher(None, letters, a_key).ratio() > 0.4:
            return 0.68

    if not d_key or not a_key:
        return 0.25 if len(asr_span_tokens) == 1 else 0.05

    ratio = SequenceMatcher(None, d_key, a_key).ratio()
    length_penalty = 0.08 * max(0, len(asr_span_tokens) - 1)
    return max(0.0, ratio - length_penalty)


def _grapheme_weight(tok: str) -> int:
    clean = re.sub(r"\s+", "", tok)
    return max(1, len(clean))


def map_display_script_to_asr(
    display_words: list[str],
    asr_words: list[dict[str, Any]],
    fps: int = 60,
    silences: list[tuple[float, float]] | None = None,
) -> list[dict[str, Any]]:
    """
    Align clean display_words verbatim onto ASR word timestamps via monotonic DP.
    Supports 1-to-many spans (e.g., '₹50,000' <- 'पन्नास हजार रुपये', 'SIP' <- 'एस आय पी')
    and compound number merges (e.g., '₹1 कोटी 48' <- '148').
    """
    if not display_words:
        return []
    if not asr_words:
        raise ValueError("Cannot map display words onto an empty ASR transcript.")

    n = len(display_words)
    m = len(asr_words)
    asr_texts = [str(w.get("word", "")).strip() for w in asr_words]

    neg_inf = -1e9
    dp = [[neg_inf] * (m + 1) for _ in range(n + 1)]
    back: list[list[tuple[int, int] | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0

    max_span = 4
    for i in range(1, n + 1):
        d_tok = display_words[i - 1]
        for j in range(1, m + 1):
            # 1 display word <- k ASR words (k = 1..max_span)
            for k in range(1, min(max_span, j) + 1):
                if dp[i - 1][j - k] <= neg_inf / 2:
                    continue
                score = dp[i - 1][j - k] + _token_similarity(d_tok, asr_texts[j - k : j])
                if score > dp[i][j]:
                    dp[i][j] = score
                    back[i][j] = (i - 1, j - k)

            # Fallback: 2 display words share 1 merged ASR word (rare ASR compound merge)
            if i >= 2 and dp[i - 2][j - 1] > neg_inf / 2:
                merged_score = _token_similarity(
                    display_words[i - 2] + display_words[i - 1], [asr_texts[j - 1]]
                ) - 0.15
                if dp[i - 2][j - 1] + merged_score > dp[i][j]:
                    dp[i][j] = dp[i - 2][j - 1] + merged_score
                    back[i][j] = (i - 2, j - 1)

            # Indian number compound merge: e.g. ["₹1", "कोटी", "48"] <- ["148"]
            if i >= 3 and dp[i - 3][j - 1] > neg_inf / 2:
                d_prev2 = re.sub(r"[^0-9]", "", display_words[i - 3])
                d_mid = _strip_punct(display_words[i - 2])
                d_cur = re.sub(r"[^0-9]", "", display_words[i - 1])
                a_digits = re.sub(r"[^0-9]", "", asr_texts[j - 1])
                if d_prev2 and d_cur and d_mid in SCALE_UNIT_WORDS and a_digits == (d_prev2 + d_cur):
                    tri_score = 1.05
                    if dp[i - 3][j - 1] + tri_score > dp[i][j]:
                        dp[i][j] = dp[i - 3][j - 1] + tri_score
                        back[i][j] = (i - 3, j - 1)

    if dp[n][m] <= neg_inf / 2:
        # Proportional fallback if token counts differ wildly (e.g., missing ASR section)
        total_start = int(asr_words[0]["start_ms"])
        total_end = int(asr_words[-1]["end_ms"])
        span = max(n, total_end - total_start)
        result: list[dict[str, Any]] = []
        for idx, word in enumerate(display_words):
            s_ms = total_start + int(round((idx / n) * span))
            e_ms = total_start + int(round(((idx + 1) / n) * span))
            e_ms = max(s_ms + 1, e_ms)
            s_f = int(round((s_ms / 1000.0) * fps))
            e_f = max(s_f + 1, int(round((e_ms / 1000.0) * fps)))
            result.append(
                {"word": word, "start_ms": s_ms, "end_ms": e_ms, "start_frame": s_f, "end_frame": e_f}
            )
        return result

    spans: list[tuple[int, int, int, int]] = []
    ci, cj = n, m
    while ci > 0 or cj > 0:
        prev = back[ci][cj]
        assert prev is not None
        pi, pj = prev
        spans.append((pi, ci, pj, cj))
        ci, cj = pi, pj
    spans.reverse()

    aligned: list[dict[str, Any]] = []
    for d_start, d_end, a_start, a_end in spans:
        t0 = int(asr_words[a_start]["start_ms"])
        t1 = max(t0 + 1, int(asr_words[a_end - 1]["end_ms"]))
        if silences:
            for sil_s, sil_e in silences:
                ss_ms = int(round(sil_s * 1000))
                se_ms = int(round(sil_e * 1000))
                # Trim leading/trailing silence bleed if speech remains >= 120ms
                if t0 < se_ms < t1 and t0 >= ss_ms - 50 and (t1 - se_ms) >= 120:
                    t0 = se_ms
                if t0 < ss_ms < t1 and t1 <= se_ms + 50 and (ss_ms - t0) >= 120:
                    t1 = ss_ms
        sub_words = display_words[d_start:d_end]
        weights = [_grapheme_weight(w) for w in sub_words]
        total_w = max(1, sum(weights))
        cum_w = 0
        for k, word in enumerate(sub_words):
            s_ms = t0 + int(round((cum_w / total_w) * (t1 - t0)))
            cum_w += weights[k]
            e_ms = max(s_ms + 1, t0 + int(round((cum_w / total_w) * (t1 - t0))))
            if aligned and s_ms < aligned[-1]["end_ms"]:
                # Allow overlap only if negligible; enforce monotonic start
                s_ms = max(s_ms, aligned[-1]["start_ms"])
                e_ms = max(s_ms + 1, e_ms)
            s_f = int(round((s_ms / 1000.0) * fps))
            e_f = max(s_f + 1, int(round((e_ms / 1000.0) * fps)))
            aligned.append(
                {
                    "word": word,
                    "start_ms": s_ms,
                    "end_ms": e_ms,
                    "start_frame": s_f,
                    "end_frame": e_f,
                }
            )
    return aligned


def _multipart_request(
    url: str,
    api_key: str,
    fields: dict[str, str],
    file_field: str,
    file_path: Path,
) -> dict[str, Any]:
    boundary = f"----AntigravityBoundary{uuid.uuid4().hex}"
    body = bytearray()

    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{value}\r\n".encode("utf-8"))

    mime_type = mimetypes.guess_type(file_path.name)[0] or "audio/wav"
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode("utf-8")
    )
    body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
    body.extend(file_path.read_bytes())
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "xi-api-key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ElevenLabs API error {exc.code}: {detail}") from exc


def run_elevenlabs_forced_alignment(
    wav_path: Path, clean_text: str, fps: int
) -> list[dict[str, Any]]:
    """Call ElevenLabs POST /v1/forced-alignment for English/Hindi exact alignment."""
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is required for --backend forced-alignment.")
    data = _multipart_request(
        "https://api.elevenlabs.io/v1/forced-alignment",
        api_key=api_key,
        fields={"text": clean_text},
        file_field="file",
        file_path=wav_path,
    )
    words: list[dict[str, Any]] = []
    for item in data.get("words", []):
        tok = str(item.get("text", "")).strip()
        if not tok:
            continue
        s_ms = int(round(float(item["start"]) * 1000))
        e_ms = max(s_ms + 1, int(round(float(item["end"]) * 1000)))
        s_f = int(round((s_ms / 1000.0) * fps))
        e_f = max(s_f + 1, int(round((e_ms / 1000.0) * fps)))
        words.append(
            {"word": tok, "start_ms": s_ms, "end_ms": e_ms, "start_frame": s_f, "end_frame": e_f}
        )
    return words


def run_elevenlabs_scribe(wav_path: Path, language: str) -> list[dict[str, Any]]:
    """Call ElevenLabs Scribe STT (POST /v1/speech-to-text) with word timestamps."""
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is required for --backend scribe.")
    fields = {
        "model_id": "scribe_v1",
        "timestamps_granularity": "word",
    }
    if language and language != "auto":
        fields["language_code"] = language
    data = _multipart_request(
        "https://api.elevenlabs.io/v1/speech-to-text",
        api_key=api_key,
        fields=fields,
        file_field="file",
        file_path=wav_path,
    )
    words: list[dict[str, Any]] = []
    for item in data.get("words", []):
        if item.get("type") not in (None, "word"):
            continue
        tok = str(item.get("text", "")).strip()
        if not tok:
            continue
        s_ms = int(round(float(item["start"]) * 1000))
        e_ms = max(s_ms + 1, int(round(float(item["end"]) * 1000)))
        words.append({"word": tok, "start_ms": s_ms, "end_ms": e_ms})
    return words


def run_local_whisper(wav_path: Path, language: str, model_size: str = "large-v3") -> list[dict[str, Any]]:
    """Run faster-whisper or openai-whisper locally to obtain raw word timestamps."""
    lang_arg = None if language == "auto" else language
    words: list[dict[str, Any]] = []
    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(wav_path), word_timestamps=True, language=lang_arg)
        for seg in segments:
            for w in getattr(seg, "words", []) or []:
                tok = w.word.strip()
                if tok:
                    words.append(
                        {
                            "word": tok,
                            "start_ms": int(round(float(w.start) * 1000)),
                            "end_ms": max(
                                int(round(float(w.start) * 1000)) + 1,
                                int(round(float(w.end) * 1000)),
                            ),
                        }
                    )
        return words
    except ImportError:
        pass

    import whisper  # type: ignore

    model = whisper.load_model(model_size)
    kwargs: dict[str, Any] = {"word_timestamps": True}
    if lang_arg:
        kwargs["language"] = lang_arg
    result = model.transcribe(str(wav_path), **kwargs)
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            tok = str(w["word"]).strip()
            if tok:
                s_ms = int(round(float(w["start"]) * 1000))
                e_ms = max(s_ms + 1, int(round(float(w["end"]) * 1000)))
                words.append({"word": tok, "start_ms": s_ms, "end_ms": e_ms})
    return words


def _is_forbidden_split(left_tok: str, right_tok: str) -> bool:
    """Return True if splitting between left_tok and right_tok breaks a locked phrase or number unit."""
    l_clean = _strip_punct(left_tok)
    r_clean = _strip_punct(right_tok)
    if (l_clean, r_clean) in LOCKED_BIGRAMS:
        return True
    if re.search(r"[0-9₹]", left_tok) and r_clean in (SCALE_UNIT_WORDS | {"वर्षं", "वर्षे", "वर्षांनंतर"}):
        return True
    # Keep "१ कोटी ४८ लाख" together
    if l_clean in SCALE_UNIT_WORDS and re.search(r"^[0-9]+$", r_clean):
        return True
    return False


def _assign_engines_50_30_20(beats: list[list[dict[str, Any]]]) -> list[tuple[str, str]]:
    """Assign engines across all beats to hit ~50% remotion_motion, ~30% omni_broll, ~20% kinetic_breather."""
    n = len(beats)
    if n == 0:
        return []
    target_k = round(n * 0.20)
    target_o = round(n * 0.30)
    target_r = n - target_k - target_o
    quotas = {"remotion_motion": target_r, "omni_broll": target_o, "kinetic_breather": target_k}

    scored: list[tuple[int, dict[str, float]]] = []
    for idx, beat in enumerate(beats):
        text = " ".join(w["word"] for w in beat)
        has_num = bool(re.search(r"[0-9₹%]", text))
        has_q = "?" in text
        has_excl = "!" in text
        is_short = len(beat) <= 6

        r_score = (3.0 if has_num else 0.0) + (1.5 if any(k in text for k in ("लाख", "कोटी", "corpus", "वर्षं")) else 0.0)
        k_score = (3.5 if has_q else 0.0) + (2.0 if (has_excl and not has_num) else 0.0) + (1.5 if is_short else 0.0) - (1.5 if has_num and not has_q else 0.0)
        o_score = (2.5 if not has_num else 0.5) + (1.5 if any(k in text for k in ("वडील", "मुलगा", "मुलांना", "fight", "इन्व्हेस्टमेंट", "पहिला", "दुसरा", "तिसरा")) else 0.0)
        scored.append((idx, {"remotion_motion": r_score, "omni_broll": o_score, "kinetic_breather": k_score}))

    assignments: dict[int, str] = {}
    # Assign kinetic_breather first (highest affinity beats), then omni_broll, then remotion_motion
    remaining_indices = set(range(n))
    for engine in ("kinetic_breather", "omni_broll", "remotion_motion"):
        q = quotas[engine]
        if q <= 0:
            continue
        ranked = sorted(
            remaining_indices,
            key=lambda i: (scored[i][1][engine] - max(v for k, v in scored[i][1].items() if k != engine), -i),
            reverse=True,
        )
        for i in ranked[:q]:
            assignments[i] = engine
            remaining_indices.remove(i)

    motion_cycle = ("P9_OBJECT_CALLOUT", "P5_LINE_ILLUSTRATION", "P8_SIDE_ILLUSTRATION", "P10_DARK_GRAPH", "P4_LINE_TEXT")
    motion_idx = 0
    results: list[tuple[str, str]] = []
    for idx, beat in enumerate(beats):
        eng = assignments[idx]
        text = " ".join(w["word"] for w in beat)
        if eng == "kinetic_breather":
            results.append((eng, "KINETIC_BREATHER"))
        elif eng == "omni_broll":
            results.append((eng, "P2_BROLL_TEXT"))
        else:
            if any(k in text for k in ("कोटी", "%", "₹64", "₹61")):
                principle = "P10_DARK_GRAPH" if ("कोटी" in text or "%" in text) else "P8_SIDE_ILLUSTRATION"
            elif any(k in text for k in ("सलग", "10 वर्षं", "20 वर्षं", "30 वर्षं")):
                principle = "P5_LINE_ILLUSTRATION"
            else:
                principle = motion_cycle[motion_idx % len(motion_cycle)]
                motion_idx += 1
            results.append((eng, principle))
    return results


def _partition_group_dp(
    grp: list[dict[str, Any]],
    g_start_ms: int,
    g_end_ms: int,
    min_beat_ms: int,
    max_beat_ms: int,
) -> list[tuple[list[dict[str, Any]], int, int]]:
    """Partition one manual [SCENE] group into contiguous [2.0s, 3.5s] grammar-safe beats."""
    n = len(grp)
    if n == 0:
        return []
    total_dur = g_end_ms - g_start_ms
    if total_dur <= max_beat_ms or n <= 2:
        return [(grp, g_start_ms, g_end_ms)]

    inf = 1e15
    dp = [inf] * (n + 1)
    prev_idx = [-1] * (n + 1)
    dp[0] = 0.0
    ideal_ms = (min_beat_ms + max_beat_ms) / 2.0

    for j in range(1, n + 1):
        beat_end = g_end_ms if j == n else int(grp[j]["start_ms"])
        split_penalty = 0.0
        if j < n:
            left_w = grp[j - 1]["word"]
            right_w = grp[j]["word"]
            if _is_forbidden_split(left_w, right_w):
                split_penalty += 1e7
            if re.search(r"[.,।?!;:]$", left_w):
                split_penalty -= 600_000.0
            gap_ms = int(grp[j]["start_ms"]) - int(grp[j - 1]["end_ms"])
            if gap_ms >= 120:
                split_penalty -= 250_000.0

        for i in range(j):
            if dp[i] >= inf / 2:
                continue
            beat_start = g_start_ms if i == 0 else int(grp[i]["start_ms"])
            dur = beat_end - beat_start
            if dur <= 0:
                continue
            dur_cost = (dur - ideal_ms) ** 2
            if dur < min_beat_ms:
                dur_cost += 5e7 + 50_000.0 * (min_beat_ms - dur)
            elif dur > max_beat_ms:
                dur_cost += 5e7 + 50_000.0 * (dur - max_beat_ms)
            if (j - i) == 1:
                dur_cost += 2e6
            cand = dp[i] + dur_cost + split_penalty
            if cand < dp[j]:
                dp[j] = cand
                prev_idx[j] = i

    if prev_idx[n] == -1:
        return [(grp, g_start_ms, g_end_ms)]

    spans: list[tuple[int, int]] = []
    cur = n
    while cur > 0:
        p = prev_idx[cur]
        spans.append((p, cur))
        cur = p
    spans.reverse()

    out: list[tuple[list[dict[str, Any]], int, int]] = []
    for i, j in spans:
        b_start = g_start_ms if i == 0 else int(grp[i]["start_ms"])
        b_end = g_end_ms if j == n else int(grp[j]["start_ms"])
        out.append((grp[i:j], b_start, b_end))
    return out


def slice_explainer_beats(
    aligned_words: list[dict[str, Any]],
    manual_groups: list[list[str]],
    fps: int = 60,
    min_beat_ms: int = 2000,
    max_beat_ms: int = 3500,
    total_duration_ms: int | None = None,
) -> dict[str, Any]:
    """
    Slice aligned words into contiguous 2.0s-3.5s beats respecting manual [SCENE] / paragraph breaks,
    assigning ~50/30/20 engines and matched enter/exit camera transition handshakes.
    """
    if not aligned_words:
        return {"fps": fps, "width": 1080, "height": 1920, "mode": "explainer", "scenes": []}

    cursor = 0
    group_slices: list[list[dict[str, Any]]] = []
    for grp in manual_groups:
        take = aligned_words[cursor : cursor + len(grp)]
        if take:
            group_slices.append(take)
        cursor += len(grp)
    if cursor < len(aligned_words):
        group_slices.append(aligned_words[cursor:])

    end_bound_ms = max(
        int(aligned_words[-1]["end_ms"]),
        int(total_duration_ms) if total_duration_ms is not None else int(aligned_words[-1]["end_ms"]),
    )

    beat_records: list[tuple[list[dict[str, Any]], int, int]] = []
    for g_idx, grp in enumerate(group_slices):
        g_start = 0 if (g_idx == 0 and int(grp[0]["start_ms"]) <= 200) else int(grp[0]["start_ms"])
        g_end = int(group_slices[g_idx + 1][0]["start_ms"]) if (g_idx + 1 < len(group_slices)) else end_bound_ms
        beat_records.extend(_partition_group_dp(grp, g_start, g_end, min_beat_ms, max_beat_ms))

    engine_assignments = _assign_engines_50_30_20([b[0] for b in beat_records])
    counts = {"remotion_motion": 0, "omni_broll": 0, "kinetic_breather": 0}
    scenes: list[dict[str, Any]] = []

    for i, (beat, start_ms, end_ms) in enumerate(beat_records):
        start_frame = int(round((start_ms / 1000.0) * fps)) if i == 0 else scenes[-1]["end_frame"]
        end_frame = max(start_frame + 24, int(round((end_ms / 1000.0) * fps)))
        engine, principle = engine_assignments[i]
        counts[engine] += 1

        enter_type = "none" if i == 0 else scenes[-1]["exit_transition"]["type"]
        exit_type = "none" if i == len(beat_records) - 1 else TRANSITION_CYCLE[i % len(TRANSITION_CYCLE)]

        scenes.append(
            {
                "scene_id": f"Scene{i + 1:02d}",
                "engine": engine,
                "principle_id": principle,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "start_frame": start_frame,
                "end_frame": end_frame,
                "duration_frames": end_frame - start_frame,
                "text": " ".join(w["word"] for w in beat),
                "words": beat,
                "enter_transition": {"type": enter_type, "duration_frames": 0 if enter_type == "none" else 18},
                "exit_transition": {"type": exit_type, "duration_frames": 0 if exit_type == "none" else 18},
            }
        )

    return {
        "fps": fps,
        "width": 1080,
        "height": 1920,
        "mode": "explainer",
        "total_duration_ms": end_bound_ms,
        "total_duration_frames": scenes[-1]["end_frame"] if scenes else 0,
        "engine_counts": counts,
        "scenes": scenes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual ElevenLabs Voiceover Ingest & Beat Choreographer.")
    parser.add_argument("--audio", required=True, help="Input voiceover (.mp3/.wav).")
    parser.add_argument("--script", required=True, help="Clean display-script.txt path.")
    parser.add_argument("--language", default="mr", help="Language code: en, hi, mr, or auto.")
    parser.add_argument(
        "--backend",
        choices=["forced-alignment", "scribe", "whisper", "asr-json"],
        default="scribe",
    )
    parser.add_argument("--asr-json", help="Pre-extracted ASR JSON file when using --backend asr-json.")
    parser.add_argument("--whisper-model", default="large-v3")
    parser.add_argument("--out-wav", default="build/voice_master.wav")
    parser.add_argument("--public-wav", default="public/assets/audio/voice_master.wav")
    parser.add_argument("--out-transcript", default="build/transcript_ms.json")
    parser.add_argument("--out-timeline", default="build/explainer_timeline.json")
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--skip-audio-prep", action="store_true")
    args = parser.parse_args()

    audio_path = Path(args.audio).resolve()
    script_path = Path(args.script).resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"Display script not found: {script_path}")

    script_text = script_path.read_text(encoding="utf-8")
    manual_groups, display_words = parse_display_script(script_text)
    if not display_words:
        raise ValueError(f"No display tokens found in {script_path}")

    out_wav = Path(args.out_wav).resolve()
    public_wav = Path(args.public_wav).resolve() if args.public_wav else None
    if not args.skip_audio_prep:
        if not audio_path.exists():
            raise FileNotFoundError(f"Voiceover audio not found: {audio_path}")
        render_prepped_voice(audio_path, out_wav, public_wav)
        print(f"Prepped voice master: {out_wav}")
    elif not out_wav.exists():
        out_wav = audio_path

    silences = detect_silences(out_wav, noise_db="-36dB", min_silence_s=0.18) if out_wav.exists() else []
    total_duration_ms = int(round(probe_duration(out_wav) * 1000)) if out_wav.exists() else None

    if args.backend == "forced-alignment":
        aligned = run_elevenlabs_forced_alignment(out_wav, " ".join(display_words), args.fps)
    else:
        if args.backend == "asr-json":
            if not args.asr_json:
                raise ValueError("--asr-json is required when --backend asr-json is selected.")
            raw_asr = json.loads(Path(args.asr_json).read_text(encoding="utf-8"))
            asr_words = raw_asr if isinstance(raw_asr, list) else raw_asr.get("words", [])
        elif args.backend == "scribe":
            asr_words = run_elevenlabs_scribe(out_wav, args.language)
        else:
            asr_words = run_local_whisper(out_wav, args.language, args.whisper_model)

        aligned = map_display_script_to_asr(display_words, asr_words, fps=args.fps, silences=silences)

    out_transcript = Path(args.out_transcript).resolve()
    out_transcript.parent.mkdir(parents=True, exist_ok=True)
    out_transcript.write_text(json.dumps(aligned, indent=2, ensure_ascii=False), encoding="utf-8")

    timeline = slice_explainer_beats(
        aligned,
        manual_groups,
        fps=args.fps,
        total_duration_ms=total_duration_ms,
    )
    out_timeline = Path(args.out_timeline).resolve()
    out_timeline.parent.mkdir(parents=True, exist_ok=True)
    out_timeline.write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"Wrote {len(aligned)} display-locked words to {out_transcript} "
        f"and {len(timeline['scenes'])} explainer scenes to {out_timeline}."
    )


if __name__ == "__main__":
    main()
