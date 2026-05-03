from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
W, H = 1280, 720
FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"


PALETTES = {
    "midnight_emerald": {
        "bg0": (7, 14, 24),
        "bg1": (12, 86, 76),
        "bg2": (24, 45, 98),
        "band0": (10, 42, 76),
        "band1": (21, 147, 132),
        "gold0": (255, 228, 99),
        "gold1": (205, 133, 18),
        "pill": (13, 28, 52),
        "pill_text": (83, 218, 232),
        "badge": (210, 47, 75),
    },
    "royal_burgundy": {
        "bg0": (12, 8, 25),
        "bg1": (94, 28, 74),
        "bg2": (33, 45, 108),
        "band0": (32, 36, 100),
        "band1": (122, 39, 94),
        "gold0": (255, 220, 91),
        "gold1": (207, 118, 18),
        "pill": (18, 18, 43),
        "pill_text": (225, 185, 255),
        "badge": (220, 49, 70),
    },
    "noir_cyan": {
        "bg0": (5, 8, 14),
        "bg1": (13, 70, 103),
        "bg2": (30, 30, 75),
        "band0": (10, 46, 78),
        "band1": (15, 112, 160),
        "gold0": (255, 225, 80),
        "gold1": (198, 130, 15),
        "pill": (9, 18, 32),
        "pill_text": (82, 211, 255),
        "badge": (196, 40, 62),
    },
}


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_layer(size=(W, H)):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def draw_text(draw, xy, s, size, fill, bold=True, anchor=None, stroke=0, stroke_fill=(0, 0, 0), spacing=4):
    draw.multiline_text(
        xy,
        s,
        font=font(size, bold),
        fill=fill,
        anchor=anchor,
        stroke_width=stroke,
        stroke_fill=stroke_fill,
        spacing=spacing,
        align="center",
    )


def make_bg(p):
    img = Image.new("RGBA", (W, H), (*p["bg0"], 255))
    pix = img.load()
    for y in range(H):
        for x in range(W):
            nx, ny = x / W, y / H
            c = max(0, 1 - math.hypot(nx - 0.52, ny - 0.34) * 1.45)
            l = max(0, 1 - math.hypot(nx - 0.08, ny - 0.18) * 2.0)
            r = max(0, 1 - math.hypot(nx - 0.96, ny - 0.55) * 2.0)
            b = max(0, 1 - math.hypot(nx - 0.48, ny - 0.72) * 1.7)
            base = p["bg0"]
            a = p["bg1"]
            q = p["bg2"]
            rr = int(base[0] + a[0] * c * 0.78 + q[0] * r * 0.38 + a[0] * l * 0.22 + p["band1"][0] * b * 0.1)
            gg = int(base[1] + a[1] * c * 0.78 + q[1] * r * 0.38 + a[1] * l * 0.22 + p["band1"][1] * b * 0.1)
            bb = int(base[2] + a[2] * c * 0.78 + q[2] * r * 0.38 + a[2] * l * 0.22 + p["band1"][2] * b * 0.1)
            pix[x, y] = (min(rr, 255), min(gg, 255), min(bb, 255), 255)

    d = ImageDraw.Draw(img, "RGBA")
    # dark top/bottom vignette like the original.
    d.rectangle((0, 0, W, 90), fill=(0, 0, 0, 88))
    d.rectangle((0, H - 118, W, H), fill=(0, 0, 0, 122))

    # grid and subtle texture.
    for x in range(-80, W + 120, 96):
        d.line((x, 0, x + 120, H), fill=(255, 255, 255, 7), width=1)
    for y in range(122, 608, 54):
        d.line((0, y, W, y + 12), fill=(255, 255, 255, 6), width=1)

    random.seed(42)
    for _ in range(1300):
        x = random.randrange(W)
        y = random.randrange(H)
        d.point((x, y), fill=(255, 255, 255, random.randrange(3, 8)))

    # faint background words.
    draw_text(d, (150, 158), "Technology", 42, (255, 255, 255, 10), False, anchor="ma")
    draw_text(d, (1030, 520), "Innovation", 42, (255, 255, 255, 13), False, anchor="ma")
    draw_text(d, (222, 506), "Selection", 32, (255, 255, 255, 8), False, anchor="ma")
    return img


