#!/usr/bin/env python3
"""Final production pass: EBU R128 loudness normalization + broadcast-motion
graphics (ticker + bug, no duplicate banner), applied once to the already
subtitled/overlaid clip, followed by platform-native exports.

Added 2026-08-28 in response to two confirmed gaps in the pipeline: (1) no
audio loudness normalization existed anywhere — clips from different source
outlets play back at wildly inconsistent volume; (2) broadcast_graphics.py's
motion ticker (built specifically to fix "video reading as static") was
built and tested but never wired into the standard per-clip workflow.

Intended position in content-agent-prompt.md §5's step order:
  1-4. capture, cut, headline overlay (breaking_news_overlay.render_breaking_news
       with export=False), composite -> produces an un-exported master
  5. burn_subtitles.py burn() on that master -> subtitled master
  6. THIS SCRIPT on the subtitled master -> normalized + ticker'd master,
     then platform exports
  7+. logo blur, copy to ready-to-post, clip-log entry (unchanged)

Why loudnorm runs once here rather than per-platform: normalizing the
master once and re-encoding platform exports from that normalized master
is one loudnorm pass instead of three: identical result, a third of the
audio-filter cost.

Why the ticker has no banner: breaking_news_overlay.py's Tier A overlay
already renders a headline near the top of frame — broadcast_graphics.py's
own banner would duplicate that text near the bottom. Only the ticker
(motion) and small BV bug are applied here — see apply_broadcast_motion()
in broadcast_graphics.py for the exact positioning logic.

Usage:
  python3 finalize_clip.py --video <subtitled_master.mp4> \\
      --ticker "OTHER HEADLINE ONE  •  OTHER HEADLINE TWO" \\
      --clip-id tb0XX_slug --out-dir test-batch/exports
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from broadcast_graphics import apply_broadcast_motion, apply_progress_bar, build_bug, build_question_strip, FRAME_W, FRAME_H
from breaking_news_overlay import export_platforms


def _apply_pb_graphics(video_path, output_path, closing_question=None,
                       closing_question_start=None):
    """New 2026-08-28 standard pipeline: progress bar + BV bug + closing question.

    Replaces apply_broadcast_motion (ticker + bug) in the standard production
    pipeline per broadcast_graphics.py docstring: source footage already shows
    the real outlet's watermark; stacking BV's own news-style ticker risked
    reading as broadcast impersonation, which WEAKENS (not strengthens) the
    transformative-use posture (docs/legal-report/02-analysis/07-risk-mitigation-patterns.md
    §7-8). A plain progress bar carries none of that risk.

    Single ffmpeg pass: progress bar (drawbox width grows over duration) +
    bug overlay (top-left) + optional closing question strip (bottom, enabled
    at closing_question_start). Video re-encoded, audio copied.
    """
    # Probe duration for the progress-bar width expression
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True,
    )
    try:
        duration = float(probe.stdout.strip())
    except ValueError:
        raise RuntimeError(f"could not probe duration: {probe.stderr[-500:]}")

    with tempfile.TemporaryDirectory() as tmp:
        bug_path = f"{tmp}/bug.png"
        build_bug(bug_path)

        inputs = [str(video_path), "-loop", "1", "-i", bug_path]
        # drawbox progress bar at extreme bottom edge
        pb_y = FRAME_H - 6
        width_expr = f"min(iw,iw*t/{duration:.3f})"
        filter_parts = [f"drawbox=x=0:y={pb_y}:w='{width_expr}':h=6:color=0xFFD700@0.85:t=fill[bg];[0:v][1:v]overlay=20:40[base]"]
        input_idx = 2

        if closing_question and closing_question_start is not None:
            q_path = f"{tmp}/question.png"
            build_question_strip(q_path, closing_question)
            inputs += ["-loop", "1", "-i", q_path]
            q_y = FRAME_H - 6 - 150  # above progress bar, below subtitle zone
            filter_parts.append(
                f"[base][{input_idx}:v]overlay=0:{q_y}:enable='gte(t,{closing_question_start})'[final]"
            )
            video_label = "[final]"
        else:
            video_label = "[base]"

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", ";".join(filter_parts),
            "-map", video_label, "-map", "0:a?",
            "-c:v", "libx264", "-crf", "22", "-preset", "fast",
            "-c:a", "copy",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"pb graphics failed: {result.stderr[-2000:]}")

FFMPEG = "ffmpeg"

# Target -14 LUFS integrated loudness — the common mobile/short-form-video
# target (louder than broadcast TV's -23/-24 LUFS, matches what YouTube/
# TikTok/Instagram players typically normalize toward on playback anyway).
LOUDNORM_TARGET_I = -14.0
LOUDNORM_TARGET_TP = -1.5
LOUDNORM_TARGET_LRA = 11.0


def measure_loudness(video_path):
    """First pass: measure the input's actual loudness stats via loudnorm's
    own analysis mode (print_format=json), so the second pass can apply
    precise linear correction instead of loudnorm's default dynamic (less
    accurate) single-pass behavior."""
    cmd = [
        FFMPEG, "-i", str(video_path),
        "-af", (
            f"loudnorm=I={LOUDNORM_TARGET_I}:TP={LOUDNORM_TARGET_TP}:"
            f"LRA={LOUDNORM_TARGET_LRA}:print_format=json"
        ),
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # loudnorm prints its JSON block to stderr, after ffmpeg's own logging.
    stderr = result.stderr
    start = stderr.rfind("{")
    end = stderr.rfind("}")
    if start == -1 or end == -1:
        raise RuntimeError(f"loudnorm measurement failed to produce stats:\n{stderr[-1500:]}")
    return json.loads(stderr[start:end + 1])


def normalize_audio(video_path, output_path):
    """Two-pass EBU R128 loudness normalization, video stream copied through
    unchanged (only the audio filter chain runs, video is a straight copy —
    this is purely an audio-loudness fix, not a re-render)."""
    stats = measure_loudness(video_path)
    filt = (
        f"loudnorm=I={LOUDNORM_TARGET_I}:TP={LOUDNORM_TARGET_TP}:"
        f"LRA={LOUDNORM_TARGET_LRA}:"
        f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
        f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:linear=true:print_format=summary"
    )
    cmd = [
        FFMPEG, "-y", "-i", str(video_path),
        "-c:v", "copy",
        "-af", filt,
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"loudnorm apply pass failed: {result.stderr[-2000:]}")
    return stats


def finalize(video_path, clip_id, out_dir, ticker=None, ticker_speed_px_per_s=180.0,
             closing_question=None, closing_question_start=None,
             use_progress_bar=True):
    """Final production pass: loudnorm + broadcast graphics → platform exports.

    use_progress_bar=True (default, 2026-08-28 standard): applies a thin gold
    progress bar + BV bug + optional closing question. See _apply_pb_graphics().
    use_progress_bar=False: legacy apply_broadcast_motion (ticker + bug) for
    backward compatibility with existing produce_tb*.py scripts.
    """
    out_dir = Path(out_dir)
    with tempfile.TemporaryDirectory() as tmp:
        normalized_path = f"{tmp}/{clip_id}_normalized.mp4"
        print(f"\n{'='*60}\n  Normalizing audio loudness ({clip_id})\n{'='*60}")
        stats = normalize_audio(video_path, normalized_path)
        print(f"  Input: {stats['input_i']} LUFS -> Target: {LOUDNORM_TARGET_I} LUFS")

        final_master = out_dir / f"{clip_id}_master.mp4"
        print(f"\n{'='*60}\n  Applying broadcast graphics ({clip_id})\n{'='*60}")
        if use_progress_bar:
            _apply_pb_graphics(
                normalized_path, final_master,
                closing_question=closing_question,
                closing_question_start=closing_question_start,
            )
        else:
            apply_broadcast_motion(
                normalized_path, final_master,
                ticker=ticker,
                ticker_speed_px_per_s=ticker_speed_px_per_s,
                closing_question=closing_question,
                closing_question_start=closing_question_start,
                include_banner=False,
            )

    print(f"\n✅ Finalized master: {final_master.stat().st_size / 1_048_576:.1f} MB")
    outputs = {"master": final_master}
    outputs.update(export_platforms(final_master, clip_id, out_dir))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, help="Overlaid master to finalize (no subtitles — policy 2026-08-28)")
    parser.add_argument("--clip-id", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--ticker", default="", help="Legacy ticker text (only used with --legacy-ticker)")
    parser.add_argument("--ticker-speed-px-per-s", type=float, default=180.0)
    parser.add_argument("--closing-question", default=None)
    parser.add_argument("--closing-question-start", type=float, default=None)
    parser.add_argument("--legacy-ticker", action="store_true",
                        help="Use old ticker+bug pipeline instead of progress bar")
    args = parser.parse_args()

    if args.closing_question and args.closing_question_start is None:
        parser.error("--closing-question requires --closing-question-start")

    try:
        finalize(
            args.video, args.clip_id, args.out_dir,
            ticker=args.ticker,
            ticker_speed_px_per_s=args.ticker_speed_px_per_s,
            closing_question=args.closing_question,
            closing_question_start=args.closing_question_start,
            use_progress_bar=not args.legacy_ticker,
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
