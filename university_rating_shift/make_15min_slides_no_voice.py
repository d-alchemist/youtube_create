from __future__ import annotations

import json
import math
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"
TARGET_SECONDS = 480
TARGET_LABEL = "8min"
TARGET_TITLE = "8分版"
OUT_DIR = DIST / f"slides_{TARGET_LABEL}_no_voice"
REF = ASSETS / "ref_engineering_ranking_maxres.jpg"
FFMPEG = "/opt/anaconda3/bin/ffmpeg"
FFPROBE = "/opt/anaconda3/bin/ffprobe"

W, H = 1920, 1080
FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"

BLUE = (40, 174, 255, 255)
CYAN = (80, 230, 255, 255)
RED = (235, 31, 48, 255)
GOLD = (255, 218, 58, 255)
PINK = (255, 84, 116, 255)
WHITE = (252, 252, 252, 255)
TITLE_BADGE_TEXT = "意外と知らない大学評価の変化"
TITLE_POINT_TEXT = "名前のイメージではなく、いま選ばれている理由に注目します。"


SOURCE_BY_NAME = {
    "千葉工業大学": "2025年度一般選抜 志願者数162,005人 / 私立大学1位",
    "近畿大学": "2026年度一般入試 総志願者数234,245人 / 過去最多",
    "東洋大学": "2025年度志願者数113,762名 / 私立大学全国4位",
    "芝浦工業大学": "THE日本大学ランキング2025 総合32位 / 私立7位",
    "名城大学": "実就職率ランキング 15年連続全国No.1",
    "東京電機大学": "2025年3月卒 就職内定率99.2% / 求人社数17,545社",
    "武蔵野大学": "データサイエンス学部・AI/ビッグデータ教育",
    "金沢工業大学": "プロジェクトデザイン教育 / PBL型の実践教育",
    "國學院大學": "渋谷立地と伝統分野の再評価",
    "東京都市大学": "都市・環境・情報領域へ広がる実学系ブランド",
}

APPLICANT_DATA = [
    ("近畿大学", 234245, "2026年度"),
    ("千葉工業大学", 162005, "2025年度"),
    ("東洋大学", 113762, "2025年度"),
]

METHOD_WEIGHTS = [
    ("志願者数・人気変化", 35),
    ("就職実績・企業評価", 25),
    ("学部改革・時代適合", 25),
    ("親世代イメージとの差", 15),
]

EXPANDED_NOTES = {
    "東京都市大学": [
        "親世代には「武蔵工大」という理工系の印象が残りやすい大学です。",
        "いまは都市生活、環境、情報、建築など、社会課題に近い領域まで見え方が広がっています。",
        "名前の変更だけでなく、理工系の土台を現代的な実学へ接続している点を評価しました。",
    ],
    "國學院大學": [
        "親世代には文学、神道、日本文化の伝統校というイメージが強い大学です。",
        "現在は渋谷という立地、人文系の厚み、法・経済・観光系の展開で、堅実な総合大学として見られています。",
        "派手な改革ではなく、伝統を今の進路価値へつなげ直している点が変化です。",
    ],
    "金沢工業大学": [
        "地方の工業大学という見られ方から、実践型エンジニア教育の大学へ印象が変わっています。",
        "プロジェクトデザイン教育のように、課題発見から設計、実装までを学ぶ仕組みが特徴です。",
        "企業が求める実務接続型の学びと相性がよく、親世代の単純な知名度評価では測りにくい大学です。",
    ],
    "武蔵野大学": [
        "親世代には女子大、文系中心という印象が残りやすい大学です。",
        "いまはAI、データサイエンス、アントレプレナーシップ、サステナビリティなど、新しい学びの展開が速いです。",
        "校名イメージと実際の学部構成の差が大きく、評価が変わった大学として入れています。",
    ],
    "東京電機大学": [
        "電機・工学の専門校という印象は今も強いですが、現代ではIT、メーカー、情報系人材への評価につながっています。",
        "2025年3月卒業生・修了生の就職内定率99.2%、求人社数17,545社という企業接点が大きな根拠です。",
        "地味に見える技術系大学ほど、就職市場での評価が見直されやすくなっています。",
    ],
    "名城大学": [
        "中部の大規模私大という印象から、就職実績で全国的に見られる大学へ変化しています。",
        "学部卒業生2,000人以上の大学で、実就職率ランキング15年連続全国No.1という実績が強いです。",
        "大学名の全国的な派手さより、卒業後の成果を数字で示せる点を評価しました。",
    ],
    "芝浦工業大学": [
        "親世代には地味な工業大学という印象を持たれがちでした。",
        "現在は首都圏理工系の有力校として、理工系人気、国際性、企業評価の面で存在感があります。",
        "THE日本大学ランキング2025で総合32位、私立7位という外部評価も、見方の変化を支えています。",
    ],
    "東洋大学": [
        "中堅私大の一角という見方から、首都圏の人気総合大学という見方へ変わっています。",
        "2025年度の志願者数は113,762名で、私立大学全国4位です。",
        "キャンパス立地、学部規模、受験生からの選ばれ方が、親世代のイメージを更新しています。",
    ],
    "近畿大学": [
        "関西の大規模私大という印象から、実学、広報、改革の全国ブランドへ変わっています。",
        "2026年度一般入試の総志願者数は234,245人で過去最多です。",
        "水産、医療、情報、建築などの実学色に加え、伝え方の強さも評価を押し上げています。",
    ],
    "千葉工業大学": [
        "工業系の単科大学という印象から、AI、宇宙、半導体で注目される大学へ変わっています。",
        "2025年度一般選抜の志願者数は162,005人で私立大学1位です。",
        "時代が求める領域に大学の打ち出しが噛み合い、親世代の知名度評価を大きく超えています。",
    ],
}


