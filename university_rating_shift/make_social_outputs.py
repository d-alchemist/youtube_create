from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
OUT_DIR = DIST / "social"

FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"

WHITE = (252, 252, 252, 255)
CYAN = (76, 229, 255, 255)
BLUE = (35, 170, 255, 255)
GOLD = (255, 218, 58, 255)
RED = (235, 31, 48, 255)
BLACK = (2, 9, 24, 255)

YOUTUBE_URL_PLACEHOLDER = "{YOUTUBE_URL}"


THREADS_POST = f"""親世代の大学イメージ、かなり更新されてます。

昔の知名度や校名イメージだけでは、
いま選ばれている大学は見えにくいです。

志願者数・就職実績・学部改革で見ると、
評価が大きく変わっている大学があります。

TOP10をYouTubeで詳しく解説しました👇
{YOUTUBE_URL_PLACEHOLDER}

#大学受験 #大学ランキング #データの錬金術師"""


X_POST = f"""親世代の大学イメージ、もう古いかもしれません。

志願者数・就職実績・学部改革で見ると、評価が大きく変わった大学があります。

「親世代と評価が変わった大学TOP10」を公開しました👇
{YOUTUBE_URL_PLACEHOLDER}

#大学受験 #大学ランキング"""


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_size(draw: ImageDraw.ImageDraw, lines: list[str], fnt: ImageFont.FreeTypeFont, spacing: int) -> tuple[int, int]:
    widths = []
    heights = []
    for line in lines:
        box = draw.textbbox((0, 0), line, font=fnt)
        widths.append(box[2] - box[0])
        heights.append(box[3] - box[1])
    return max(widths) if widths else 0, sum(heights) + spacing * max(0, len(lines) - 1)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
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
    fill,
    bold: bool = True,
    align: str = "center",
    stroke: int = 0,
):
    x1, y1, x2, y2 = box
    max_w = x2 - x1
    max_h = y2 - y1
    selected = None
    for size in range(max_size, min_size - 1, -2):
        fnt = font(size, bold)
        spacing = max(6, int(size * 0.18))
        lines = wrap_text(draw, text, fnt, max_w)
        width, height = text_size(draw, lines, fnt, spacing)
        if width <= max_w and height <= max_h:
            selected = fnt, spacing, lines, height
            break
    if selected is None:
        raise RuntimeError(f"Text overflow: {text}")
    fnt, spacing, lines, height = selected
    x = x1 + max_w / 2 if align == "center" else x1
    y = y1 + (max_h - height) / 2
    anchor = "ma" if align == "center" else "la"
    draw.multiline_text(
        (x, y),
        "\n".join(lines),
        font=fnt,
        fill=fill,
        anchor=anchor,
        spacing=spacing,
        align=align,
        stroke_width=stroke,
        stroke_fill=(0, 0, 0, 220),
    )


def neon_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int = 28):
    x1, y1, x2, y2 = box
    for expand, alpha, width in [(12, 35, 10), (7, 70, 6), (2, 140, 3)]:
        draw.rounded_rectangle(
            (x1 - expand, y1 - expand, x2 + expand, y2 + expand),
            radius + expand,
            outline=(BLUE[0], BLUE[1], BLUE[2], alpha),
            width=width,
        )
    draw.rounded_rectangle(box, radius, fill=(0, 8, 24, 232), outline=BLUE, width=3)


def gold_badge(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, 30, fill=(255, 203, 35, 255), outline=(255, 245, 160, 255), width=4)
    draw.rounded_rectangle((x1 + 12, y1 + 10, x2 - 12, y1 + 38), 16, fill=(255, 245, 105, 145))
    fit_text(draw, (x1 + 32, y1 + 12, x2 - 32, y2 - 8), text, 58, 30, (3, 11, 28, 255), True, "center", 1)


