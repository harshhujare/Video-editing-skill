#!/usr/bin/env python3
"""
Modular Multi-Project Workspace Manager for the Video Editing Pipeline.

Allows the workspace to edit or generate any number of videos across all 5 modes:
  1. talking-head       (Mode A: Raw camera clip + Nano Banana illustrations + Remotion dataviz)
  2. faceless-explainer (Mode B: ElevenLabs voiceover + display-script.txt + 50/30/20 motion beats)
  3. editorial-hybrid   (Mode C: Talking-head or VO + Nano Banana Economist/Monocle illustrations)
  4. generative-broll   (Mode D: Omni-Video / Pexels 9:16 B-roll + rotoscoped back-text)
  5. lemo-opuscar-film  (Mode E: 100% code-driven Canvas/WebGL short film in 99 Lemo-Opuscar styles)

Each project is isolated under `projects/<slug>/` and can be loaded into the active
Remotion workspace (`src/`, `public/assets/`, `build/`, `artifacts/`) or saved back
with a single command so no video ever overwrites another.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = ROOT / "projects"
ACTIVE_FILE = ROOT / ".active_project"
FINAL_DIR = ROOT / "Final-edited-video"

VALID_MODES = [
    "talking-head",
    "faceless-explainer",
    "editorial-hybrid",
    "generative-broll",
    "lemo-opuscar-film",
]


def get_active_slug() -> str | None:
    if ACTIVE_FILE.exists():
        slug = ACTIVE_FILE.read_text(encoding="utf-8").strip()
        return slug or None
    return None


def set_active_slug(slug: str) -> None:
    ACTIVE_FILE.write_text(slug + "\n", encoding="utf-8")


def copy_tree_contents(src_dir: Path, dst_dir: Path, pattern: str = "*") -> int:
    if not src_dir.exists():
        return 0
    dst_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in src_dir.glob(pattern):
        target = dst_dir / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
            count += 1
        elif item.is_file():
            shutil.copy2(item, target)
            count += 1
    return count


def clear_dir_files(target_dir: Path, pattern: str = "*") -> None:
    if not target_dir.exists():
        return
    for item in target_dir.glob(pattern):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def ensure_project_dirs(pdir: Path) -> None:
    for sub in [
        "input",
        "artifacts",
        "build",
        "assets/aroll",
        "assets/audio",
        "assets/generated",
        "assets/broll",
        "src/scenes",
        "output",
    ]:
        (pdir / sub).mkdir(parents=True, exist_ok=True)


def save_active_to_project(slug: str, mode: str | None = None, lang: str | None = None, fps: int | None = None) -> Path:
    pdir = PROJECTS_DIR / slug
    ensure_project_dirs(pdir)

    meta_path = pdir / "project.json"
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    meta["slug"] = slug
    meta["mode"] = mode or meta.get("mode", "editorial-hybrid")
    meta["language"] = lang or meta.get("language", "mr")
    meta["fps"] = fps or meta.get("fps", 30)
    meta["aspect_ratio"] = meta.get("aspect_ratio", "9:16")
    meta["updated_at"] = datetime.now().isoformat(timespec="seconds")

    # 1. Save active Remotion scenes & Root/AudioTimeline
    clear_dir_files(pdir / "src" / "scenes", "Scene*.tsx")
    scene_count = copy_tree_contents(ROOT / "src" / "scenes", pdir / "src" / "scenes", "Scene*.tsx")
    for fname in ["Root.tsx", "AudioTimeline.tsx"]:
        fsrc = ROOT / "src" / fname
        if fsrc.exists():
            shutil.copy2(fsrc, pdir / "src" / fname)

    # 2. Save active artifacts/edit_plan.md
    if (ROOT / "artifacts" / "edit_plan.md").exists():
        shutil.copy2(ROOT / "artifacts" / "edit_plan.md", pdir / "artifacts" / "edit_plan.md")

    # 3. Save key build JSONs & trimmed A-roll / voice_master
    for bfile in [
        "transcript_ms.json",
        "transcript_ms_draft.json",
        "explainer_timeline.json",
        "asset_manifest.json",
        "aroll_trimmed.mp4",
        "voice_master.wav",
        "v3_editorial_qa_grid.jpg",
        "v2_swp_qa_grid.jpg",
    ]:
        bsrc = ROOT / "build" / bfile
        if bsrc.exists():
            shutil.copy2(bsrc, pdir / "build" / bfile)

    # 4. Save project-scoped public assets (aroll, audio, generated, broll)
    for asset_sub in ["aroll", "audio", "generated", "broll"]:
        copy_tree_contents(ROOT / "public" / "assets" / asset_sub, pdir / "assets" / asset_sub)

    # 5. Save input glossary if present
    if (ROOT / "input" / "glossary-mr.json").exists():
        shutil.copy2(ROOT / "input" / "glossary-mr.json", pdir / "input" / "glossary-mr.json")

    meta["scene_count"] = scene_count
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    set_active_slug(slug)
    print(f"[SAVED] Active workspace -> projects/{slug}/ ({scene_count} scenes)")
    return pdir


def load_project_into_workspace(slug: str, save_current: bool = True) -> None:
    pdir = PROJECTS_DIR / slug
    if not pdir.exists():
        raise FileNotFoundError(f"Project not found: {pdir}")

    current = get_active_slug()
    if save_current and current and current != slug and (PROJECTS_DIR / current).exists():
        save_active_to_project(current)

    # 1. Load src/scenes, Root.tsx, AudioTimeline.tsx
    clear_dir_files(ROOT / "src" / "scenes", "Scene*.tsx")
    scene_count = copy_tree_contents(pdir / "src" / "scenes", ROOT / "src" / "scenes", "Scene*.tsx")
    for fname in ["Root.tsx", "AudioTimeline.tsx"]:
        fsrc = pdir / "src" / fname
        if fsrc.exists():
            shutil.copy2(fsrc, ROOT / "src" / fname)

    # 2. Load artifacts/edit_plan.md
    if (pdir / "artifacts" / "edit_plan.md").exists():
        (ROOT / "artifacts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdir / "artifacts" / "edit_plan.md", ROOT / "artifacts" / "edit_plan.md")

    # 3. Load build files
    (ROOT / "build").mkdir(parents=True, exist_ok=True)
    copy_tree_contents(pdir / "build", ROOT / "build")

    # 4. Load project-scoped public/assets/{aroll,audio,generated,broll}
    for asset_sub in ["aroll", "audio", "generated", "broll"]:
        target_dir = ROOT / "public" / "assets" / asset_sub
        clear_dir_files(target_dir)
        copy_tree_contents(pdir / "assets" / asset_sub, target_dir)

    # 5. Load input files
    if (pdir / "input" / "glossary-mr.json").exists():
        (ROOT / "input").mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdir / "input" / "glossary-mr.json", ROOT / "input" / "glossary-mr.json")

    set_active_slug(slug)
    print(f"[LOADED] projects/{slug}/ -> active workspace ({scene_count} scenes ready)")


def init_new_project(
    slug: str,
    mode: str,
    lang: str,
    fps: int,
    source: str | None = None,
    script: str | None = None,
    clean_workspace: bool = False,
) -> Path:
    current = get_active_slug()
    if current and current != slug and (PROJECTS_DIR / current).exists():
        save_active_to_project(current)

    pdir = PROJECTS_DIR / slug
    ensure_project_dirs(pdir)

    # Copy domain glossary template for Marathi projects
    glossary_tpl = ROOT / ".agents" / "skills" / "08-marathi-devanagari-engine" / "references" / "glossary-mr.template.json"
    if lang == "mr" and glossary_tpl.exists() and not (pdir / "input" / "glossary-mr.json").exists():
        shutil.copy2(glossary_tpl, pdir / "input" / "glossary-mr.json")

    if source:
        src_path = Path(source).resolve()
        if not src_path.exists():
            raise FileNotFoundError(f"Source media not found: {src_path}")
        if mode in ("talking-head", "editorial-hybrid", "generative-broll") and src_path.suffix.lower() in (".mp4", ".mov", ".mkv"):
            dst_media = pdir / "input" / "raw_clip.mp4"
        else:
            dst_media = pdir / "input" / f"voiceover{src_path.suffix.lower()}"
        shutil.copy2(src_path, dst_media)
        print(f"  Copied source media -> {dst_media.relative_to(ROOT)}")

    if script:
        scr_path = Path(script).resolve()
        if not scr_path.exists():
            raise FileNotFoundError(f"Script file not found: {scr_path}")
        dst_scr = pdir / "input" / "display-script.txt"
        shutil.copy2(scr_path, dst_scr)
        print(f"  Copied display script -> {dst_scr.relative_to(ROOT)}")

    meta = {
        "slug": slug,
        "mode": mode,
        "language": lang,
        "fps": fps,
        "aspect_ratio": "9:16",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "scene_count": 0,
        "final_output": f"Final-edited-video/{slug}_final.mp4",
    }
    (pdir / "project.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    if clean_workspace:
        clear_dir_files(ROOT / "src" / "scenes", "Scene*.tsx")
        for sub in ["aroll", "audio", "generated", "broll"]:
            clear_dir_files(ROOT / "public" / "assets" / sub)
        set_active_slug(slug)
        print(f"[INIT] Created and activated clean workspace for projects/{slug}/ (mode={mode}, lang={lang}, fps={fps})")
    else:
        print(f"[INIT] Created projects/{slug}/ (mode={mode}, lang={lang}, fps={fps})")
    return pdir


def list_projects() -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    active = get_active_slug()
    pdirs = sorted([d for d in PROJECTS_DIR.iterdir() if d.is_dir()])
    if not pdirs:
        print("No projects found in projects/.")
        return

    print(f"{'ACTIVE':<8} {'PROJECT SLUG':<28} {'MODE':<20} {'LANG':<6} {'FPS':<5} {'SCENES':<8} {'FINAL VIDEO'}")
    print("-" * 105)
    for d in pdirs:
        meta_file = d / "project.json"
        meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}
        slug = d.name
        is_act = "  *   " if slug == active else "      "
        mode = meta.get("mode", "unknown")
        lang = meta.get("language", "mr")
        fps = str(meta.get("fps", 30))
        scenes = len(list((d / "src" / "scenes").glob("Scene*.tsx"))) if (d / "src" / "scenes").exists() else 0
        final_out = meta.get("final_output", f"Final-edited-video/{slug}_final.mp4")
        print(f"{is_act:<8} {slug:<28} {mode:<20} {lang:<6} {fps:<5} {scenes:<8} {final_out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Modular Multi-Project Manager for Video Editing Workspace")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List all video projects and active status")

    p_init = sub.add_parser("init", help="Initialize a new isolated video project under projects/<slug>/")
    p_init.add_argument("slug", help="Project slug (e.g. sip-vs-fd-reel, father-three-sons)")
    p_init.add_argument("--mode", choices=VALID_MODES, default="editorial-hybrid")
    p_init.add_argument("--lang", default="mr", help="Language code: mr, hi, en")
    p_init.add_argument("--fps", type=int, default=30, choices=[24, 30, 60])
    p_init.add_argument("--source", default=None, help="Optional path to raw video clip or voiceover audio")
    p_init.add_argument("--script", default=None, help="Optional path to display-script.txt")
    p_init.add_argument("--activate", action="store_true", help="Save current project and clear workspace for this new project")

    p_save = sub.add_parser("save", help="Save current active workspace files into projects/<slug>/")
    p_save.add_argument("slug", nargs="?", default=None, help="Project slug (defaults to current .active_project)")
    p_save.add_argument("--mode", choices=VALID_MODES, default=None)
    p_save.add_argument("--lang", default=None)
    p_save.add_argument("--fps", type=int, default=None)

    p_load = sub.add_parser("load", help="Load projects/<slug>/ into the active Remotion workspace")
    p_load.add_argument("slug", help="Project slug to activate")
    p_load.add_argument("--no-save-current", action="store_true", help="Do not auto-save current project before loading")

    args = parser.parse_args()
    if args.cmd == "list":
        list_projects()
    elif args.cmd == "init":
        init_new_project(args.slug, args.mode, args.lang, args.fps, args.source, args.script, args.activate)
    elif args.cmd == "save":
        slug = args.slug or get_active_slug()
        if not slug:
            print("Error: No slug provided and no .active_project set.", file=sys.stderr)
            sys.exit(1)
        save_active_to_project(slug, args.mode, args.lang, args.fps)
    elif args.cmd == "load":
        load_project_into_workspace(args.slug, save_current=not args.no_save_current)


if __name__ == "__main__":
    main()
