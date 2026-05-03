from __future__ import annotations

import json
import math
import os
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build_rich"
ASSETS = ROOT / "assets"
REF = ASSETS / "ref_engineering_ranking_maxres.jpg"
W, H = 1920, 1080
FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FFMPEG = "/opt/anaconda3/bin/ffmpeg"
FFPROBE = "/opt/anaconda3/bin/ffprobe"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def draw_text(draw, xy, s, size, fill, bold=True, anchor=None, stroke=0, stroke_fill=(0, 0, 0), spacing=8, align="left"):
    draw.multiline_text(
        xy,
        s,
        font=font(size, bold),
        fill=fill,
        anchor=anchor,
        stroke_width=stroke,
        stroke_fill=stroke_fill,
        spacing=spacing,
        align=align,
    )


def wrap_jp(text: str, max_chars: int):
    out, buf = [], ""
    for ch in text:
        buf += ch
        if len(buf) >= max_chars:
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return "\n".join(out)


def rich_bg(seed=0, blur_ref=True):
    if REF.exists() and blur_ref:
        src = Image.open(REF).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
        bg = src.filter(ImageFilter.GaussianBlur(30))
        bg = ImageEnhance.Color(bg).enhance(1.12)
        bg = ImageEnhance.Contrast(bg).enhance(1.12)
        wash_l = Image.new("RGB", (W, H), (18, 9, 42))
        wash_r = Image.new("RGB", (W, H), (0, 66, 78))
        mask = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mask)
        for x in range(W):
            md.line((x, 0, x, H), fill=int(255 * x / W))
        wash = Image.composite(wash_r, wash_l, mask)
        bg = Image.blend(bg, wash, 0.42)
        bg = ImageEnhance.Brightness(bg).enhance(0.78)
        img = bg.convert("RGBA")
    else:
        img = Image.new("RGBA", (W, H), (6, 10, 18, 255))
        pix = img.load()
        for y in range(H):
            for x in range(W):
                nx, ny = x / W, y / H
                c = max(0, 1 - math.hypot(nx - 0.48, ny - 0.33) * 1.6)
                r = max(0, 1 - math.hypot(nx - 0.92, ny - 0.60) * 2.0)
                pix[x, y] = (int(7 + 30 * c + 6 * r), int(10 + 28 * c + 68 * r), int(18 + 72 * c + 80 * r), 255)

    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, 132), fill=(0, 0, 0, 82))
    d.rectangle((0, H - 128, W, H), fill=(0, 0, 0, 118))
    for x in range(-100, W + 180, 140):
        d.line((x, 0, x + 190, H), fill=(255, 255, 255, 8), width=1)
    for y in range(170, H - 120, 80):
        d.line((0, y, W, y + 16), fill=(255, 255, 255, 6), width=1)
    random.seed(seed)
    for _ in range(1700):
        x, y = random.randrange(W), random.randrange(H)
        d.point((x, y), fill=(255, 255, 255, random.randrange(3, 9)))

    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    for i in range(0, 420, 3):
        vd.rectangle((i, i, W - i, H - i), outline=int(255 * i / 420), width=3)
    vignette = ImageOps.invert(vignette).filter(ImageFilter.GaussianBlur(42))
    img = Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, vignette.point(lambda p: int(p * 0.26)))
    return img


def badge(draw, text="決定版", xy=(58, 50), fill=(214, 50, 74, 255)):
    x, y = xy
    draw.rounded_rectangle((x, y, x + 205, y + 80), 14, fill=fill, outline=(255, 145, 164, 95), width=2)
    draw_text(draw, (x + 102, y + 20), text, 39, (255, 255, 255), True, anchor="ma")


def pill(draw, text="VALUE SHIFT", xy=(1530, 56), w=300):
    x, y = xy
    draw.rounded_rectangle((x, y, x + w, y + 60), 30, fill=(8, 20, 42, 228), outline=(255, 255, 255, 28), width=1)
    draw_text(draw, (x + w / 2, y + 15), text, 28, (93, 226, 238), True, anchor="ma")


def bottom_band(draw, s):
    y = H - 112
    for x in range(W):
        t = x / W
        col = (int(14 * (1 - t) + 23 * t), int(52 * (1 - t) + 118 * t), int(105 * (1 - t) + 130 * t), 232)
        draw.line((x, y, x, H), fill=col)
    draw.line((0, y - 4, W, y - 4), fill=(0, 0, 0, 135), width=5)
    draw.line((0, y, W, y), fill=(255, 255, 255, 55), width=1)
    draw_text(draw, (W / 2, y + 28), s, 45, (255, 225, 92), True, anchor="ma", stroke=2, stroke_fill=(0, 0, 0), align="center")


