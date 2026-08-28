#!/usr/bin/env python3
"""Motion/graphics package for clip videos.

**Standard pipeline default (changed 2026-08-28, per Leo):** a thin,
neutral progress bar (apply_progress_bar()) — solves the original motion
problem (video reading as static on a held shot) without the news-ticker
styling. Reasoning: source footage often already shows the real outlet's
own on-screen watermark; stacking BV's own separate news-style
ticker/banner on top of that risked reading as broadcast impersonation
(a platform-policy concern, separate from copyright) and, per the
channel's own risk docs (docs/legal-report/02-analysis/07-risk-mitigation-patterns.md
§7-8), a clip that looks more like broadcast decoration and less like
independent editorial work actually WEAKENS the transformative-use
posture rather than strengthening it. A plain progress bar carries none
of that risk while still fixing the static-video problem.

**Legacy (apply_broadcast_motion(), kept for reference/direct CLI use
only — no longer called by the standard pipeline):** a persistent
'BREAKING' banner with headline, a continuously scrolling ticker, and a
small network bug/logo. Original ByteVerdict branding — deliberately NOT
copying any real network's actual logo/wordmark/color trademark, only the
general layout convention (banner + ticker + bug) common across TV news
broadcasts — the trademark risk itself was assessed as low, but the
broadcast-impersonation-read risk led to the 2026-08-28 change above.

Usage:
  python3 broadcast_graphics.py --video <in.mp4> --headline "..." \\
      --ticker "ITEM ONE  •  ITEM TWO  •  ITEM THREE" --output <out.mp4>
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FRAME_W = 1080
FRAME_H = 1920

BRAND_RED = (196, 30, 40, 255)
BRAND_DARK = (17, 17, 20, 235)
WHITE = (255, 255, 255, 255)

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def build_bug(path: str) -> None:
    """Small logo bug, top-left — 'BV' mark + BYTEVERDICT wordmark, minimal."""
    img = Image.new("RGBA", (280, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 60, 60], fill=BRAND_RED)
    f_mark = _font(34)
    f_word = _font(26)
    d.text((10, 10), "BV", font=f_mark, fill=WHITE)
    d.text((70, 16), "BYTEVERDICT", font=f_word, fill=WHITE)
    img.save(path)


def build_banner(path: str, headline: str) -> int:
    """Static 'BREAKING' tag + headline bar. Returns the banner image height."""
    height = 190
    img = Image.new("RGBA", (FRAME_W, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # BREAKING tag
    tag_h = 70
    d.rectangle([0, 0, FRAME_W, tag_h], fill=BRAND_RED)
    f_tag = _font(46)
    d.text((30, 10), "BREAKING", font=f_tag, fill=WHITE)
    # Headline bar
    d.rectangle([0, tag_h, FRAME_W, height], fill=BRAND_DARK)
    f_headline = _font(38)
    # wrap headline to fit width
    words = headline.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if d.textlength(test, font=f_headline) > FRAME_W - 60:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    y = tag_h + 12
    for line in lines[:2]:
        d.text((30, y), line, font=f_headline, fill=WHITE)
        y += 46
    img.save(path)
    return height


def build_ticker_strip(path: str, ticker_text: str) -> int:
    """Wide horizontal strip of repeated ticker text, scrolled via overlay
    x-expression in ffmpeg rather than baked-in motion — one strip, animated
    at composite time. Returns the strip width in pixels."""
    f = _font(34)
    unit = f"   {ticker_text}   •  "
    # repeat enough times to comfortably loop-scroll across a long clip
    repeated = unit * 6
    tmp_img = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp_img)
    text_w = int(d.textlength(repeated, font=f))
    strip_h = 60
    img = Image.new("RGBA", (text_w, strip_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, text_w, strip_h], fill=BRAND_RED)
    d.text((0, 12), repeated, font=f, fill=WHITE)
    img.save(path)
    return text_w


def build_question_strip(path: str, question: str) -> int:
    """Static (non-scrolling) strip replacing the ticker for the closing
    beat — distinct amber color + 'YOUR TAKE:' prefix so it reads as a
    deliberate call-to-action, not just more ticker noise. Wraps to fit
    the frame width instead of clipping. Returns the strip height."""
    f = _font(30)
    text = f"YOUR TAKE:  {question}"
    tmp_img = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp_img)
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if d.textlength(test, font=f) > FRAME_W - 40:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)

    line_h = 40
    height = 20 + line_h * len(lines)
    img = Image.new("RGBA", (FRAME_W, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, FRAME_W, height], fill=(214, 158, 46, 255))  # amber, distinct from the red ticker
    y = 10
    for line in lines:
        d.text((20, y), line, font=f, fill=(20, 20, 20, 255))
        y += line_h
    img.save(path)
    return height


def apply_progress_bar(video_path, output_path, color="0xFFD700", height=6, opacity=0.85):
    """Thin growing progress bar across the very bottom edge of the frame —
    the standard pipeline's motion element as of 2026-08-28 (see module
    docstring for why this replaced the news-ticker style).

    Pure ffmpeg drawbox, no PNG generation needed — width grows linearly
    from 0 to full frame width over the clip's actual duration (probed
    first), positioned at the extreme bottom edge (y = FRAME_H - height),
    thin enough to sit comfortably below any overlay/subtitle text without
    needing to track their exact positions the way the old ticker did.
    """
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True,
    )
    try:
        duration = float(probe.stdout.strip())
    except ValueError:
        raise RuntimeError(f"could not probe duration of {video_path}: {probe.stderr[-500:]}")

    y = FRAME_H - height
    # width expression: full frame width * (elapsed time / total duration),
    # clamped so it never exceeds the frame even on the last frame's
    # slightly-over-duration timestamp.
    width_expr = f"min(iw,iw*t/{duration:.3f})"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"drawbox=x=0:y={y}:w='{width_expr}':h={height}:color={color}@{opacity}:t=fill",
        "-c:v", "libx264", "-crf", "22", "-preset", "fast",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-2000:]}")
    print(f"Done: {output_path}")


def apply_broadcast_motion(
    video_path,
    output_path,
    headline=None,
    ticker=None,
    ticker_speed_px_per_s=180.0,
    closing_question=None,
    closing_question_start=None,
    include_banner=True,
):
    """Composite the bug + (optional) banner + scrolling ticker onto a video.

    include_banner=False (added 2026-08-28, for use from the standard
    production pipeline via finalize_clip.py) skips the 'BREAKING' + headline
    bar — breaking_news_overlay.py's Tier A overlay already draws a headline
    near the top of frame, and this banner sits near the bottom, so running
    both duplicates the headline text on screen. With include_banner=False,
    headline may be omitted; only the bug + ticker (the actual motion fix)
    are applied. Set True (default) to preserve the original standalone
    banner+ticker+bug package behavior for direct CLI use.
    """
    if include_banner and not headline:
        raise ValueError("headline is required when include_banner=True")
    if closing_question and closing_question_start is None:
        raise ValueError("closing_question requires closing_question_start")

    with tempfile.TemporaryDirectory() as tmp:
        bug_path = f"{tmp}/bug.png"
        ticker_path = f"{tmp}/ticker.png"

        build_bug(bug_path)
        ticker_w = build_ticker_strip(ticker_path, ticker)
        speed = ticker_speed_px_per_s

        inputs = ["-i", str(video_path), "-loop", "1", "-i", bug_path]
        filter_complex = "[0:v][1:v]overlay=20:40[v1];"
        next_label = "v1"
        next_input_idx = 2

        if include_banner:
            banner_path = f"{tmp}/banner.png"
            banner_h = build_banner(banner_path, headline)
            banner_y = FRAME_H - banner_h - 260  # sits above the bottom safe zone
            ticker_y = banner_y + banner_h
            inputs += ["-loop", "1", "-i", banner_path]
            filter_complex += f"[{next_label}][{next_input_idx}:v]overlay=0:{banner_y}[v2];"
            next_label = "v2"
            next_input_idx += 1
        else:
            # No banner — breaking_news_overlay.py's Tier A overlay already
            # draws a context line at y=1640 and a source-attribution line
            # at y=1690 (height ~30px, ending ~y=1720). A first version of
            # this placed the ticker at FRAME_H-260=1660, which sat directly
            # on top of that source line and hid it completely — confirmed
            # by a real test render (frame crop showed the source line
            # missing entirely under the ticker). Parking the ticker just
            # below that line instead, at y=1730, clears it with a small
            # margin while staying well below the rolling-subtitle band
            # (ends ~y=1594, see MARGIN_V in burn_subtitles.py) even at 2
            # wrapped subtitle lines.
            ticker_y = 1730

        inputs += ["-loop", "1", "-i", ticker_path]
        filter_complex += (
            f"[{next_label}][{next_input_idx}:v]overlay="
            f"x='{FRAME_W}-mod(t*{speed}\\,{ticker_w}+{FRAME_W})':y={ticker_y}[v3]"
        )
        next_input_idx += 1
        last_label = "v3"

        if closing_question:
            question_path = f"{tmp}/question.png"
            build_question_strip(question_path, closing_question)
            inputs += ["-loop", "1", "-i", question_path]
            filter_complex += f";[v3][{next_input_idx}:v]overlay=0:{ticker_y}:enable='gte(t,{closing_question_start})'[v4]"
            last_label = "v4"

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", f"[{last_label}]", "-map", "0:a?",
            "-c:v", "libx264", "-crf", "22", "-preset", "fast",
            "-c:a", "copy",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr[-2000:]}")

    print(f"Done: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True)
    parser.add_argument("--headline", default=None, help="Required unless --no-banner")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--no-banner", action="store_true",
                        help="Skip the BREAKING+headline banner (use when a headline overlay is already applied elsewhere, e.g. via breaking_news_overlay.py) — keeps the bug + ticker only.")
    parser.add_argument("--ticker-speed-px-per-s", type=float, default=180.0)
    parser.add_argument("--closing-question", default=None,
                        help="If given, replaces the ticker with this static question for the final --closing-question-start seconds onward. Only use for stories that genuinely support an opinion/prediction question — skip entirely for tragedies/disasters where 'what's your take' would be tone-deaf.")
    parser.add_argument("--closing-question-start", type=float, default=None,
                        help="Video time (seconds) the closing question replaces the ticker. Required if --closing-question is given.")
    args = parser.parse_args()

    try:
        apply_broadcast_motion(
            args.video, args.output,
            headline=args.headline, ticker=args.ticker,
            ticker_speed_px_per_s=args.ticker_speed_px_per_s,
            closing_question=args.closing_question,
            closing_question_start=args.closing_question_start,
            include_banner=not args.no_banner,
        )
    except (ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