@dataclass
class Slide:
    slug: str
    duration: int
    title: str
    subtitle: str
    body: list[str]
    kind: str
    data: dict[str, Any] | None = None
    source: str | None = None

    @property
    def visible_text(self) -> list[str]:
        lines = [self.title]
        if self.subtitle:
            lines.append(self.subtitle)
        lines.extend(self.body)
        if self.source:
            lines.append(f"根拠: {self.source}")
        return lines


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_size(draw: ImageDraw.ImageDraw, lines: list[str], fnt: ImageFont.FreeTypeFont, spacing: int) -> tuple[int, int]:
    if not lines:
        return 0, 0
    widths = []
    heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=fnt)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    return max(widths), sum(heights) + spacing * (len(lines) - 1)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for ch in paragraph:
            trial = current + ch
            if draw.textlength(trial, font=fnt) <= max_w or not current:
                current = trial
            else:
                lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def fit_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    max_size: int,
    min_size: int,
    fill: tuple[int, int, int, int],
    bold: bool = False,
    align: str = "left",
    valign: str = "top",
    stroke: int = 0,
    stroke_fill: tuple[int, int, int, int] = (0, 0, 0, 0),
    spacing_ratio: float = 0.22,
):
    x1, y1, x2, y2 = box
    max_w = x2 - x1
    max_h = y2 - y1
    chosen = None
    for size in range(max_size, min_size - 1, -2):
        fnt = font(size, bold)
        spacing = max(5, int(size * spacing_ratio))
        lines = wrap_text(draw, text, fnt, max_w)
        width, height = text_size(draw, lines, fnt, spacing)
        if width <= max_w and height <= max_h:
            chosen = (fnt, spacing, lines, width, height)
            break
    if chosen is None:
        raise RuntimeError(f"Text overflow: {text[:80]} in box={box}")
    fnt, spacing, lines, _, height = chosen
    if align == "center":
        x = x1 + max_w / 2
        anchor = "ma"
    elif align == "right":
        x = x2
        anchor = "ra"
    else:
        x = x1
        anchor = "la"
    if valign == "center":
        y = y1 + (max_h - height) / 2
    elif valign == "bottom":
        y = y2 - height
    else:
        y = y1
    draw.multiline_text(
        (x, y),
        "\n".join(lines),
        font=fnt,
        fill=fill,
        anchor=anchor,
        spacing=spacing,
        align=align,
        stroke_width=stroke,
        stroke_fill=stroke_fill,
    )


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def neon_rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, color=BLUE, width: int = 3):
    for expand, alpha, w in [(10, 28, 8), (6, 55, 5), (2, 130, 3)]:
        x1, y1, x2, y2 = box
        draw.rounded_rectangle(
            (x1 - expand, y1 - expand, x2 + expand, y2 + expand),
            radius + expand,
            fill=None,
            outline=(color[0], color[1], color[2], alpha),
            width=w,
        )
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=color, width=width)
    x1, y1, x2, _ = box
    mid = (x1 + x2) // 2
    draw.line((x1 + 42, y1 + 2, mid - 45, y1 + 2), fill=(255, 255, 255, 150), width=1)
    draw.line((mid + 45, y1 + 2, x2 - 42, y1 + 2), fill=(255, 255, 255, 150), width=1)
    draw.ellipse((mid - 5, y1 - 5, mid + 5, y1 + 5), fill=(255, 255, 255, 220))


