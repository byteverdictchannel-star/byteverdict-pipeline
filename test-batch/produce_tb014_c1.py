#!/usr/bin/env python3
"""Production script for tb014-c1 — SpaceX Falcon 9 Moon Crash (NASASpaceNews).

Pipeline (updated 2026-08-28):
  1. Trim source (t=3-42, ~39s)
  2. Overlay headline (render_breaking_news, export=False)
  3. Burn rolling subtitles (burn_subtitles.py)
  4. Finalize (loudnorm + progress bar + bug + closing question + exports)

Source: NASASpaceNews — "NASA Just Released Images of the SpaceX Moon Crash"
Audio: English (ffmpeg metadata: eng, Opus, stereo, 150kb/s; English VTT captions verified)
"""
import sys, os, shutil
from pathlib import Path

BASE = Path("/home/leo/clips-channel")
PIPELINE = BASE / "pipeline"
EXPORTS = BASE / "test-batch/exports"
READY = BASE / "test-batch/ready-to-post"
PLATFORMS = BASE / "test-batch/exports/platform-exports"

sys.path.insert(0, str(PIPELINE))
from breaking_news_overlay import render_breaking_news
from finalize_clip import finalize
from burn_subtitles import burn

SRC = BASE / "test-batch/captures/tb014_c1_CsxVS-NFupA.mp4"
VTT_FILE = BASE / "test-batch/captures/tb014_c1_CsxVS-NFupA.en.vtt"

IN_POINT = 3.0
OUT_POINT = 42.0

CLIP_ID = "tb014_c1"
OVERLAY_HEADLINE = ["SpaceX's Falcon 9 slammed into the Moon", "NASA found a 60-foot crater"]
OVERLAY_SOURCE = "NASASpaceNews"
OVERLAY_DATE = "August 27, 2026"

# Closing question — science/policy story with a genuine opinion angle
CLOSING_QUESTION = "Are we thinking about what we leave behind on the Moon?"
CLOSING_QUESTION_START = 32.0  # appears in final ~7s of 39s clip

TICKER = ""

def main():
    import subprocess

    # Step 1: Trim source segment
    cut_raw = EXPORTS / f"{CLIP_ID}_cut_raw.mp4"
    cmd = [
        "/home/leo/.local/bin/ffmpeg", "-y",
        "-ss", str(IN_POINT), "-to", str(OUT_POINT),
        "-i", str(SRC),
        "-c", "copy",
        str(cut_raw),
    ]
    print(f"Step 1: Trimming source (t={IN_POINT}-{OUT_POINT}, ~{OUT_POINT-IN_POINT}s)")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"FATAL: trim failed:\n{proc.stderr[-2000:]}")
        return 1
    print(f"  Trimmed: {cut_raw.name} ({cut_raw.stat().st_size / 1_048_576:.1f} MB)")

    # Step 2: Render headline overlay (export=False)
    print(f"\nStep 2: Rendering headline overlay (export=False)")
    render_breaking_news(
        clip_id=CLIP_ID,
        src_path=cut_raw,
        headline_lines=OVERLAY_HEADLINE,
        context_line=OVERLAY_DATE,
        source=OVERLAY_SOURCE,
        out_dir=EXPORTS,
        export=False,
    )
    overlaid = EXPORTS / f"{CLIP_ID}_master.mp4"
    if not overlaid.exists():
        print("FATAL: overlay master not produced")
        return 1
    print(f"  Overlay master: {overlaid.name} ({overlaid.stat().st_size / 1_048_576:.1f} MB)")

    # Step 3: Burn rolling subtitles
    print(f"\nStep 3: Burning rolling subtitles from {VTT_FILE.name}...")
    subtitled = EXPORTS / f"{CLIP_ID}_subtitled.mp4"
    burn(
        video_path=str(overlaid),
        vtt_file=str(VTT_FILE),
        in_point=IN_POINT,
        out_point=OUT_POINT,
        output_path=str(subtitled),
    )
    if not subtitled.exists():
        print("FATAL: subtitle burn failed")
        return 1
    print(f"  Subtitled master: {subtitled.name} ({subtitled.stat().st_size / 1_048_576:.1f} MB)")

    # Step 4: Finalize — loudnorm + progress bar + bug + closing question + exports
    print(f"\nStep 4: Finalizing (loudnorm + progress bar + bug + closing question + exports)")
    outputs = finalize(
        video_path=str(subtitled),
        clip_id=CLIP_ID,
        out_dir=str(EXPORTS),
        ticker=TICKER,
        closing_question=CLOSING_QUESTION,
        closing_question_start=CLOSING_QUESTION_START,
    )

    # Step 6: Copy MASTER to ready-to-post
    ready_master = READY / f"{CLIP_ID}_master.mp4"
    shutil.copy2(outputs["master"], ready_master)
    print(f"\n  Master copied to ready-to-post: {ready_master.name}")

    # Step 7: Copy platform exports to platform-exports/
    for plat, out_path in outputs.items():
        if plat != "master":
            plat_export = PLATFORMS / Path(out_path).name
            shutil.copy2(out_path, plat_export)
            print(f"  {plat} export copied: {plat_export.name}")

    print(f"\n{'='*60}")
    print(f"  PRODUCTION COMPLETE: {CLIP_ID}")
    print(f"{'='*60}")
    print(f"  Master:    {ready_master.name} ({ready_master.stat().st_size/1_048_576:.1f} MB)")
    for plat, path in outputs.items():
        if plat != "master":
            print(f"  {plat:10s}: {path.name} ({path.stat().st_size/1_048_576:.1f} MB)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
