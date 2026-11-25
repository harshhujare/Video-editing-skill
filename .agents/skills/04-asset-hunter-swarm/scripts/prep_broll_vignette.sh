#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <input.mp4> <output.mp4> [paper_texture.png]" >&2
  exit 1
fi

INPUT_VIDEO="$1"
OUTPUT_VIDEO="$2"
TEXTURE_PNG="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "$TEXTURE_PNG" ]]; then
  python "$SCRIPT_DIR/prep_broll_vignette.py" --input "$INPUT_VIDEO" --output "$OUTPUT_VIDEO" --texture "$TEXTURE_PNG"
else
  python "$SCRIPT_DIR/prep_broll_vignette.py" --input "$INPUT_VIDEO" --output "$OUTPUT_VIDEO"
fi
