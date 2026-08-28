#!/usr/bin/env python3
"""Reusable "Tier A" breaking-news overlay template (SKILL.md overlay spec).

Headline (yellow, bold) -> optional quote line (white) -> context line (white,
small) -> source attribution (yellow, small). Text-on-video only — no
narration/voiceover is added; original clip audio passes through unchanged
(or with an optional gain adjustment).

Fixes the ffmpeg drawtext escaping bug found in render_tb006.py: literal
commas and colons inside text values must be escaped (\\, and \\:) or ffmpeg's
filtergraph parser breaks. escape_drawtext() handles this once, centrally, so
per-clip scripts don't need to think about it.

Also fixes the text-overflow bug found in tb005-c1 (2026-08-28): every text
line was drawn at a fixed fontsize regardless of length, so "Canada hits
back" ran off both edges of the frame — ffmpeg's drawtext centers on measured
width, so oversized text overflows symmetrically rather than clipping to one
side, which is why it wasn't obvious from a quick look. fit_fontsize() now
measures each line with PIL (measurement only — rendering is still ffmpeg
drawtext, unchanged) and shrinks the font until it fits within the safe
margin before handing a size to ffmpeg. Same principle as libass/ASS
auto-fit subtitle rendering, adapted to this codebase's existing drawtext
approach rather than switching rendering engines.

Usage (per-clip script):

    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
    from breaking_news_overlay import render_breaking_news

    render_breaking_news(
        clip_id="tb0XX_some_slug",
        src_path=Path("/home/leo/clips-channel/test-batch/exports/tb0XX_cut_raw.mp4"),
        headline_lines=["Two-line headline", "goes here"],
        context_line="City, ST -- Aug 27, 2026",
        source="Outlet Name",
        out_dir=Path("/home/leo/clips-channel/test-batch/exports"),
    )
"""

import subprocess
from pathlib import Path

from PIL import ImageFont

HOME = Path("/home/leo")
FFMPEG = str(HOME / ".local" / "bin" / "ffmpeg")
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Platform export presets: (suffix, crf). All 1080x1920, H.264, CRF 20-23
# per SKILL.md export hygiene section.
PLATFORMS = {
    "tiktok": ("tiktok_9x16", 20),
    "ytshorts": ("ytshorts_9x16", 23),
    "igreels": ("igreels_9x16", 20),
}

CANVAS_W = 1080
SAFE_MARGIN = 60  # each side; matches the margin convention used elsewhere in this pipeline
MIN_FONTSIZE = 24  # never shrink past this — a title this small has failed anyway


def _measure_width(text, fontfile, fontsize):
    font = ImageFont.truetype(fontfile, fontsize)
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def fit_fontsize(text, fontfile, start_size, max_width=None, min_size=MIN_FONTSIZE):
    """Return the largest fontsize <= start_size at which `text` fits max_width.

    Pure measurement via PIL — no rendering happens here, ffmpeg drawtext
    still does the actual compositing. Shrinks in steps of 1pt; a bare-metal
    binary search isn't worth it at these string lengths and font sizes.
    """
    if max_width is None:
        max_width = CANVAS_W - 2 * SAFE_MARGIN
    size = start_size
    while size > min_size and _measure_width(text, fontfile, size) > max_width:
        size -= 1
    return size


def escape_drawtext(text):
    """Escape text for safe use inside an ffmpeg drawtext filter value.

    ffmpeg's filtergraph parser treats , and : as structural separators and
    ' as a quote — any of these appearing literally in overlay text (e.g.
    "a dumb, stupid country" or "Source: Outlet") breaks filter parsing
    unless escaped. Backslash must be escaped first so we don't double-escape
    the backslashes this function itself inserts.
    """
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace(",", "\\,")
    text = text.replace("'", "’")  # apostrophes -> typographic quote, avoids quoting issues
    return text


def _drawtext(text, fontsize, color, y, fontfile, x="(w-text_w)/2"):
    return (
        f"drawtext=text='{escape_drawtext(text)}':fontsize={fontsize}:"
        f"fontcolor={color}:x={x}:y={y}:fontfile={fontfile}"
    )