def neon_line(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], color=BLUE, width: int = 3):
    for w, alpha in [(12, 26), (8, 45), (4, 110)]:
        draw.line(points, fill=(color[0], color[1], color[2], alpha), width=w, joint="curve")
    draw.line(points, fill=color, width=width, joint="curve")


def draw_world_dots(draw: ImageDraw.ImageDraw):
    random.seed(8)
    for _ in range(420):
        x = random.randint(760, 1400)
        y = random.randint(28, 225)
        dx = (x - 1080) / 330
        dy = (y - 122) / 95
        if dx * dx + dy * dy < 1.05 and random.random() > 0.18:
            r = 2 if random.random() < 0.82 else 3
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(0, 114, 255, random.randint(42, 120)))
    for _ in range(90):
        x = random.randint(60, 1840)
        y = random.randint(55, 710)
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(0, 108, 255, random.randint(70, 170)))


def draw_tower(draw: ImageDraw.ImageDraw):
    x, y = 1650, 190
    color = (35, 148, 255, 86)
    edge = (50, 180, 255, 150)
    draw.polygon([(x + 115, y - 65), (x + 165, y + 55), (x + 65, y + 55)], fill=(5, 24, 51, 135), outline=edge)
    draw.rectangle((x + 52, y + 54, x + 178, y + 570), fill=(4, 22, 48, 145), outline=edge, width=2)
    draw.rectangle((x + 82, y + 120, x + 148, y + 570), fill=(5, 32, 66, 165), outline=(38, 146, 255, 110), width=1)
    draw.ellipse((x + 86, y + 155, x + 144, y + 213), outline=(75, 199, 255, 160), width=3)
    draw.line((x + 115, y + 161, x + 115, y + 207), fill=edge, width=2)
    draw.line((x + 92, y + 184, x + 138, y + 184), fill=edge, width=2)
    for row in range(6):
        yy = y + 260 + row * 48
        for col in range(3):
            xx = x + 72 + col * 34
            draw.rectangle((xx, yy, xx + 14, yy + 24), fill=color, outline=(57, 171, 255, 96))
    neon_line(draw, [(x - 35, y + 565), (x + 210, y + 410), (x + 285, y + 345)], color=(0, 128, 255, 255), width=4)


def make_background(seed: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (2, 6, 18, 255))
    px = img.load()
    for y in range(H):
        for x in range(W):
            nx = x / W
            ny = y / H
            blue = int(18 + 45 * nx + 22 * (1 - abs(ny - 0.35)))
            red = int(7 + 38 * max(0, 1 - nx) * max(0, 0.8 - ny))
            green = int(8 + 18 * nx)
            px[x, y] = (red, green, blue, 255)

    d = ImageDraw.Draw(img, "RGBA")
    draw_world_dots(d)
    draw_tower(d)

    # Perspective floor grid.
    horizon = 650
    for i in range(-9, 17):
        start_x = 960 + i * 96
        end_x = 960 + i * 260
        d.line((start_x, horizon, end_x, H), fill=(0, 126, 255, 72), width=1)
    for i in range(0, 10):
        y = int(horizon + (H - horizon) * (i / 9) ** 1.55)
        d.line((0, y, W, y), fill=(0, 126, 255, 58), width=1)

    # Red energy accents, top left.
    neon_line(d, [(-30, 118), (305, 118), (342, 75), (305, 32), (-30, 32)], RED, 3)
    for off in [0, 36, 78]:
        neon_line(d, [(-80, 395 - off), (250, 54 - off)], RED, 3)
    d.polygon([(0, 0), (360, 0), (265, 115), (0, 116)], fill=(80, 0, 12, 76))
    d.rectangle((0, 0, W, 112), fill=(0, 0, 0, 80))
    d.rectangle((0, H - 84, W, H), fill=(0, 0, 0, 160))

    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    for i in range(0, 500, 5):
        vd.rectangle((i, i, W - i, H - i), outline=int(255 * i / 500), width=5)
    vignette = ImageOps.invert(vignette).filter(ImageFilter.GaussianBlur(60))
    return Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, vignette.point(lambda p: int(p * 0.16)))


