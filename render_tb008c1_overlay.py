#!/usr/bin/env python3
"""Render overlay PNG for tb008c1 — Canada retaliatory tariffs (CTV News)"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

# Fonts
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Colors
WHITE = (255, 255, 255)
YELLOW = (255, 210, 50)
LIGHT_GRAY = (200, 200, 200)
DARK_BG = (0, 0, 0)

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

def text_with_bg(draw, xy, text, font, color, bg_alpha=140, padding=10):
    """Draw text with a semi-transparent background box."""
    bbox = draw.textbbox(xy, text, font=font)
    x1, y1 = bbox[0] - padding, bbox[1] - padding
    x2, y2 = bbox[2] + padding, bbox[3] + padding
    # Background box
    draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, bg_alpha))
    # Text
    draw.text(xy, text, font=font, fill=color + (255,))

# --- HEADLINE (top, yellow, bold) ---
try:
    headline_font = ImageFont.truetype(FONT_BOLD, 52)
except:
    headline_font = ImageFont.load_default()

headline_y = 180

# Line 1
text_with_bg(draw, (W//2, headline_y), "Canada hits back with tariffs",
             headline_font, YELLOW, bg_alpha=150, padding=12)

# Line 2
text_with_bg(draw, (W//2, headline_y + 60), "Dollar-for-dollar. $27.6 billion.",
             headline_font, YELLOW, bg_alpha=150, padding=12)

# --- CONTEXT LINES (below headline, white, regular) ---
try:
    context_font = ImageFont.truetype(FONT_REG, 30)
except:
    context_font = ImageFont.load_default()

ctx_y = headline_y + 140

text_with_bg(draw, (W//2, ctx_y), "Canada slapped retaliatory tariffs on ~700 US products — cosmetics, furniture, food.",
             context_font, WHITE, bg_alpha=140, padding=10)

text_with_bg(draw, (W//2, ctx_y + 40), "Trump says the US won't tolerate it.",
             context_font, WHITE, bg_alpha=140, padding=10)

# --- SOURCE ATTRIBUTION (bottom, small, gray) ---
try:
    attr_font = ImageFont.truetype(FONT_REG, 20)
except:
    attr_font = ImageFont.load_default()

attr_y = H - 120
text_with_bg(draw, (W - 20, attr_y), "Source: CTV News",
             attr_font, LIGHT_GRAY, bg_alpha=120, padding=8)

# --- DATE (bottom, small, gray) ---
text_with_bg(draw, (W - 20, attr_y + 28), "August 26, 2026",
             attr_font, LIGHT_GRAY, bg_alpha=120, padding=8)

img.save("/home/leo/clips-channel/test-batch/overlays/tb008c1_overlay.png")
print("Overlay saved: test-batch/overlays/tb008c1_overlay.png")
print(f"Size: {W}x{H}")