def background(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BLACK)
    draw = ImageDraw.Draw(img, "RGBA")
    for y in range(h):
        ratio = y / max(1, h - 1)
        color = (
            int(3 + 10 * ratio),
            int(8 + 14 * ratio),
            int(28 + 38 * ratio),
            255,
        )
        draw.line((0, y, w, y), fill=color)

    for i in range(0, w + 260, 92):
        draw.line((i, int(h * 0.62), i - 340, h), fill=(0, 108, 255, 120), width=2)
    for i in range(0, 10):
        y = int(h * 0.62 + i * h * 0.038)
        draw.line((0, y, w, y), fill=(0, 120, 255, 95), width=1)

    draw.polygon([(0, 0), (230, 0), (315, 78), (0, 78)], fill=(85, 0, 13, 235), outline=RED)
    draw.line((0, 94, 150, 0), fill=RED, width=7)
    draw.line((0, 132, 210, 0), fill=(255, 40, 62, 210), width=5)
    draw.line((0, 170, 270, 0), fill=(255, 40, 62, 160), width=4)

    for x, y in [(80, 660), (190, 540), (790, 165), (930, 238), (1020, 590)]:
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(40, 150, 255, 190))
    return img


def draw_brand(draw: ImageDraw.ImageDraw, w: int):
    poly = [(w - 430, 34), (w - 44, 34), (w - 18, 74), (w - 44, 114), (w - 430, 114), (w - 464, 74)]
    draw.polygon(poly, fill=(2, 12, 28, 230), outline=BLUE)
    fit_text(draw, (w - 410, 46, w - 62, 100), "DATA ALCHEMIST", 32, 20, CYAN, True, "center", 0)


def make_threads_card(out: Path):
    img = background((1080, 1350))
    draw = ImageDraw.Draw(img, "RGBA")
    draw_brand(draw, 1080)
    fit_text(draw, (70, 185, 1010, 420), "親世代の大学イメージ\n今、かなり変わってます", 74, 46, WHITE, True, "center", 3)
    gold_badge(draw, (100, 500, 980, 610), "評価が変わった大学 TOP10")
    neon_panel(draw, (88, 710, 992, 910), 26)
    fit_text(draw, (140, 748, 940, 872), "志願者数・就職・学部改革で見る\n“いま選ばれる大学”", 46, 30, WHITE, True, "center", 2)
    fit_text(draw, (90, 1030, 990, 1116), "YouTubeで詳しく解説", 46, 30, CYAN, True, "center", 1)
    fit_text(draw, (90, 1148, 990, 1230), "1位はかなり意外かもしれません", 40, 28, GOLD, True, "center", 1)
    fit_text(draw, (74, 1282, 1006, 1325), "公開情報をもとにした独自ランキングです", 24, 18, (235, 242, 246, 235), True, "center", 0)
    img.convert("RGB").save(out, quality=96)


def make_x_card(out: Path):
    base_path = DIST / "thumbnail_final_D.png"
    if base_path.exists():
        img = Image.open(base_path).convert("RGBA").resize((1600, 900), Image.Resampling.LANCZOS)
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay, "RGBA")
        od.rectangle((0, 0, 1600, 900), fill=(0, 0, 0, 46))
        img = Image.alpha_composite(img, overlay)
    else:
        img = background((1600, 900))
    draw = ImageDraw.Draw(img, "RGBA")
    neon_panel(draw, (94, 620, 1506, 790), 24)
    fit_text(draw, (150, 642, 1450, 710), "親世代の大学イメージ、もう古いかもしれません", 50, 32, WHITE, True, "center", 2)
    fit_text(draw, (150, 724, 1450, 772), "YouTubeでTOP10を解説", 30, 22, CYAN, True, "center", 0)
    img.convert("RGB").save(out, quality=95)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    threads_txt = OUT_DIR / "threads_post.txt"
    x_txt = OUT_DIR / "x_post.txt"
    threads_img = OUT_DIR / "threads_card_1080x1350.jpg"
    x_img = OUT_DIR / "x_card_1600x900.jpg"

    threads_txt.write_text(THREADS_POST + "\n", encoding="utf-8")
    x_txt.write_text(X_POST + "\n", encoding="utf-8")
    make_threads_card(threads_img)
    make_x_card(x_img)

    meta = {
        "youtube_url_placeholder": YOUTUBE_URL_PLACEHOLDER,
        "threads": {
            "post": str(threads_txt),
            "image": str(threads_img),
            "image_size": "1080x1350",
        },
        "x": {
            "post": str(x_txt),
            "image": str(x_img),
            "image_size": "1600x900",
        },
    }
    (OUT_DIR / "social_outputs.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