def header(draw: ImageDraw.ImageDraw, slide: Slide, index: int, total_slides: int):
    counter = [(-8, 30), (302, 30), (356, 73), (302, 116), (-8, 116)]
    for shift, alpha, width in [(10, 40, 9), (5, 88, 5), (0, 255, 3)]:
        pts = [(x + shift, y) for x, y in counter]
        draw.line(pts + [pts[0]], fill=(255, 44, 56, alpha), width=width, joint="curve")
    draw.polygon(counter, fill=(64, 0, 9, 214))
    fit_text(draw, (35, 40, 260, 105), f"{index + 1:02d}/{total_slides}", 55, 42, WHITE, True, "center", "center", 2, (0, 0, 0, 220))

    logo = [(1370, 28), (1868, 28), (1906, 67), (1868, 106), (1370, 106), (1332, 67)]
    inner = [(1386, 42), (1852, 42), (1877, 67), (1852, 92), (1386, 92), (1361, 67)]
    for pts, alpha, width in [(logo, 70, 8), (logo, 180, 4), (inner, 210, 2)]:
        draw.line(pts + [pts[0]], fill=(23, 168, 255, alpha), width=width, joint="curve")
    draw.polygon(logo, fill=(2, 13, 32, 206))
    fit_text(draw, (1415, 42, 1818, 91), "DATA ALCHEMIST", 36, 26, (104, 232, 255, 255), True, "center", "center", 1, (0, 40, 90, 220))


def footer(draw: ImageDraw.ImageDraw, slide: Slide):
    draw.rectangle((38, 1001, 46, 1044), fill=RED)
    fit_text(
        draw,
        (70, 996, 1510, 1042),
        "公開情報をもとにした独自ランキングです。大学の優劣を断定するものではありません。",
        24,
        18,
        (202, 216, 223, 230),
        True,
        "left",
        "center",
    )


def draw_title_block(draw: ImageDraw.ImageDraw, slide: Slide):
    fit_text(draw, (110, 125, 1810, 258), slide.title, 84, 52, WHITE, True, "center", "center", 3, (0, 0, 0, 230))
    neon_line(draw, [(250, 292), (875, 292), (960, 286), (1045, 292), (1670, 292)], BLUE, 2)
    if slide.subtitle:
        fit_text(draw, (210, 312, 1710, 365), slide.subtitle, 36, 24, (238, 244, 246, 245), True, "center", "center", 1, (0, 0, 0, 160))


def draw_body_cards(draw: ImageDraw.ImageDraw, body: list[str], top: int = 405, compact: bool = False):
    card_h = 132 if compact else 145
    gap = 24 if compact else 28
    for i, text in enumerate(body):
        y = top + i * (card_h + gap)
        neon_rounded(draw, (130, y, 1765, y + card_h), 24, (2, 10, 25, 220), BLUE, 3)
        draw.ellipse((174, y + 34, 244, y + 104), fill=GOLD, outline=(255, 247, 180, 255), width=2)
        fit_text(draw, (174, y + 34, 244, y + 104), str(i + 1), 40, 28, (15, 13, 18, 255), True, "center", "center")
        fit_text(draw, (300, y + 24, 1705, y + card_h - 22), text, 39, 25, WHITE, True, "left", "center", 1, (0, 0, 0, 180))


def draw_method_cards(draw: ImageDraw.ImageDraw, body: list[str], x: int, y: int, w: int):
    card_h = 182
    gap = 28
    for i, text in enumerate(body):
        yy = y + i * (card_h + gap)
        neon_rounded(draw, (x, yy, x + w, yy + card_h), 24, (2, 10, 25, 224), BLUE, 3)
        draw.ellipse((x + 44, yy + 54, x + 116, yy + 126), fill=GOLD, outline=(255, 247, 180, 255), width=2)
        fit_text(draw, (x + 44, yy + 54, x + 116, yy + 126), str(i + 1), 40, 28, (15, 13, 18, 255), True, "center", "center")
        fit_text(draw, (x + 155, yy + 28, x + w - 42, yy + card_h - 28), text, 34, 24, WHITE, True, "left", "center", 1, (0, 0, 0, 180))