def build_overlay_filter(headline_lines, context_line, source, quote_line=None):
    """Build the Tier A overlay filter chain: scale/crop to 9:16 + drawtext stack.

    Every line's fontsize is fit to the canvas width before rendering — see
    fit_fontsize(). A line that's short enough renders at the original fixed
    size unchanged; only oversized text actually shrinks.
    """
    # setsar=1 (added 2026-08-28): without it, some source footage carries
    # a non-1:1 sample aspect ratio through scale/pad (observed: 10240:10239
    # on real produced clips) — visually invisible but confuses strict
    # metadata parsers. Confirmed via a real test: Telegram's bot API stored
    # a clip with this SAR as duration=0, width=320, height=320 and refused
    # to play it, even though the file was a completely normal 30s 1080x1920
    # video. Resetting SAR to 1:1 right after scale/pad is a one-line fix
    # with no visual effect (1080x1920 pixels are already square-equivalent
    # at this point) and no impact on any downstream step.
    #
    # Scaling: force_original_aspect_ratio=decrease + pad (changed 2026-08-28
    # in response to Leo's "video is out of frame" feedback on tb020-c2).
    # The old increase+crop approach scaled a 16:9 source to 3413px wide to
    # fill the 1920px height, then center-cropped to 1080px — losing ~68% of
    # the source width and cutting off right-side chyrons/text in split-screen
    # news broadcasts. decrease+pad scales to fit within the target
    # (preserving ALL source content) and fills the remainder with black
    # letterbox bars. Black bars are standard for 16:9→9:16 and never hide
    # content, which is the priority for news where edge graphics matter.
    parts = ["scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"]

    y = 180
    for line in headline_lines:
        size = fit_fontsize(line, FONT_BOLD, 52)
        parts.append(_drawtext(line, size, "yellow", y, FONT_BOLD))
        y += 60

    if quote_line:
        size = fit_fontsize(quote_line, FONT_BOLD, 44)
        parts.append(_drawtext(quote_line, size, "white", y + 10, FONT_BOLD))

    size = fit_fontsize(context_line, FONT_REG, 30)
    parts.append(_drawtext(context_line, size, "white", 1640, FONT_REG))

    source_text = f"Source: {source}"
    size = fit_fontsize(source_text, FONT_REG, 26)
    parts.append(_drawtext(source_text, size, "yellow@0.8", 1690, FONT_REG))

    return ",".join(parts)


def run(cmd, label):
    print(f"\n{'='*60}\n  {label}\n{'='*60}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"ERROR: {proc.returncode}")
        print(proc.stderr[-1500:])
        return False
    print((proc.stderr + proc.stdout)[-300:])
    return True


def export_platforms(source_path, clip_id, out_dir):
    """Re-encode `source_path` into the 3 platform-native exports.

    Split out of render_breaking_news() (2026-08-28) so it can run on
    whatever the actual FINAL video is — after subtitles (burn_subtitles.py)
    and broadcast motion graphics (broadcast_graphics.py) are applied, not
    just the freshly-overlaid master — so every platform export inherits the
    complete production, not just the headline. See content-agent-prompt.md
    §5 for the intended step order this now supports.
    """
    out_dir = Path(out_dir)
    source_path = Path(source_path)
    outputs = {}
    for platform, (suffix, crf) in PLATFORMS.items():
        out_path = out_dir / f"{clip_id}_{suffix}.mp4"
        cmd = [
            FFMPEG, "-y", "-i", str(source_path),
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(out_path),
        ]
        if not run(cmd, f"Exporting {platform} ({out_path.name})"):
            raise RuntimeError(f"{clip_id}: {platform} export failed")
        print(f"  ✅ {out_path.name}: {out_path.stat().st_size / 1_048_576:.1f} MB")
        outputs[platform] = out_path
    return outputs


def render_breaking_news(
    clip_id,
    src_path,
    headline_lines,
    context_line,
    source,
    out_dir,
    quote_line=None,
    audio_volume=None,
    export=True,
):
    """Render a Tier A breaking-news master, optionally + 3 platform-native exports.

    No narration/voiceover is added — original clip audio passes through
    (optionally gain-adjusted via audio_volume, e.g. 7.5 to boost quiet audio).

    Pass export=False when subtitles/broadcast-graphics still need to be
    applied to the master before platform export — call export_platforms()
    yourself once those steps are done, on their final output, instead.
    export=True (default) preserves the original one-shot behavior for
    simple clips with no subtitle/graphics pass.
    """
    out_dir = Path(out_dir)
    src_path = Path(src_path)
    master = out_dir / f"{clip_id}_master.mp4"

    overlay = build_overlay_filter(headline_lines, context_line, source, quote_line)

    cmd_master = [
        FFMPEG, "-y", "-i", str(src_path),
        "-vf", overlay,
    ]
    if audio_volume:
        cmd_master += ["-af", f"volume={audio_volume}"]
    cmd_master += [
        "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(master),
    ]

    if not run(cmd_master, f"Producing {clip_id} master"):
        raise RuntimeError(f"{clip_id}: master render failed")

    print(f"\n✅ Master: {master.stat().st_size / 1_048_576:.1f} MB")

    outputs = {"master": master}
    if export:
        outputs.update(export_platforms(master, clip_id, out_dir))

    return outputs
