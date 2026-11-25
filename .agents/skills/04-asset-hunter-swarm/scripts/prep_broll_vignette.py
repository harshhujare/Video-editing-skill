#!/usr/bin/env python3
"""
Pre-process Pexels stock B-roll into the Arthur Brooks textured vignette look:
- Crop/scale to 1080x1920 @ 60fps
- Desaturate 25% and boost contrast 10%
- Apply outer-20% radial Gaussian blur and dark vignette
- Blend a 15% opacity fine paper grain overlay (image or procedural grain)
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def build_filtergraph(has_texture: bool) -> str:
    base = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,fps=60,setsar=1,"
        "eq=saturation=0.75:contrast=1.10,format=gbrp[graded];"
        "[graded]split=2[sharp][toblur];"
        "[toblur]gblur=sigma=18[blurred];"
        # White center (kept sharp) -> black outer 20% perimeter (blurred)
        "color=c=white:s=1080x1920:r=60:d=0.02,format=gray,"
        "geq='if(lt(hypot((X-W/2)/(W*0.42),(Y-H/2)/(H*0.42)),1),255,clip(255*(1-(hypot((X-W/2)/(W*0.42),(Y-H/2)/(H*0.42))-1)/0.25),0,255))'[radialmask];"
        "[blurred][sharp][radialmask]maskedmerge,"
        "vignette=angle=PI/3.2:mode=forward,format=yuv420p[vig]"
    )
    if has_texture:
        return (
            base
            + ";[1:v]scale=1080:1920,format=rgba,colorchannelmixer=aa=0.15[grain];"
            "[vig][grain]overlay=0:0:shortest=1,format=yuv420p[out]"
        )
    return base + ";[vig]noise=alls=6:allf=t+u,format=yuv420p[out]"


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply Arthur Brooks B-roll vignette and paper grain.")
    parser.add_argument("--input", required=True, help="Raw stock video path.")
    parser.add_argument("--output", required=True, help="Processed MP4 output path.")
    parser.add_argument(
        "--texture",
        default="public/assets/textures/paper_light.png",
        help="Optional paper texture PNG for 15%% overlay.",
    )
    args = parser.parse_args()

    in_path = Path(args.input).resolve()
    out_path = Path(args.output).resolve()
    tex_path = Path(args.texture).resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input B-roll not found: {in_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    has_texture = tex_path.exists()

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(in_path)]
    if has_texture:
        cmd.extend(["-loop", "1", "-i", str(tex_path)])

    cmd.extend(
        [
            "-filter_complex",
            build_filtergraph(has_texture),
            "-map",
            "[out]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(out_path),
        ]
    )
    subprocess.run(cmd, check=True)
    print(f"Processed B-roll vignette -> {out_path} (texture={'yes' if has_texture else 'procedural'})")


if __name__ == "__main__":
    main()
