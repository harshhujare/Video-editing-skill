#!/usr/bin/env python3
"""
Verify Marathi Devanagari transcripts and Remotion TSX scene files for:
1. Broken Unicode ligatures / dotted circles (U+25CC)
2. Orphaned Devanagari combining marks or trailing bare virama/halant (U+094D)
3. Subtitle cards exceeding 5 words or 28 grapheme clusters
4. Forbidden `.split('')` / `.split("")` calls in Remotion components
5. Missing `Intl.Segmenter`, Devanagari italic styling, or tight `lineHeight < 1.42`
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
DOTTED_CIRCLE = "\u25CC"
VIRAMA = "\u094D"
COMBINING_DEVANAGARI = set(
    [chr(c) for c in range(0x0900, 0x0904)]
    + [chr(c) for c in range(0x093A, 0x0950)]
    + [chr(c) for c in range(0x0951, 0x0958)]
    + [chr(c) for c in range(0x0962, 0x0964)]
)

CHAR_SPLIT_RE = re.compile(r"""\.split\(\s*(['"])\1\s*\)""")
LINE_HEIGHT_RE = re.compile(r"""lineHeight\s*:\s*([0-9]+(?:\.[0-9]+)?)""")
ITALIC_RE = re.compile(r"""fontStyle\s*:\s*['"]italic['"]""")


def count_aksharas(text: str) -> int:
    """Count Devanagari grapheme clusters (Aksharas) + non-Devanagari base chars."""
    clusters = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        clusters += 1
        i += 1
        while i < n:
            nxt = text[i]
            if nxt == VIRAMA:
                i += 1
                # Virama joins the following consonant into the same Akshara cluster.
                if i < n and "\u0915" <= text[i] <= "\u0939":
                    i += 1
                    continue
                break
            if nxt in COMBINING_DEVANAGARI or unicodedata.combining(nxt):
                i += 1
                continue
            break
    return clusters


def check_unicode_text(text: str, context: str) -> list[str]:
    issues: list[str] = []
    if DOTTED_CIRCLE in text:
        issues.append(f"{context}: Contains dotted circle (◌ / U+25CC) indicating broken ligature.")
    for token in text.split():
        if token and token[0] in COMBINING_DEVANAGARI:
            issues.append(f"{context}: Token '{token}' starts with orphaned combining mark.")
        if token.endswith(VIRAMA):
            issues.append(f"{context}: Token '{token}' ends with trailing bare Halant (U+094D).")
    return issues


def verify_transcript(transcript_path: Path) -> list[str]:
    issues: list[str] = []
    if not transcript_path.exists():
        return [f"Transcript not found: {transcript_path}"]
    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    entries = data if isinstance(data, list) else data.get("words", [])
    for idx, item in enumerate(entries):
        word = str(item.get("word", ""))
        issues.extend(check_unicode_text(word, f"transcript[{idx}]"))
    return issues


def verify_scenes(scenes_dir: Path) -> list[str]:
    issues: list[str] = []
    if not scenes_dir.exists():
        return [f"Scenes directory not found: {scenes_dir}"]

    tsx_files = sorted(scenes_dir.glob("*.tsx"))
    for sf in tsx_files:
        code = sf.read_text(encoding="utf-8")
        has_devanagari = bool(DEVANAGARI_RE.search(code))
        issues.extend(check_unicode_text(code, sf.name))

        if CHAR_SPLIT_RE.search(code):
            issues.append(
                f"{sf.name}: Forbidden .split('') detected; use Intl.Segmenter('mr', {{ granularity: 'grapheme' }})."
            )

        if has_devanagari:
            for m in LINE_HEIGHT_RE.finditer(code):
                lh = float(m.group(1))
                if lh < 1.42:
                    issues.append(
                        f"{sf.name}: lineHeight {lh} < 1.42 risks clipping Devanagari Matras/Ukars."
                    )
            if ITALIC_RE.search(code) and "unicode-range" not in code:
                # Flag italic usage inside files containing Devanagari unless explicitly scoped to Latin.
                issues.append(
                    f"{sf.name}: fontStyle: 'italic' found alongside Devanagari text; keep italic strictly on Latin font_special."
                )
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify Marathi Devanagari transcripts and Remotion scenes."
    )
    parser.add_argument("--transcript", default="", help="Path to build/transcript_ms.json")
    parser.add_argument("--scenes-dir", default="", help="Path to src/scenes")
    parser.add_argument(
        "--check-card",
        default="",
        help="Optional single subtitle card string to validate word/grapheme limits.",
    )
    args = parser.parse_args()

    errors: list[str] = []
    if args.check_card:
        errors.extend(check_unicode_text(args.check_card, "card"))
        words = args.check_card.split()
        aksharas = count_aksharas(args.check_card)
        if len(words) > 5:
            errors.append(f"Card has {len(words)} words (max 5 for Marathi).")
        if aksharas > 28:
            errors.append(f"Card has {aksharas} grapheme clusters (max 28).")

    if args.transcript:
        errors.extend(verify_transcript(Path(args.transcript)))
    if args.scenes_dir:
        errors.extend(verify_scenes(Path(args.scenes_dir)))

    report: dict[str, Any] = {"passed": len(errors) == 0, "errors": errors}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