def gold_text(base, xy, s, size, p, anchor="ma", stroke=3):
    # soft outer glow
    glow = text_layer()
    gd = ImageDraw.Draw(glow, "RGBA")
    draw_text(gd, xy, s, size, (*p["gold0"], 210), True, anchor=anchor, stroke=stroke, stroke_fill=(64, 40, 0, 190))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))

    layer = text_layer()
    d = ImageDraw.Draw(layer, "RGBA")
    # shadow
    draw_text(d, (xy[0] + 6, xy[1] + 7), s, size, (0, 0, 0, 88), True, anchor=anchor, stroke=stroke, stroke_fill=(0, 0, 0, 90))
    # two-tone gold by drawing lower darker duplicate clipped-ish via full text first
    draw_text(d, xy, s, size, (*p["gold0"], 255), True, anchor=anchor, stroke=stroke, stroke_fill=(78, 48, 4, 255))
    base.alpha_composite(layer)


def white_title(base, xy, s, size):
    layer = text_layer()
    d = ImageDraw.Draw(layer, "RGBA")
    draw_text(d, (xy[0] + 5, xy[1] + 7), s, size, (0, 0, 0, 140), True, anchor="ma", stroke=2, stroke_fill=(0, 0, 0, 170), spacing=8)
    draw_text(d, xy, s, size, (252, 253, 255, 255), True, anchor="ma", stroke=1, stroke_fill=(18, 20, 30, 210), spacing=8)
    base.alpha_composite(layer)


def tilted_badge(base, p):
    badge = Image.new("RGBA", (260, 114), (0, 0, 0, 0))
    d = ImageDraw.Draw(badge, "RGBA")
    d.rounded_rectangle((8, 8, 250, 106), 10, fill=(*p["badge"], 255), outline=(255, 152, 168, 90), width=2)
    draw_text(d, (130, 35), "決定版", 40, (255, 255, 255, 255), True, anchor="ma")
    badge = badge.rotate(357, expand=True, resample=Image.Resampling.BICUBIC)
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow.alpha_composite(badge.filter(ImageFilter.GaussianBlur(3)), (34, 38))
    base.alpha_composite(shadow)
    base.alpha_composite(badge, (32, 34))


def pill(base, p):
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((986, 40, 1248, 98), 28, fill=(*p["pill"], 236), outline=(255, 255, 255, 18), width=1)
    draw_text(d, (1117, 55), "独自ランキング", 30, (*p["pill_text"], 255), True, anchor="ma")


def bottom_band(base, p):
    band = Image.new("RGBA", (W, 92), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band, "RGBA")
    for x in range(W):
        t = x / W
        col = tuple(int(p["band0"][i] * (1 - t) + p["band1"][i] * t) for i in range(3))
        bd.line((x, 0, x, 92), fill=(*col, 228))
    band = band.filter(ImageFilter.GaussianBlur(0.15))
    base.alpha_composite(band, (0, 630))
    d = ImageDraw.Draw(base, "RGBA")
    d.line((0, 630, W, 630), fill=(255, 255, 255, 42), width=1)
    d.line((0, 626, W, 626), fill=(0, 0, 0, 86), width=3)
    draw_text(
        d,
        (640, 654),
        "志願者数・就職・学部改革データ完全集計",
        43,
        (*p["gold0"], 255),
        True,
        anchor="ma",
        stroke=2,
        stroke_fill=(0, 0, 0, 220),
    )


def render(name: str, filename: str):
    p = PALETTES[name]
    img = make_bg(p)
    d = ImageDraw.Draw(img, "RGBA")
    tilted_badge(img, p)
    pill(img, p)
    draw_text(d, (640, 102), "V A L U E   S H I F T", 32, (235, 235, 248, 214), True, anchor="ma")
    white_title(img, (640, 240), "親世代と評価が変わった\n大学ランキング", 70)
    gold_text(img, (640, 498), "2026", 120, p)
    bottom_band(img, p)
    out = DIST / filename
    img.convert("RGB").save(out, quality=95)
    return out


def main():
    DIST.mkdir(exist_ok=True)
    main = render("royal_burgundy", "thumbnail_ref_style_v2_royal_burgundy.jpg")
    render("midnight_emerald", "thumbnail_ref_style_v2_midnight_emerald.jpg")
    render("noir_cyan", "thumbnail_ref_style_v2_noir_cyan.jpg")
    img = Image.open(main)
    img.save(DIST / "thumbnail_oyasedai_hyouka_daigaku.jpg", quality=95)
    print(main)


if __name__ == "__main__":
    main()
