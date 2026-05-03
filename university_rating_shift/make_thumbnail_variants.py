from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
W, H = 1920, 1080
FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text(draw, xy, s, size, fill, bold=True, anchor=None, stroke=0, stroke_fill=(0, 0, 0)):
    draw.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def bg_warm():
    img = Image.new("RGB", (W, H), (247, 244, 236))
    p = img.load()
    for y in range(H):
        for x in range(W):
            v = int(18 * (x / W) + 10 * (y / H))
            p[x, y] = (247 - v, 244 - v, 236 - v)
    return img


def bg_deep():
    img = Image.new("RGB", (W, H), (18, 22, 28))
    p = img.load()
    for y in range(H):
        for x in range(W):
            d = math.hypot((x - 1550) / W, (y - 220) / H)
            glow = max(0, 1 - d * 2.0)
            r = int(18 + 35 * glow)
            g = int(22 + 80 * glow)
            b = int(28 + 105 * glow)
            p[x, y] = (r, g, b)
    return img


def bg_red():
    img = Image.new("RGB", (W, H), (34, 18, 20))
    p = img.load()
    for y in range(H):
        for x in range(W):
            glow = max(0, 1 - math.hypot((x - 380) / W, (y - 420) / H) * 1.9)
            p[x, y] = (int(34 + 120 * glow), int(18 + 22 * glow), int(20 + 18 * glow))
    return img


def variant_a(path: Path):
    img = bg_warm()
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 96), fill=(21, 24, 29))
    text(d, (72, 27), "大学選び、親の常識は古い？", 42, (255, 255, 255), True)
    d.rounded_rectangle((86, 165, 860, 300), 18, fill=(230, 55, 49))
    text(d, (126, 188), "親世代は", 72, (255, 255, 255), True)
    text(d, (540, 188), "知らない", 72, (255, 230, 96), True)
    text(d, (82, 354), "評価が", 132, (21, 24, 29), True)
    text(d, (82, 500), "変わった大学", 150, (21, 24, 29), True)
    text(d, (96, 712), "TOP10", 190, (230, 55, 49), True)
    d.rounded_rectangle((1060, 142, 1800, 880), 28, fill=(21, 24, 29))
    text(d, (1430, 206), "昔", 76, (180, 190, 198), True, anchor="ma")
    text(d, (1430, 326), "中堅？", 106, (255, 255, 255), True, anchor="ma")
    d.line((1160, 505, 1700, 505), fill=(255, 230, 96), width=8)
    text(d, (1430, 576), "今", 76, (255, 230, 96), True, anchor="ma")
    text(d, (1430, 698), "就職強者", 104, (255, 255, 255), True, anchor="ma")
    d.rounded_rectangle((80, 945, 1840, 1032), 14, fill=(255, 230, 96))
    text(d, (118, 964), "偏差値だけでは見えない“いま選ばれる大学”", 50, (21, 24, 29), True)
    img.save(path, quality=95)


def variant_b(path: Path):
    img = bg_deep()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((72, 72, 392, 164), 18, fill=(255, 213, 72))
    text(d, (104, 94), "受験生必見", 46, (18, 22, 28), True)
    text(d, (80, 244), "親の大学観", 128, (255, 255, 255), True, stroke=2)
    text(d, (80, 392), "もう古い", 164, (255, 213, 72), True, stroke=2)
    d.rounded_rectangle((92, 640, 980, 760), 18, fill=(226, 45, 50))
    text(d, (135, 666), "評価が変わった大学", 62, (255, 255, 255), True)
    text(d, (1160, 178), "TOP", 196, (255, 255, 255), True)
    text(d, (1140, 385), "10", 330, (255, 213, 72), True)
    d.rounded_rectangle((80, 880, 1780, 984), 16, fill=(255, 255, 255))
    text(d, (126, 905), "志願者数・就職・学部改革で独自ランキング", 56, (18, 22, 28), True)
    img.save(path, quality=95)


def variant_c(path: Path):
    img = bg_red()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((80, 70, 510, 160), 18, fill=(255, 255, 255))
    text(d, (116, 92), "親世代とズレる", 48, (32, 18, 20), True)
    text(d, (78, 244), "昔の評価で", 116, (255, 255, 255), True, stroke=2)
    text(d, (78, 384), "選ぶと損", 158, (255, 226, 79), True, stroke=2)
    text(d, (92, 615), "評価急変大学", 114, (255, 255, 255), True, stroke=2)
    d.rounded_rectangle((1130, 166, 1780, 820), 34, fill=(255, 226, 79))
    text(d, (1455, 238), "TOP", 128, (32, 18, 20), True, anchor="ma")
    text(d, (1450, 398), "10", 260, (32, 18, 20), True, anchor="ma")
    text(d, (1455, 720), "2026版", 78, (178, 35, 38), True, anchor="ma")
    d.rounded_rectangle((90, 906, 1785, 1008), 12, fill=(255, 255, 255))
    text(d, (130, 932), "就職・人気・新学部で見た“今の実力”", 56, (32, 18, 20), True)
    img.save(path, quality=95)


def main():
    DIST.mkdir(exist_ok=True)
    variant_a(DIST / "thumbnail_v2_a_editorial.jpg")
    variant_b(DIST / "thumbnail_v2_b_dark.jpg")
    variant_c(DIST / "thumbnail_v2_c_warning.jpg")
    variant_b(DIST / "thumbnail_oyasedai_hyouka_daigaku.jpg")
    print("created 3 variants; selected B as main")


if __name__ == "__main__":
    main()