def title_slide(path: Path):
    img = rich_bg(1)
    d = ImageDraw.Draw(img, "RGBA")
    badge(d)
    pill(d, "独自ランキング", (1530, 58), 310)
    draw_text(d, (W / 2, 146), "V A L U E   S H I F T", 48, (238, 236, 248, 230), True, anchor="ma")
    draw_text(d, (W / 2 + 8, 384), "親世代と評価が変わった\n大学ランキング", 106, (0, 0, 0, 155), True, anchor="ma", stroke=3, stroke_fill=(0, 0, 0), spacing=8, align="center")
    draw_text(d, (W / 2, 374), "親世代と評価が変わった\n大学ランキング", 106, (252, 252, 255), True, anchor="ma", stroke=1, stroke_fill=(30, 24, 42), spacing=8, align="center")
    draw_text(d, (W / 2 + 8, 690), "2026", 188, (0, 0, 0, 120), True, anchor="ma", stroke=2, stroke_fill=(0, 0, 0))
    draw_text(d, (W / 2, 680), "2026", 188, (255, 218, 78), True, anchor="ma", stroke=2, stroke_fill=(74, 43, 3))
    bottom_band(d, "志願者数・就職・学部改革データ完全集計")
    img.convert("RGB").save(path, quality=95)


def method_slide(path: Path):
    img = rich_bg(2)
    d = ImageDraw.Draw(img, "RGBA")
    badge(d, "評価軸")
    pill(d, "DATA ALCHEMIST", (1485, 58), 350)
    draw_text(d, (120, 185), "偏差値だけでは見えない\n“評価の変化”を見る", 82, (252, 252, 255), True, stroke=2, stroke_fill=(0, 0, 0), spacing=12)
    axes = [
        ("志願者数", "いま受験生に選ばれているか"),
        ("就職実績", "企業から評価されているか"),
        ("学部改革", "AI・データ・実学に対応しているか"),
        ("印象差", "親世代のイメージからどれだけ変わったか"),
    ]
    x0, y0 = 1020, 188
    for i, (a, b) in enumerate(axes):
        y = y0 + i * 150
        d.rounded_rectangle((x0, y, 1800, y + 110), 22, fill=(7, 15, 27, 180), outline=(255, 255, 255, 35), width=1)
        d.ellipse((x0 + 32, y + 28, x0 + 84, y + 80), fill=(255, 218, 78))
        draw_text(d, (x0 + 58, y + 38), str(i + 1), 27, (9, 15, 25), True, anchor="ma")
        draw_text(d, (x0 + 112, y + 20), a, 42, (255, 255, 255), True)
        draw_text(d, (x0 + 112, y + 70), b, 28, (210, 222, 229), True)
    bottom_band(d, "公開情報をもとにした独自ランキングです")
    img.convert("RGB").save(path, quality=95)


def rank_slide(path: Path, item: dict, top=False):
    img = rich_bg(item["rank"] + 3)
    d = ImageDraw.Draw(img, "RGBA")
    badge(d, f"第{item['rank']}位")
    pill(d, item["tag"], (1390, 58), 445)
    name_size = 88 if len(item["name"]) <= 6 else 78
    draw_text(d, (112, 188), item["name"], name_size, (255, 255, 255), True, stroke=2, stroke_fill=(0, 0, 0))
    draw_text(d, (112, 286), f"変化スコア {item['score']}", 38, (255, 225, 92), True, stroke=1, stroke_fill=(0, 0, 0))

    # Score bar.
    bx, by, bw, bh = 112, 354, 640, 30
    d.rounded_rectangle((bx, by, bx + bw, by + bh), 15, fill=(255, 255, 255, 30))
    d.rounded_rectangle((bx, by, bx + int(bw * item["score"] / 100), by + bh), 15, fill=(255, 218, 78))

    # Comparison cards.
    card_y = 438
    d.rounded_rectangle((110, card_y, 880, card_y + 230), 26, fill=(7, 15, 27, 190), outline=(255, 255, 255, 35), width=1)
    d.rounded_rectangle((1040, card_y, 1810, card_y + 230), 26, fill=(14, 59, 72, 190), outline=(255, 218, 78, 70), width=1)
    draw_text(d, (150, card_y + 32), "親世代の印象", 36, (154, 180, 196), True)
    draw_text(d, (1080, card_y + 32), "いまの評価", 36, (255, 225, 92), True)
    draw_text(d, (150, card_y + 100), wrap_jp(item["old"], 18), 46, (255, 255, 255), True, spacing=8)
    draw_text(d, (1080, card_y + 100), wrap_jp(item["now"], 18), 46, (255, 255, 255), True, spacing=8)

    # Reason.
    d.rounded_rectangle((110, 728, 1810, 870), 24, fill=(0, 0, 0, 105), outline=(255, 255, 255, 22), width=1)
    draw_text(d, (150, 758), wrap_jp(item["reason"], 44), 38, (238, 244, 242), True, spacing=8)
    bottom_band(d, "親世代のイメージから、いまの実力へ")
    img.convert("RGB").save(path, quality=95)


