from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
W, H = 1280, 720
FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text(draw, xy, s, size, fill, bold=True, anchor=None, stroke=0, stroke_fill=(0, 0, 0)):
    draw.text(
        xy,
        s,
        font=font(size, bold),
        fill=fill,
        anchor=anchor,
        stroke_width=stroke,
        stroke_fill=stroke_fill,
    )


def make_bg():
    img = Image.new("RGB", (W, H), (8, 18, 19))
    pix = img.load()
    for y in range(H):
        for x in range(W):
            nx, ny = x / W, y / H
            center = max(0, 1 - math.hypot(nx - 0.52, ny - 0.43) * 1.55)
            left = max(0, 1 - math.hypot(nx - 0.1, ny - 0.45) * 2.0)
            right = max(0, 1 - math.hypot(nx - 0.92, ny - 0.36) * 2.1)
            r = int(8 + 8 * center + 2 * left + 7 * right)
            g = int(18 + 72 * center + 24 * left + 52 * right)
            b = int(19 + 58 * center + 22 * left + 40 * right)
            pix[x, y] = (r, g, b)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    for i in range(0, W, 88):
        d.line((i, 0, i + 320, H), fill=(255, 255, 255, 12), width=1)
    for y in range(118, H, 74):
        d.line((0, y, W, y - 44), fill=(255, 255, 255, 8), width=1)
    d.rectangle((0, 0, W, 82), fill=(0, 0, 0, 104))
    d.rectangle((0, H - 82, W, H), fill=(0, 0, 0, 122))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def main():
    DIST.mkdir(exist_ok=True)
    img = make_bg()
    d = ImageDraw.Draw(img, "RGBA")

    # Subtle background words, like the reference.
    text(d, (96, 474), "VALUE", 70, (45, 102, 96, 255), True)
    text(d, (900, 438), "Reputation", 48, (66, 122, 116, 255), False)
    text(d, (896, 516), "University", 48, (54, 108, 102, 255), False)

    # Left badge, matching the reference layout but with a richer accent.
    d.rounded_rectangle((34, 42, 178, 106), 10, fill=(199, 50, 61, 255))
    text(d, (106, 56), "決定版", 32, (255, 255, 255), True, anchor="ma")

    # Right small pill.
    d.rounded_rectangle((1048, 52, 1215, 94), 20, fill=(13, 76, 83, 230), outline=(83, 210, 196, 128), width=1)
    text(d, (1132, 61), "独自ランキング", 22, (189, 255, 239), True, anchor="ma")

    # English eyebrow.
    text(d, (640, 92), "VALUE SHIFT UNIVERSITY RANKING", 28, (214, 238, 232), True, anchor="ma")

    # Main title.
    text(d, (640, 184), "親世代と評価が変わった", 66, (247, 250, 247), True, anchor="ma", stroke=2, stroke_fill=(0, 0, 0))
    text(d, (640, 272), "大学ランキング", 74, (247, 250, 247), True, anchor="ma", stroke=2, stroke_fill=(0, 0, 0))

    # Year / hook.
    text(d, (640, 430), "2026", 124, (238, 195, 74), True, anchor="ma", stroke=2, stroke_fill=(64, 42, 6))

    # Bottom band.
    band = Image.new("RGBA", (W, 86), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band, "RGBA")
    for x in range(W):
        t = x / W
        col = (
            int(9 + 18 * t),
            int(72 + 75 * t),
            int(88 + 82 * t),
            226,
        )
        bd.line((x, 0, x, 86), fill=col)
    band = band.filter(ImageFilter.GaussianBlur(0.2))
    img.alpha_composite(band, (0, 584))
    d = ImageDraw.Draw(img, "RGBA")
    d.line((0, 584, W, 584), fill=(210, 255, 238, 64), width=1)
    d.line((0, 669, W, 669), fill=(0, 0, 0, 110), width=2)
    text(d, (640, 604), "志願者数・就職・学部改革データで完全集計", 42, (255, 225, 104), True, anchor="ma", stroke=2)

    out = DIST / "thumbnail_ref_style_recolor.jpg"
    img.convert("RGB").save(out, quality=94)
    img.convert("RGB").save(DIST / "thumbnail_oyasedai_hyouka_daigaku.jpg", quality=94)
    print(out)


if __name__ == "__main__":
    main()