def draw_weight_chart(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    neon_rounded(draw, (x, y, x + w, y + h), 24, (2, 10, 25, 220), BLUE, 3)
    fit_text(draw, (x + 38, y + 28, x + w - 38, y + 82), "評価配分", 38, 28, (255, 255, 255, 255), True)
    colors = [(255, 218, 82, 255), (91, 231, 239, 255), (255, 91, 123, 255), (190, 166, 255, 255)]
    for i, (label, value) in enumerate(METHOD_WEIGHTS):
        yy = y + 122 + i * 88
        fit_text(draw, (x + 42, yy - 4, x + 410, yy + 48), label, 28, 20, (231, 239, 242, 255), True, "left", "center")
        bar_x1 = x + 420
        bar_x2 = x + w - 150
        draw.rounded_rectangle((bar_x1, yy + 10, bar_x2, yy + 40), 15, fill=(255, 255, 255, 42))
        fill_w = int((bar_x2 - bar_x1) * value / 40)
        draw.rounded_rectangle((bar_x1, yy + 10, bar_x1 + fill_w, yy + 40), 15, fill=colors[i])
        fit_text(draw, (x + w - 130, yy - 2, x + w - 38, yy + 52), f"{value}%", 24, 18, colors[i], True, "right", "center")


def draw_score_chart(draw: ImageDraw.ImageDraw, ranking: list[dict[str, Any]], x: int, y: int, w: int, h: int):
    neon_rounded(draw, (x, y, x + w, y + h), 26, (2, 10, 25, 224), BLUE, 3)
    fit_text(draw, (x + 38, y + 26, x + w - 38, y + 76), "独自評価スコア TOP10", 40, 28, WHITE, True)
    items = sorted(ranking, key=lambda item: item["rank"])
    max_score = 100
    for i, item in enumerate(items):
        yy = y + 105 + i * 52
        label = f"{item['rank']}位 {item['name']}"
        fit_text(draw, (x + 38, yy - 4, x + 330, yy + 34), label, 24, 17, (232, 241, 244, 255), True, "left", "center")
        draw.rounded_rectangle((x + 350, yy + 4, x + w - 110, yy + 30), 13, fill=(255, 255, 255, 38))
        bar_w = int((w - 500) * item["score"] / max_score)
        color = (255, 218, 82, 255) if item["rank"] <= 3 else (91, 231, 239, 245)
        draw.rounded_rectangle((x + 350, yy + 4, x + 350 + bar_w, yy + 30), 13, fill=color)
        fit_text(draw, (x + w - 90, yy - 6, x + w - 38, yy + 38), str(item["score"]), 24, 18, color, True, "right", "center")


def draw_applicant_chart(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    neon_rounded(draw, (x, y, x + w, y + h), 26, (2, 10, 25, 224), BLUE, 3)
    fit_text(draw, (x + 38, y + 26, x + w - 38, y + 78), "志願者数で見える“今選ばれる大学”", 38, 26, WHITE, True)
    max_value = max(value for _, value, _ in APPLICANT_DATA)
    colors = [(255, 218, 82, 255), (91, 231, 239, 255), (255, 91, 123, 255)]
    for i, (name, value, year) in enumerate(APPLICANT_DATA):
        yy = y + 125 + i * 112
        fit_text(draw, (x + 48, yy - 8, x + 330, yy + 42), name, 30, 22, (244, 249, 250, 255), True, "left", "center")
        draw.rounded_rectangle((x + 350, yy + 4, x + w - 360, yy + 50), 23, fill=(255, 255, 255, 38))
        bar_w = int((w - 760) * value / max_value)
        draw.rounded_rectangle((x + 350, yy + 4, x + 350 + bar_w, yy + 50), 23, fill=colors[i])
        fit_text(draw, (x + w - 320, yy - 8, x + w - 44, yy + 60), f"{value:,}人", 30, 20, colors[i], True, "right", "center")
        fit_text(draw, (x + 48, yy + 48, x + 330, yy + 86), year, 21, 16, (196, 211, 219, 230), True, "left", "center")


def draw_rank_gauge(draw: ImageDraw.ImageDraw, item: dict[str, Any], x: int, y: int, w: int):
    neon_rounded(draw, (x, y, x + w, y + 112), 18, (2, 10, 25, 218), BLUE, 2)
    fit_text(draw, (x + 34, y + 20, x + 350, y + 58), "独自変化スコア", 28, 20, (235, 244, 247, 255), True)
    draw.rounded_rectangle((x + 34, y + 72, x + w - 130, y + 96), 12, fill=(255, 255, 255, 42))
    fill_w = int((w - 210) * item["score"] / 100)
    draw.rounded_rectangle((x + 34, y + 72, x + 34 + fill_w, y + 96), 12, fill=(255, 218, 82, 255))
    fit_text(draw, (x + w - 110, y + 48, x + w - 36, y + 100), str(item["score"]), 40, 28, (255, 218, 82, 255), True, "right", "center")


def draw_gold_badge(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str):
    x1, y1, x2, y2 = box
    for expand, alpha, width in [(12, 40, 10), (7, 75, 6), (2, 150, 3)]:
        draw.rounded_rectangle(
            (x1 - expand, y1 - expand, x2 + expand, y2 + expand),
            38 + expand,
            outline=(255, 198, 36, alpha),
            width=width,
        )
    draw.rounded_rectangle(box, 34, fill=(255, 201, 37, 255), outline=(255, 245, 158, 255), width=4)
    draw.rounded_rectangle((x1 + 10, y1 + 9, x2 - 10, y1 + 36), 18, fill=(255, 242, 109, 155))
    draw.rounded_rectangle((x1 + 14, y2 - 18, x2 - 14, y2 - 8), 8, fill=(173, 107, 10, 105))
    fit_text(draw, (x1 + 48, y1 + 18, x2 - 48, y2 - 14), text, 48, 30, (2, 11, 28, 255), True, "center", "center", 1, (255, 255, 255, 115))


def draw_title_point(draw: ImageDraw.ImageDraw, text: str):
    y = 792
    neon_rounded(draw, (95, y, 1825, y + 120), 18, (2, 10, 25, 230), BLUE, 3)
    draw.ellipse((138, y + 26, 206, y + 94), fill=GOLD, outline=(255, 247, 180, 255), width=2)
    fit_text(draw, (138, y + 26, 206, y + 94), "1", 42, 28, (12, 12, 20, 255), True, "center", "center")
    fit_text(draw, (255, y + 24, 1770, y + 98), text, 43, 26, WHITE, True, "left", "center", 1, (0, 0, 0, 190))


def render_slide(slide: Slide, index: int, ranking: list[dict[str, Any]], total_slides: int) -> Path:
    img = make_background(index).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    header(draw, slide, index, total_slides)
    footer(draw, slide)

    if slide.kind == "title":
        fit_text(draw, (105, 190, 1815, 420), slide.title, 96, 68, WHITE, True, "center", "center", 3, (0, 0, 0, 240))
        neon_line(draw, [(245, 462), (820, 462), (960, 455), (1100, 462), (1675, 462)], BLUE, 2)
        fit_text(draw, (210, 485, 1710, 555), slide.subtitle, 42, 28, (238, 244, 246, 245), True, "center", "center", 1, (0, 0, 0, 180))
        if slide.body:
            draw_gold_badge(draw, (430, 612, 1490, 706), slide.body[0])
        if len(slide.body) > 1:
            draw_title_point(draw, slide.body[1])
    elif slide.kind == "method":
        draw_title_block(draw, slide)
        draw_method_cards(draw, slide.body[:2], 120, 420, 820)
        draw_weight_chart(draw, 1015, 400, 790, 485)
    elif slide.kind == "score_chart":
        draw_title_block(draw, slide)
        draw_score_chart(draw, ranking, 190, 380, 1540, 565)
    elif slide.kind == "applicant_chart":
        draw_title_block(draw, slide)
        draw_applicant_chart(draw, 210, 390, 1500, 455)
        neon_rounded(draw, (210, 875, 1710, 936), 18, (2, 10, 25, 220), BLUE, 2)
        fit_text(draw, (260, 884, 1660, 926), slide.body[0], 30, 20, WHITE, True, "center", "center")
    elif slide.kind == "rank_full":
        item = slide.data or {}
        rounded(draw, (92, 145, 325, 238), 16, (217, 48, 76, 245), (255, 172, 185, 120), 2)
        fit_text(draw, (115, 160, 302, 224), f"第{item['rank']}位", 44, 30, (255, 255, 255, 255), True, "center", "center")
        fit_text(draw, (380, 148, 1290, 235), item["name"], 78, 48, WHITE, True, "left", "center", 3, (0, 0, 0, 220))
        neon_rounded(draw, (1325, 157, 1808, 220), 18, (2, 15, 35, 220), BLUE, 2)
        fit_text(draw, (1350, 169, 1785, 209), item["tag"], 30, 20, CYAN, True, "center", "center")
        draw_rank_gauge(draw, item, 110, 270, 720)

        for x, label, text, color in [
            (110, "親世代の印象", item["old"], (7, 15, 29, 204)),
            (1010, "いまの評価", item["now"], (14, 62, 76, 204)),
        ]:
            neon_rounded(draw, (x, 405, x + 800, 558), 18, color, BLUE, 2)
            fit_text(draw, (x + 38, 426, x + 744, 470), label, 29, 22, (255, 225, 92, 255), True)
            fit_text(draw, (x + 38, 486, x + 744, 535), text, 36, 24, WHITE, True, "left", "center", 1, (0, 0, 0, 150))

        notes = slide.body[2:]
        for i, note in enumerate(notes):
            y = 595 + i * 78
            neon_rounded(draw, (165, y, 1755, y + 66), 15, (2, 10, 25, 212), BLUE, 2)
            draw.ellipse((200, y + 17, 232, y + 49), fill=(255, 218, 82, 255))
            fit_text(draw, (250, y + 10, 1715, y + 56), note, 30, 19, WHITE, True, "left", "center", 1, (0, 0, 0, 160))

        rounded(draw, (165, 842, 1755, 912), 14, (0, 0, 0, 185), (255, 255, 255, 80), 1)
        fit_text(draw, (205, 856, 1715, 900), f"根拠: {slide.source}", 27, 18, (218, 232, 237, 255), True, "left", "center")
    elif slide.kind == "rank_overview":
        item = slide.data or {}
        rounded(draw, (92, 145, 325, 238), 26, (217, 48, 76, 245), (255, 172, 185, 120), 2)
        fit_text(draw, (115, 160, 302, 224), f"第{item['rank']}位", 44, 30, (255, 255, 255, 255), True, "center", "center")
        fit_text(draw, (380, 148, 1290, 235), item["name"], 76, 48, (255, 255, 255, 255), True, "left", "center", 2, (0, 0, 0, 180))
        rounded(draw, (1325, 157, 1808, 220), 30, (7, 21, 39, 226), (255, 255, 255, 40), 1)
        fit_text(draw, (1350, 169, 1785, 209), item["tag"], 27, 18, (91, 231, 239, 255), True, "center", "center")
        draw_rank_gauge(draw, item, 110, 285, 760)

        for x, label, text, color in [
            (110, "親世代の印象", item["old"], (7, 15, 29, 204)),
            (1010, "いまの評価", item["now"], (14, 62, 76, 204)),
        ]:
            rounded(draw, (x, 435, x + 800, 655), 28, color, (255, 255, 255, 42), 1)
            fit_text(draw, (x + 44, 460, x + 744, 510), label, 32, 24, (255, 225, 92, 255), True)
            fit_text(draw, (x + 44, 530, x + 744, 620), text, 44, 30, (255, 255, 255, 255), True, "left", "center")
        draw_body_cards(draw, slide.body, top=720, compact=True)
    elif slide.kind == "rank_evidence":
        item = slide.data or {}
        fit_text(draw, (120, 150, 1680, 230), f"{item['name']}：評価が変わった理由", 62, 40, (255, 255, 255, 255), True, "left", "center", 2, (0, 0, 0, 175))
        rounded(draw, (120, 265, 1800, 780), 30, (5, 13, 27, 174), (255, 255, 255, 38), 1)
        fit_text(draw, (165, 302, 1745, 455), "\n".join(slide.body[:2]), 38, 28, (248, 252, 253, 255), True, "left", "center")
        rounded(draw, (165, 500, 1745, 632), 22, (12, 64, 78, 190), (255, 255, 255, 35), 1)
        fit_text(draw, (205, 524, 1705, 608), slide.body[2], 34, 24, (255, 247, 206, 255), True, "left", "center")
        rounded(draw, (165, 665, 1745, 735), 18, (0, 0, 0, 120), (255, 255, 255, 28), 1)
        fit_text(draw, (205, 678, 1705, 722), f"根拠: {slide.source}", 26, 18, (200, 221, 229, 255), True, "left", "center")
        draw_rank_gauge(draw, item, 640, 815, 650)
    elif slide.kind == "final":
        draw_title_block(draw, slide)
        draw_body_cards(draw, slide.body, top=400, compact=False)
    else:
        draw_title_block(draw, slide)
        draw_body_cards(draw, slide.body, top=400, compact=False)

    out = OUT_DIR / f"{index:02d}_{slide.slug}.png"
    img.convert("RGB").save(out, quality=96)
    return out


def build_slides(ranking: list[dict[str, Any]]) -> list[Slide]:
    ranking_desc = sorted(ranking, key=lambda item: item["rank"], reverse=True)
    slides = [
        Slide(
            "title",
            15,
            "親世代と評価が変わった\n大学ランキング TOP10",
            "偏差値だけでは見えない、いま選ばれる大学の変化を見る",
            [
                TITLE_BADGE_TEXT,
                TITLE_POINT_TEXT,
            ],
            "title",
        ),
        Slide(
            "premise",
            30,
            "親世代のイメージと、いまの評価は違う",
            "校名・昔の偏差値・卒業生の印象だけでは、現在の大学価値は見えにくい",
            [
                "親世代の評価は、昔の知名度や校名イメージに引っ張られやすいです。",
                "いまの評価は、志願者数、就職実績、学部改革、社会ニーズとの接続で変わります。",
                "このランキングでは、親世代の印象からどれだけ評価が更新されたかを見ます。",
            ],
            "final",
        ),
        Slide(
            "method",
            30,
            "評価軸は4つ",
            "人気・就職・改革・印象差を、公開情報ベースで独自集計",
            [
                "志願者数は、いま受験生に選ばれているかを見る指標です。",
                "就職実績と学部改革は、企業や社会からの評価につながる指標です。",
            ],
            "method",
        ),
        Slide(
            "score_chart",
            30,
            "全体像：独自評価スコア",
            "上位ほど、親世代の印象から現在の評価への変化が大きい",
            [],
            "score_chart",
        ),
        Slide(
            "applicant_chart",
            30,
            "根拠グラフ：志願者数で見る変化",
            "一部の大学は、受験生からの選ばれ方が数字ではっきり見える",
            [
                "近畿大学、千葉工業大学、東洋大学は、志願者数という見えやすい数字で評価の変化を示しています。",
            ],
            "applicant_chart",
        ),
    ]

    for item in ranking_desc:
        notes = EXPANDED_NOTES[item["name"]]
        slides.append(
            Slide(
                f"rank_{item['rank']:02d}",
                27,
                f"第{item['rank']}位 {item['name']}",
                item["tag"],
                [
                    f"親世代の印象: {item['old']}",
                    f"いまの評価: {item['now']}",
                    *notes,
                ],
                "rank_full",
                data=item,
                source=SOURCE_BY_NAME[item["name"]],
            )
        )

    slides.extend(
        [
            Slide(
                "common_patterns",
                30,
                "評価が変わる大学の共通点",
                "昔の知名度ではなく、いまの社会に合う学びを作れている",
                [
                    "AI、データ、半導体、都市、環境など、社会ニーズに直結する領域を伸ばしています。",
                    "就職実績、志願者数、外部ランキングなど、変化を数字で示せる大学が強いです。",
                    "親世代の校名イメージを超えるだけの、具体的な改革ストーリーがあります。",
                ],
                "final",
            ),
            Slide(
                "update_view",
                30,
                "親世代の見方をアップデートする",
                "大学名だけでなく、伸びている理由を見る",
                [
                    "大学選びでは、昔の偏差値序列だけでなく、いまの学部構成と就職の強さを見るべきです。",
                    "特に理工系、情報系、実学系は、社会の変化によって評価が動きやすい領域です。",
                    "親世代の安心感と、現代の実力評価を分けて考えることが大切です。",
                ],
                "final",
            ),
            Slide(
                "closing",
                15,
                "結論：大学選びは“今の理由”を見る時代へ",
                "名前の印象より、伸びている根拠を確認する",
                [
                    "このランキングは、大学の優劣ではなく、評価の変化を可視化するためのものです。",
                    "親世代の安心感と、いまの実力評価を分けて見ることが大切です。",
                ],
                "final",
            ),
        ]
    )
    assert sum(slide.duration for slide in slides) == TARGET_SECONDS
    assert len(slides) == 18
    return slides


def duration(path: Path) -> float:
    res = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(res.stdout.strip())


def main():
    DIST.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)
    ranking = json.loads((DIST / "ranking.json").read_text(encoding="utf-8"))
    slides = build_slides(ranking)

    rendered = [render_slide(slide, i, ranking, len(slides)) for i, slide in enumerate(slides)]

    concat = OUT_DIR / "concat_slides.txt"
    with concat.open("w", encoding="utf-8") as f:
        for slide, path in zip(slides, rendered):
            f.write(f"file '{path.resolve().as_posix()}'\n")
            f.write(f"duration {slide.duration}\n")
        f.write(f"file '{rendered[-1].resolve().as_posix()}'\n")

    video = DIST / f"oyasedai_hyouka_daigaku_{TARGET_LABEL}_slides_no_voice.mp4"
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-vf",
            "fps=24,format=yuv420p",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(video),
        ],
        check=True,
    )

    manifest = []
    cursor = 0
    script_lines = [
        f"親世代と評価が変わった大学ランキング TOP10 {TARGET_TITLE}",
        "音声化ルール: 各スライドの visible_text を必ず読む。補足を入れる場合も、この文章を省略しない。",
        "",
    ]
    for i, slide in enumerate(slides):
        start = cursor
        end = cursor + slide.duration
        cursor = end
        manifest.append(
            {
                "index": i,
                "slug": slide.slug,
                "duration": slide.duration,
                "start": start,
                "end": end,
                "image": str(rendered[i]),
                "visible_text": slide.visible_text,
            }
        )
        script_lines.append(f"## Slide {i + 1:02d} / {slide.duration}秒 / {start:03d}-{end:03d}秒")
        script_lines.extend(slide.visible_text)
        script_lines.append("")

    manifest_path = DIST / f"slides_{TARGET_LABEL}_no_voice_manifest.json"
    script_path = DIST / f"narration_script_{TARGET_LABEL}_slide_text.txt"
    manifest_path.write_text(
        json.dumps(
            {
                "duration_seconds": cursor,
                "slide_count": len(slides),
                "video": str(video),
                "slides": manifest,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    script_path.write_text("\n".join(script_lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "video": str(video),
                "duration_seconds": round(duration(video), 3),
                "slides": len(slides),
                "manifest": str(manifest_path),
                "script": str(script_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
