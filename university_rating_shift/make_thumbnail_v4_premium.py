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


def rounded_rect_alpha(base, box, radius, fill, outline=None, width=1, blur=0):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def premium_bg(seed=4):
    random.seed(seed)
    img = Image.new("RGBA", (W, H), (7, 11, 18, 255))
    pix = img.load()
    for y in range(H):
        for x in range(W):
            nx, ny = x / W, y / H
            glow1 = max(0, 1 - math.hypot(nx - 0.86, ny - 0.28) * 1.8)
            glow2 = max(0, 1 - math.hypot(nx - 0.28, ny - 0.82) * 2.2)
            glow3 = max(0, 1 - math.hypot(nx - 0.55, ny - 0.44) * 2.8)
            r = int(7 + 18 * glow1 + 6 * glow2 + 8 * glow3)
            g = int(11 + 82 * glow1 + 54 * glow2 + 18 * glow3)
            b = int(18 + 105 * glow1 + 80 * glow2 + 26 * glow3)
            pix[x, y] = (r, g, b, 255)

    d = ImageDraw.Draw(img, "RGBA")
    for x in range(-120, W + 160, 56):
        d.line((x, 0, x + 360, H), fill=(255, 255, 255, 12), width=1)
    for y in range(40, H, 54):
        d.line((0, y, W, y - 92), fill=(255, 255, 255, 9), width=1)

    # Fine noise for a less flat, more editorial finish.
    noise = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(noise)
    for _ in range(9500):
        x, y = random.randrange(W), random.randrange(H)
        v = random.randrange(18, 48)
        nd.point((x, y), fill=(255, 255, 255, v))
    img = Image.alpha_composite(img, noise)
    return img


def draw_data_object(d):
    # Isometric premium "ranking engine" block.
    cx, cy = 884, 390
    top = [(704, 236), (1042, 174), (1150, 304), (810, 374)]
    side = [(810, 374), (1150, 304), (1150, 506), (810, 596)]
    front = [(704, 236), (810, 374), (810, 596), (704, 454)]
    d.polygon(side, fill=(16, 58, 72, 230))
    d.polygon(front, fill=(19, 35, 48, 240))
    d.polygon(top, fill=(31, 211, 190, 210))
    d.line(top + [top[0]], fill=(191, 255, 245, 210), width=2)

    for i, h in enumerate([74, 104, 142, 184, 226]):
        x = 852 + i * 52
        y = 475 - h
        d.rounded_rectangle((x, y, x + 32, 504), 8, fill=(236, 255, 118, 235))
        d.rounded_rectangle((x + 8, y + 8, x + 24, 504), 4, fill=(172, 255, 224, 120))

    for r, alpha in [(188, 46), (244, 30), (304, 18)]:
        d.arc((cx - r, cy - r, cx + r, cy + r), 205, 340, fill=(108, 236, 255, alpha), width=2)

    for px, py in [(716, 228), (1040, 174), (1138, 305), (812, 594), (1008, 520)]:
        d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(236, 255, 118, 230))


def v4_main(path: Path):
    img = premium_bg()
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((54, 74, 626, 632), 34, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    img.alpha_composite(shadow)

    rounded_rect_alpha(
        img,
        (58, 70, 622, 628),
        32,
        fill=(9, 15, 25, 176),
        outline=(159, 238, 255, 54),
        width=1,
    )
    d = ImageDraw.Draw(img, "RGBA")
    draw_data_object(d)

    text(d, (94, 116), "DATA ALCHEMIST", 24, (144, 228, 234, 220), True)
    text(d, (94, 186), "大学評価、", 82, (245, 249, 246, 255), True)
    text(d, (94, 292), "逆転。", 104, (224, 255, 92, 255), True)
    d.line((94, 424, 520, 424), fill=(115, 230, 241, 120), width=2)
    text(d, (94, 472), "親世代の常識を更新する", 34, (210, 226, 229, 240), True)
    text(d, (94, 526), "TOP10", 62, (245, 249, 246, 255), True)
    d.rounded_rectangle((356, 508, 532, 582), 18, fill=(224, 255, 92, 245))
    text(d, (444, 524), "2026", 34, (8, 14, 22, 255), True, anchor="ma")

    text(d, (1096, 82), "VALUE SHIFT", 22, (200, 244, 248, 168), True, anchor="ra")
    img.convert("RGB").save(path, quality=94)


def v4_alt_glass(path: Path):
    img = premium_bg(9)
    d = ImageDraw.Draw(img, "RGBA")
    rounded_rect_alpha(img, (76, 90, 1194, 620), 42, fill=(240, 248, 255, 28), outline=(255, 255, 255, 62), width=1)
    rounded_rect_alpha(img, (128, 156, 528, 538), 28, fill=(5, 9, 16, 178), outline=(255, 255, 255, 48), width=1)
    rounded_rect_alpha(img, (754, 156, 1148, 538), 28, fill=(224, 255, 92, 230), outline=(255, 255, 255, 70), width=1)
    text(d, (328, 214), "OLD", 40, (150, 166, 178, 255), True, anchor="ma")
    text(d, (328, 328), "親の常識", 58, (245, 249, 246, 255), True, anchor="ma")
    text(d, (328, 438), "過去の評価", 42, (164, 184, 196, 255), True, anchor="ma")
    d.polygon([(585, 340), (685, 340), (685, 286), (748, 360), (685, 434), (685, 380), (585, 380)], fill=(108, 236, 255, 230))
    text(d, (951, 214), "NOW", 40, (8, 14, 22, 255), True, anchor="ma")
    text(d, (951, 332), "評価逆転", 66, (8, 14, 22, 255), True, anchor="ma")
    text(d, (951, 442), "TOP10", 62, (8, 14, 22, 255), True, anchor="ma")
    text(d, (640, 654), "大学評価、逆転。", 38, (245, 249, 246, 255), True, anchor="ma")
    img.convert("RGB").save(path, quality=94)


def v4_alt_minimal(path: Path):
    img = Image.new("RGBA", (W, H), (236, 241, 236, 255))
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(18):
        x = 660 + i * 24
        y = 512 - int((i / 17) ** 1.7 * 330)
        d.rounded_rectangle((x, y, x + 14, 560), 7, fill=(9, 22, 33, 255))
    d.rounded_rectangle((726, 128, 1134, 560), 36, fill=(11, 16, 24, 255))
    text(d, (930, 208), "VALUE", 44, (164, 181, 190, 255), True, anchor="ma")
    text(d, (930, 326), "SHIFT", 104, (224, 255, 92, 255), True, anchor="ma")
    text(d, (930, 476), "TOP10", 64, (245, 249, 246, 255), True, anchor="ma")
    text(d, (88, 142), "大学評価、", 84, (11, 16, 24, 255), True)
    text(d, (88, 250), "逆転。", 118, (11, 16, 24, 255), True)
    d.rounded_rectangle((92, 454, 496, 524), 18, fill=(224, 255, 92, 255))
    text(d, (294, 470), "親世代の常識を更新", 34, (11, 16, 24, 255), True, anchor="ma")
    img.convert("RGB").save(path, quality=94)


def main():
    DIST.mkdir(exist_ok=True)
    v4_main(DIST / "thumbnail_v4_premium_main.jpg")
    v4_alt_glass(DIST / "thumbnail_v4_glass_before_after.jpg")
    v4_alt_minimal(DIST / "thumbnail_v4_minimal_value_shift.jpg")
    v4_main(DIST / "thumbnail_oyasedai_hyouka_daigaku.jpg")
    print("created premium v4 thumbnails; selected premium_main")


if __name__ == "__main__":
    main()
