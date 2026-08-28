#!/usr/bin/env python3
"""Production script for tb012-c2 — Lunar Eclipse (NASA JPL).

Pipeline (updated 2026-08-28):
  1. Trim source (t=107-145, ~38s)
  2. Overlay headline (render_breaking_news, export=False)
  3. Burn rolling subtitles (burn_subtitles.py)
  4. Finalize (loudnorm + progress bar + bug, no closing question — observational story)

Source: NASA JPL "What's Up: August 2026 Skywatching Tips"
Audio: English confirmed via Alienware Whisper transcript
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

SRC = BASE / "test-batch/captures/src_tb012_c2_nasa_jpl_I29P2zHNGdI.mp4"

IN_POINT = 107.0
OUT_POINT = 145.0

CLIP_ID = "tb012_c2"
# Avoid % in drawtext (this ffmpeg build doesn't support %% escape — regression)
# 93% figure goes in caption instead
OVERLAY_HEADLINE = ["The moon turns red tonight", "Blood moon across the Americas"]
OVERLAY_SOURCE = "NASA / JPL"
OVERLAY_DATE = "August 28, 2026"

# No closing question — observational/astronomical story, no opinion angle
# Ticker is empty — progress bar pipeline doesn't use it

TICKER = ""

# Source video ID for subtitle fetch (no local VTT available)
SOURCE_VIDEO_ID = "I29P2zHNGdI"

def main():
    import subprocess

    # Step 1: Trim source segment (stream copy for speed)
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

    # Step 2: Render headline overlay (export=False — platform exports happen at finalize step)
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

    # Step 3: Burn rolling subtitles (API fallback — no local VTT)
    print(f"\nStep 3: Burning rolling subtitles from YouTube API ({SOURCE_VIDEO_ID})...")
    subtitled = EXPORTS / f"{CLIP_ID}_subtitled.mp4"
    burn(
        video_path=str(overlaid),
        source_video_id=SOURCE_VIDEO_ID,
        in_point=IN_POINT,
        out_point=OUT_POINT,
        output_path=str(subtitled),
    )
    if not subtitled.exists():
        print("FATAL: subtitle burn failed")
        return 1
    print(f"  Subtitled master: {subtitled.name} ({subtitled.stat().st_size / 1_048_576:.1f} MB)")

    # Step 4: Finalize — loudnorm + progress bar + bug + platform exports
    print(f"\nStep 4: Finalizing (loudnorm + progress bar + bug + exports)")
    outputs = finalize(
        video_path=str(subtitled),
        clip_id=CLIP_ID,
        out_dir=str(EXPORTS),
        ticker=TICKER,
        closing_question=None,
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
