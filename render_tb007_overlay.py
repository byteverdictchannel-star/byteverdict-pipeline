#!/usr/bin/env python3
"""Render tb007 Ratcliffe Moscow overlay PNG at 1080x1920 (9:16 vertical)."""

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

# Safe zones (YouTube Shorts UI overlap):
#  - Bottom ~15% (y > 1632) obscured by caption/description/action rail
#  - Right ~10% (x > 972) obscured by like/comment/share/follow rail
SAFE_BOTTOM = 1632
SAFE_RIGHT = 972

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def text_w(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]

def draw_text_box(draw, cx, y, text, font, fill, box_alpha=150, pad_x=24, pad_y=14):
    """Centered text with semi-transparent black backdrop."""
    tw = text_w(draw, text, font)
    th = text_w(draw, "Ag", font)  # approx line height
    box_w = tw + pad_x * 2
    box_h = th + pad_y * 2
    x0 = cx - box_w // 2
    y0 = y - pad_y
    draw.rectangle(
        [x0, y0, x0 + box_w, y0 + box_h],
        fill=(0, 0, 0, box_alpha)
    )
    draw.text((cx - tw // 2, y), text, font=font, fill=fill)

def draw_multiline_box(draw, cx, y_start, lines, font, fill, line_gap=10, box_alpha=150, pad_x=24, pad_y=14):
    """Multiple centered lines, each with its own backdrop box."""
    n = len(lines)
    th = text_w(draw, "Ag", font)
    total_h = n * (th + line_gap) - line_gap
    y = y_start
    for line in lines:
        draw_text_box(draw, cx, y, line, font, fill, box_alpha, pad_x, pad_y)
        y += th + line_gap

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

WHITE = (255, 255, 255, 255)
GRAY  = (180, 180, 180, 255)  # attribution
CAPTION_GOLD = (255, 225, 150, 255)  # burned-in caption distinct color

# ── HEADLINE (top, bold, large) ──────────────────────────────────────────
# Position: y=200 (clear of top, well above bottom safe zone)
headline_font = load_font(FONT_BOLD, 52)
headline_text = "America's top spy landed in Moscow."
draw_text_box(d, W // 2, 200, headline_text, headline_font, WHITE, box_alpha=160)

# Second headline line
headline2_font = load_font(FONT_BOLD, 46)
headline2_text = "No one would say why."
draw_text_box(d, W // 2, 270, headline2_text, headline2_font, WHITE, box_alpha=160)

# ── CONTEXT LINES (below headline, regular weight, smaller) ──────────────
context_font = load_font(FONT_REG, 30)
context_lines = [
    "A US military plane landed with no manifest, no names, no explanation.",
    "Neither Washington nor Moscow would confirm who was on board.",
]
draw_multiline_box(d, W // 2, 360, context_lines, context_font, WHITE, line_gap=14, box_alpha=150)

# ── BURNED-IN CAPTION BAR (spoken hook — visually distinct) ───────────────
# This carries the "Picture this" spoken hook for muted viewers.
# Position: lower-middle, above bottom safe zone (y=1400).
# Distinct color (warm gold), smaller text, single line, narrower box.
caption_font = load_font(FONT_REG, 28)
caption_text = '"Picture this: a US military plane leaves Washington. No notices. Heads to Russia."'
# Measure and center
ctw = text_w(d, caption_text, caption_font)
cx_box_w = ctw + 36
cx0 = (W - cx_box_w) // 2
cx1 = cx0 + cx_box_w
cy0 = 1390
cy1 = cy0 + 52
d.rectangle([cx0, cy0, cx1, cy1], fill=(20, 20, 20, 200))
# Gold left accent bar
d.rectangle([cx0, cy0, cx0 + 6, cy1], fill=CAPTION_GOLD)
d.text((cx0 + 18, cy0 + 12), caption_text, font=caption_font, fill=CAPTION_GOLD)

# ── SOURCE ATTRIBUTION (bottom, above safe zone) ──────────────────────────
attr_font = load_font(FONT_REG, 22)
attr_text = "Source: DW News"
# Position: right-aligned but within safe zone (x <= SAFE_RIGHT)
attr_w = text_w(d, attr_text, attr_font)
attr_x = SAFE_RIGHT - attr_w  # right edge at safe zone boundary
attr_y = 1560
d.text((attr_x, attr_y), attr_text, font=attr_font, fill=GRAY)

# ── DATE (small, below attribution) ──────────────────────────────────────
date_font = load_font(FONT_REG, 18)
date_text = "August 25, 2026"
d.text((attr_x, attr_y + 24), date_text, font=date_font, fill=(140, 140, 140, 255))

img.save("/home/leo/clips-channel/test-batch/overlays/tb007_overlay.png")
print("Saved tb007_overlay.png")
