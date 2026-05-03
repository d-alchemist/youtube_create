from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
W, H = 1280, 720
FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def draw_text(draw, xy, text, size, fill, bold=True, anchor=None, stroke=0, stroke_fill=(0, 0, 0)):
    draw.text(xy, text, font=font(size, bold), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def split_bg(left=(24, 28, 35), right=(255, 178, 35)):
    img = Image.new("RGB", (W, H), left)
    d = ImageDraw.Draw(img)
    d.polygon([(500, 0), (W, 0), (W, H), (405, H)], fill=right)
    d.polygon([(466, 0), (530, 0), (435, H), (371, H)], fill=(255, 255, 255))
    return img


def person_icon(draw, cx, cy, scale, fill, outline=None):
    head_r = int(46 * scale)
    draw.ellipse((cx - head_r, cy - 140 * scale, cx + head_r, cy - 48 * scale), fill=fill, outline=outline, width=4 if outline else 1)
    draw.rounded_rectangle((cx - 82 * scale, cy - 35 * scale, cx + 82 * scale, cy + 135 * scale), int(42 * scale), fill=fill, outline=outline, width=4 if outline else 1)


def phone_mock(draw, box, fill=(18, 20, 24), screen=(33, 168, 132)):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, 34, fill=fill)
    draw.rounded_rectangle((x1 + 18, y1 + 42, x2 - 18, y2 - 32), 18, fill=screen)
    draw.ellipse(((x1 + x2) // 2 - 8, y1 + 18, (x1 + x2) // 2 + 8, y1 + 34), fill=(42, 45, 52))


def variant_1(path: Path):
    img = split_bg()
    d = ImageDraw.Draw(img)
    person_icon(d, 212, 410, 1.25, (77, 84, 96))
    draw_text(d, (210, 95), "親の常識", 68, (255, 255, 255), True, anchor="ma", stroke=3)
    draw_text(d, (210, 185), "古い", 126, (255, 218, 63), True, anchor="ma", stroke=5)
    d.line((70, 320, 390, 605), fill=(232, 46, 53), width=22)
    d.line((390, 320, 70, 605), fill=(232, 46, 53), width=22)

    phone_mock(d, (760, 76, 1085, 612))
    draw_text(d, (922, 162), "2026", 54, (255, 255, 255), True, anchor="ma")
    draw_text(d, (922, 260), "評価", 74, (255, 236, 91), True, anchor="ma")
    draw_text(d, (922, 350), "逆転", 104, (255, 255, 255), True, anchor="ma", stroke=3)
    draw_text(d, (922, 485), "TOP10", 78, (20, 24, 30), True, anchor="ma")
    d.rounded_rectangle((570, 600, 1210, 684), 18, fill=(20, 24, 30))
    draw_text(d, (890, 616), "今、選ばれる大学", 44, (255, 255, 255), True, anchor="ma")
    img.save(path, quality=94)


def variant_2(path: Path):
    img = Image.new("RGB", (W, H), (10, 14, 20))
    d = ImageDraw.Draw(img)
    for i in range(18):
        x = 40 + i * 72
        h = 80 + int(260 * (i / 17) ** 1.7)
        col = (26, 75 + i * 5, 120 + i * 3)
        d.rounded_rectangle((x, H - 110 - h, x + 42, H - 110), 8, fill=col)
    d.polygon([(880, 95), (1148, 95), (1148, 590), (880, 590)], fill=(255, 214, 65))
    d.polygon([(830, 165), (880, 95), (880, 590), (830, 520)], fill=(224, 149, 28))
    draw_text(d, (84, 86), "この大学", 92, (255, 255, 255), True, stroke=4)
    draw_text(d, (82, 210), "化けた", 144, (255, 214, 65), True, stroke=5)
    d.rounded_rectangle((78, 405, 615, 490), 16, fill=(232, 48, 54))
    draw_text(d, (346, 422), "親世代は知らない", 44, (255, 255, 255), True, anchor="ma")
    draw_text(d, (1012, 165), "TOP", 74, (10, 14, 20), True, anchor="ma")
    draw_text(d, (1012, 270), "10", 160, (10, 14, 20), True, anchor="ma")
    draw_text(d, (1012, 515), "ランキング", 50, (10, 14, 20), True, anchor="ma")
    img.save(path, quality=94)


def variant_3(path: Path):
    img = Image.new("RGB", (W, H), (238, 239, 231))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((60, 70, 535, 622), 32, fill=(26, 31, 39))
    d.rounded_rectangle((745, 70, 1220, 622), 32, fill=(255, 194, 44))
    draw_text(d, (298, 112), "昔の評価", 56, (180, 188, 200), True, anchor="ma")
    draw_text(d, (298, 245), "中堅？", 94, (255, 255, 255), True, anchor="ma")
    draw_text(d, (298, 470), "親世代", 74, (255, 216, 69), True, anchor="ma")
    draw_text(d, (982, 112), "今の評価", 56, (35, 28, 18), True, anchor="ma")
    draw_text(d, (982, 245), "就職強者", 80, (35, 28, 18), True, anchor="ma")
    draw_text(d, (982, 470), "受験生", 74, (232, 48, 54), True, anchor="ma")
    d.polygon([(585, 305), (685, 305), (685, 260), (760, 345), (685, 430), (685, 385), (585, 385)], fill=(232, 48, 54))
    draw_text(d, (640, 670), "評価が変わった大学 TOP10", 48, (26, 31, 39), True, anchor="ma")
    img.save(path, quality=94)


def main():
    DIST.mkdir(exist_ok=True)
    variant_1(DIST / "thumbnail_v3_1_parent_vs_2026.jpg")
    variant_2(DIST / "thumbnail_v3_2_baketadaigaku.jpg")
    variant_3(DIST / "thumbnail_v3_3_before_after.jpg")
    variant_2(DIST / "thumbnail_oyasedai_hyouka_daigaku.jpg")
    print("created v3 thumbnails; selected v3_2 as main")


if __name__ == "__main__":
    main()