def final_slide(path: Path):
    img = rich_bg(31)
    d = ImageDraw.Draw(img, "RGBA")
    badge(d, "結論")
    pill(d, "VALUE SHIFT", (1530, 58), 310)
    draw_text(d, (W / 2, 205), "評価が変わる大学の共通点", 76, (255, 255, 255), True, anchor="ma", stroke=2, stroke_fill=(0, 0, 0))
    bullets = ["時代に合う学部を作る", "就職実績を数字で示せる", "昔の校名イメージを超える強みがある"]
    y = 360
    for b in bullets:
        d.rounded_rectangle((340, y, 1580, y + 92), 24, fill=(7, 15, 27, 180), outline=(255, 255, 255, 34), width=1)
        d.ellipse((382, y + 23, 428, y + 69), fill=(255, 218, 78))
        draw_text(d, (470, y + 22), b, 43, (255, 255, 255), True)
        y += 128
    bottom_band(d, "大学選びは、名前の印象より“伸びている理由”を見る時代へ")
    img.convert("RGB").save(path, quality=95)


def say_audio(text: str, out: Path):
    subprocess.run(["say", "-v", "Kyoko", "-r", "184", "-o", str(out), text], check=True)


def duration(path: Path) -> float:
    res = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(res.stdout.strip())


def make_part(idx: int, slide: Path, audio: Path, out: Path):
    dur = duration(audio) + 0.35
    zoom = "zoompan=z='min(zoom+0.00055,1.045)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30"
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-loop",
            "1",
            "-framerate",
            "30",
            "-i",
            str(slide),
            "-i",
            str(audio),
            "-t",
            f"{dur:.2f}",
            "-vf",
            f"{zoom},format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(out),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    BUILD.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    ranking = json.loads((DIST / "ranking.json").read_text(encoding="utf-8"))
    ranking = sorted(ranking, key=lambda x: x["rank"], reverse=True)

    slides = []
    p = BUILD / "rich_00_title.jpg"
    title_slide(p)
    slides.append((p, "親世代が知っている大学の評価と、いま受験生が見ている大学の評価は、かなり変わっています。今回は、評価が変わった大学ランキングを見ていきます。"))

    p = BUILD / "rich_01_method.jpg"
    method_slide(p)
    slides.append((p, "このランキングは、偏差値だけではありません。志願者数、就職実績、学部改革、そして親世代のイメージからの変化幅をもとにした、独自ランキングです。"))

    for idx, item in enumerate(ranking, start=2):
        p = BUILD / f"rich_{idx:02d}_rank_{item['rank']:02d}.jpg"
        rank_slide(p, item, top=item["rank"] <= 3)
        narration = f"第{item['rank']}位、{item['name']}。親世代の印象は、{item['old']}。しかし今は、{item['now']}。{item['reason']}"
        slides.append((p, narration))

    p = BUILD / "rich_99_final.jpg"
    final_slide(p)
    slides.append((p, "ランキング上位に共通するのは、昔の知名度ではなく、今の社会が求める学びを早く形にしていることです。大学選びでは、名前のイメージだけでなく、いま伸びている理由を見ることが大切です。"))

    parts = []
    for idx, (slide, narration) in enumerate(slides):
        audio = BUILD / f"rich_audio_{idx:02d}.aiff"
        part = BUILD / f"rich_part_{idx:02d}.mp4"
        say_audio(narration, audio)
        make_part(idx, slide, audio, part)
        parts.append(part)

    concat = BUILD / "rich_concat.txt"
    concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    out = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking_rich.mp4"
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(out)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Also replace the generic main video.
    main_out = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking.mp4"
    main_out.write_bytes(out.read_bytes())
    print(out)


if __name__ == "__main__":
    main()
