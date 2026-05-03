from __future__ import annotations

import json
import math
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from moviepy.editor import VideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build_motion"
ASSETS = ROOT / "assets"
REF = ASSETS / "ref_engineering_ranking_maxres.jpg"
W, H = 1920, 1080
FPS = 24
FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FFMPEG = "/opt/anaconda3/bin/ffmpeg"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def fade_in(t: float, start: float, dur: float = 0.45) -> int:
    return int(255 * ease((t - start) / dur))


def slide_y(base: float, t: float, start: float, offset: float = 26, dur: float = 0.45) -> float:
    return base + offset * (1 - ease((t - start) / dur))


def fit_lines(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int):
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


def multiline_size(draw: ImageDraw.ImageDraw, lines, fnt, spacing):
    if not lines:
        return 0, 0
    widths = [draw.textbbox((0, 0), line, font=fnt)[2] for line in lines]
    heights = [draw.textbbox((0, 0), line, font=fnt)[3] - draw.textbbox((0, 0), line, font=fnt)[1] for line in lines]
    return max(widths), sum(heights) + spacing * (len(lines) - 1)


def draw_fit(
    draw: ImageDraw.ImageDraw,
    box,
    text: str,
    max_size: int,
    min_size: int,
    fill,
    bold: bool = True,
    align: str = "left",
    valign: str = "top",
    stroke: int = 0,
    stroke_fill=(0, 0, 0),
    spacing_ratio: float = 0.18,
):
    x1, y1, x2, y2 = box
    max_w, max_h = int(x2 - x1), int(y2 - y1)
    chosen = None
    for size in range(max_size, min_size - 1, -2):
        fnt = font(size, bold)
        spacing = max(4, int(size * spacing_ratio))
        lines = fit_lines(draw, text, fnt, max_w)
        w, h = multiline_size(draw, lines, fnt, spacing)
        if w <= max_w and h <= max_h:
            chosen = size, fnt, spacing, lines, w, h
            break
    if chosen is None:
        size = min_size
        fnt = font(size, bold)
        spacing = max(3, int(size * spacing_ratio))
        lines = fit_lines(draw, text, fnt, max_w)
        while True:
            w, h = multiline_size(draw, lines, fnt, spacing)
            if h <= max_h or len(lines) <= 1:
                break
            lines[-2] += "…"
            lines = lines[:-1]
        chosen = size, fnt, spacing, lines, w, h
    _, fnt, spacing, lines, w, h = chosen
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
        y = y1 + (max_h - h) / 2
    elif valign == "bottom":
        y = y2 - h
    else:
        y = y1
    draw.multiline_text((x, y), "\n".join(lines), font=fnt, fill=fill, anchor=anchor, spacing=spacing, align=align, stroke_width=stroke, stroke_fill=stroke_fill)


def make_bg(seed=0):
    if REF.exists():
        src = Image.open(REF).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
        bg = src.filter(ImageFilter.GaussianBlur(34))
        bg = ImageEnhance.Color(bg).enhance(1.08)
        bg = ImageEnhance.Contrast(bg).enhance(1.1)
        left = Image.new("RGB", (W, H), (42, 12, 55))
        right = Image.new("RGB", (W, H), (0, 70, 82))
        mask = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mask)
        for x in range(W):
            md.line((x, 0, x, H), fill=int(255 * x / W))
        wash = Image.composite(right, left, mask)
        bg = Image.blend(bg, wash, 0.42)
        bg = ImageEnhance.Brightness(bg).enhance(0.76)
        img = bg.convert("RGBA")
    else:
        img = Image.new("RGBA", (W, H), (8, 10, 18, 255))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, 132), fill=(0, 0, 0, 92))
    d.rectangle((0, H - 126, W, H), fill=(0, 0, 0, 125))
    for x in range(-120, W + 160, 150):
        d.line((x, 0, x + 185, H), fill=(255, 255, 255, 9), width=1)
    for y in range(180, H - 140, 90):
        d.line((0, y, W, y + 18), fill=(255, 255, 255, 6), width=1)
    random.seed(seed)
    for _ in range(1150):
        d.point((random.randrange(W), random.randrange(H)), fill=(255, 255, 255, random.randrange(2, 8)))
    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    for i in range(0, 420, 4):
        vd.rectangle((i, i, W - i, H - i), outline=int(255 * i / 420), width=4)
    vignette = ImageOps.invert(vignette).filter(ImageFilter.GaussianBlur(48))
    return Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, vignette.point(lambda p: int(p * 0.22)))


def overlay_alpha(base: Image.Image, overlay: Image.Image, alpha: int):
    if alpha <= 0:
        return
    if alpha < 255:
        overlay = overlay.copy()
        a = overlay.getchannel("A").point(lambda p: p * alpha // 255)
        overlay.putalpha(a)
    base.alpha_composite(overlay)


def paste_alpha(base: Image.Image, overlay: Image.Image, xy, alpha: int = 255):
    if alpha <= 0:
        return
    if alpha < 255:
        overlay = overlay.copy()
        a = overlay.getchannel("A").point(lambda p: p * alpha // 255)
        overlay.putalpha(a)
    base.alpha_composite(overlay, xy)


def rounded(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def badge_layer(text: str, width=230, height=86):
    layer = Image.new("RGBA", (width + 22, height + 22), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    rounded(d, (8, 8, width + 8, height + 8), 14, (214, 50, 74, 255), (255, 145, 164, 100), 2)
    draw_fit(d, (22, 22, width - 8, height - 2), text, 40, 24, (255, 255, 255, 255), True, "center", "center")
    return layer


def top_pill_layer(text: str, width=380):
    layer = Image.new("RGBA", (width + 10, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    rounded(d, (4, 5, width + 4, 65), 30, (8, 20, 42, 228), (255, 255, 255, 35), 1)
    draw_fit(d, (22, 12, width - 10, 58), text, 30, 20, (93, 226, 238, 255), True, "center", "center")
    return layer


def bottom_band(img: Image.Image, text: str, alpha=255):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    y = H - 112
    for x in range(W):
        t = x / W
        col = (int(14 * (1 - t) + 23 * t), int(52 * (1 - t) + 118 * t), int(105 * (1 - t) + 130 * t), 232)
        d.line((x, y, x, H), fill=col)
    d.line((0, y - 4, W, y - 4), fill=(0, 0, 0, 135), width=5)
    d.line((0, y, W, y), fill=(255, 255, 255, 58), width=1)
    draw_fit(d, (260, y + 18, W - 260, H - 18), text, 44, 28, (255, 225, 92, 255), True, "center", "center", 2, (0, 0, 0, 230))
    overlay_alpha(img, layer, alpha)


def title_frame(bg: Image.Image, t: float, duration: float):
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    paste_alpha(img, badge_layer("決定版", 230, 86), (58, 50), fade_in(t, 0.1))
    img.alpha_composite(top_pill_layer("独自ランキング", 330), (1510, 56))
    draw_fit(d, (620, slide_y(150, t, 0.2), 1300, 220), "V A L U E   S H I F T", 48, 34, (238, 236, 248, fade_in(t, 0.2)), True, "center", "center")
    title_alpha = fade_in(t, 0.55)
    draw_fit(d, (230, slide_y(335, t, 0.55), 1690, 560), "親世代と評価が変わった\n大学ランキング", 106, 72, (252, 252, 255, title_alpha), True, "center", "center", 2, (0, 0, 0, min(210, title_alpha)))
    year_alpha = fade_in(t, 1.3)
    scale = 1.0 + 0.06 * (1 - ease((t - 1.3) / 0.7))
    size = int(184 * scale)
    draw_fit(d, (650, 650, 1270, 840), "2026", size, 120, (255, 218, 78, year_alpha), True, "center", "center", 2, (74, 43, 3, min(220, year_alpha)))
    bottom_band(img, "志願者数・就職・学部改革データ完全集計", fade_in(t, 1.8))
    return img


def method_frame(bg: Image.Image, t: float, duration: float):
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    paste_alpha(img, badge_layer("評価軸", 230, 86), (58, 50), fade_in(t, 0.1))
    img.alpha_composite(top_pill_layer("DATA ALCHEMIST", 360), (1480, 56))
    draw_fit(d, (120, 185, 860, 390), "偏差値だけでは見えない\n“評価の変化”を見る", 78, 50, (252, 252, 255, fade_in(t, 0.25)), True, "left", "center", 2, (0, 0, 0, 180))
    axes = [
        ("志願者数", "いま受験生に選ばれているか"),
        ("就職実績", "企業から評価されているか"),
        ("学部改革", "AI・データ・実学に対応しているか"),
        ("印象差", "親世代のイメージからどれだけ変わったか"),
    ]
    for i, (a, b) in enumerate(axes):
        start = 0.7 + i * 0.28
        x = int(1030 + 70 * (1 - ease((t - start) / 0.5)))
        y = 178 + i * 150
        alpha = fade_in(t, start)
        card = Image.new("RGBA", (790, 118), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card, "RGBA")
        rounded(cd, (0, 0, 790, 112), 22, (7, 15, 27, 178), (255, 255, 255, 35), 1)
        cd.ellipse((32, 30, 82, 80), fill=(255, 218, 78, 255))
        draw_fit(cd, (32, 30, 82, 80), str(i + 1), 30, 22, (9, 15, 25, 255), True, "center", "center")
        draw_fit(cd, (112, 14, 760, 56), a, 42, 30, (255, 255, 255, 255), True)
        draw_fit(cd, (112, 62, 760, 100), b, 28, 22, (210, 222, 229, 255), True)
        if alpha < 255:
            a = card.getchannel("A").point(lambda p: p * alpha // 255)
            card.putalpha(a)
        img.alpha_composite(card, (x, y))
    bottom_band(img, "公開情報をもとにした独自ランキングです", fade_in(t, 1.8))
    return img


def rank_frame(bg: Image.Image, item: dict, t: float, duration: float):
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    paste_alpha(img, badge_layer(f"第{item['rank']}位", 230, 86), (58, 50), fade_in(t, 0.05))
    img.alpha_composite(top_pill_layer(item["tag"], 440), (1390, 56))

    draw_fit(d, (112, slide_y(190, t, 0.25), 920, 292), item["name"], 82, 48, (255, 255, 255, fade_in(t, 0.25)), True, "left", "center", 2, (0, 0, 0, 190))
    draw_fit(d, (112, 300, 520, 354), f"変化スコア {item['score']}", 38, 28, (255, 225, 92, fade_in(t, 0.45)), True)
    # Animated score bar.
    bar_alpha = fade_in(t, 0.6)
    bx, by, bw, bh = 112, 362, 640, 28
    d.rounded_rectangle((bx, by, bx + bw, by + bh), 14, fill=(255, 255, 255, int(45 * bar_alpha / 255)))
    fill_w = int(bw * item["score"] / 100 * ease((t - 0.75) / 0.9))
    d.rounded_rectangle((bx, by, bx + fill_w, by + bh), 14, fill=(255, 218, 78, bar_alpha))

    # Cards.
    card_y = 448
    old_x = int(112 - 42 * (1 - ease((t - 1.05) / 0.55)))
    now_x = int(1040 + 42 * (1 - ease((t - 1.25) / 0.55)))
    old_alpha = fade_in(t, 1.05)
    now_alpha = fade_in(t, 1.25)
    for x, alpha, label, body, fill, label_color in [
        (old_x, old_alpha, "親世代の印象", item["old"], (7, 15, 27, 205), (156, 182, 198, 255)),
        (now_x, now_alpha, "いまの評価", item["now"], (14, 59, 72, 205), (255, 225, 92, 255)),
    ]:
        card = Image.new("RGBA", (770, 232), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card, "RGBA")
        rounded(cd, (0, 0, 770, 226), 26, fill, (255, 255, 255, 36), 1)
        draw_fit(cd, (38, 26, 720, 70), label, 34, 26, label_color, True)
        draw_fit(cd, (38, 90, 725, 190), body, 44, 29, (255, 255, 255, 255), True, "left", "center")
        overlay_alpha(card, Image.new("RGBA", card.size, (0, 0, 0, 0)), 0)
        if alpha < 255:
            a = card.getchannel("A").point(lambda p: p * alpha // 255)
            card.putalpha(a)
        img.alpha_composite(card, (x, card_y))

    reason_alpha = fade_in(t, 1.85)
    reason = Image.new("RGBA", (1700, 146), (0, 0, 0, 0))
    rd = ImageDraw.Draw(reason, "RGBA")
    rounded(rd, (0, 0, 1700, 140), 24, (0, 0, 0, 132), (255, 255, 255, 28), 1)
    draw_fit(rd, (42, 25, 1658, 118), item["reason"], 36, 25, (238, 244, 242, 255), True, "left", "center")
    if reason_alpha < 255:
        a = reason.getchannel("A").point(lambda p: p * reason_alpha // 255)
        reason.putalpha(a)
    img.alpha_composite(reason, (112, 748))
    bottom_band(img, "親世代のイメージから、いまの実力へ", fade_in(t, 2.2))
    return img


def final_frame(bg: Image.Image, t: float, duration: float):
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    paste_alpha(img, badge_layer("結論", 230, 86), (58, 50), fade_in(t, 0.05))
    img.alpha_composite(top_pill_layer("VALUE SHIFT", 330), (1510, 56))
    draw_fit(d, (260, 190, 1660, 300), "評価が変わる大学の共通点", 76, 50, (255, 255, 255, fade_in(t, 0.25)), True, "center", "center", 2, (0, 0, 0, 180))
    bullets = ["時代に合う学部を作る", "就職実績を数字で示せる", "昔の校名イメージを超える強みがある"]
    for i, b in enumerate(bullets):
        start = 0.7 + i * 0.35
        alpha = fade_in(t, start)
        y = int(380 + i * 130 + 28 * (1 - ease((t - start) / 0.5)))
        card = Image.new("RGBA", (1240, 94), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card, "RGBA")
        rounded(cd, (0, 0, 1240, 90), 22, (7, 15, 27, 185), (255, 255, 255, 35), 1)
        cd.ellipse((38, 23, 84, 69), fill=(255, 218, 78, 255))
        draw_fit(cd, (116, 14, 1200, 74), b, 42, 30, (255, 255, 255, 255), True, "left", "center")
        if alpha < 255:
            a = card.getchannel("A").point(lambda p: p * alpha // 255)
            card.putalpha(a)
        img.alpha_composite(card, (340, y))
    bottom_band(img, "大学選びは、名前の印象より“伸びている理由”を見る時代へ", fade_in(t, 1.8))
    return img


@dataclass
class Scene:
    kind: str
    duration: float
    data: dict | None = None
    seed: int = 0


def scene_clip(scene: Scene):
    bg = make_bg(scene.seed)

    def make_frame(t):
        if scene.kind == "title":
            img = title_frame(bg, t, scene.duration)
        elif scene.kind == "method":
            img = method_frame(bg, t, scene.duration)
        elif scene.kind == "rank":
            img = rank_frame(bg, scene.data, t, scene.duration)
        else:
            img = final_frame(bg, t, scene.duration)
        return np.array(img.convert("RGB"))

    return VideoClip(make_frame=make_frame, duration=scene.duration)


def main():
    BUILD.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    ranking = json.loads((DIST / "ranking.json").read_text(encoding="utf-8"))
    ranking = sorted(ranking, key=lambda x: x["rank"], reverse=True)
    scenes = [Scene("title", 5.5, seed=1), Scene("method", 6.5, seed=2)]
    scenes += [Scene("rank", 6.8, data=item, seed=10 + item["rank"]) for item in ranking]
    scenes.append(Scene("final", 7.0, seed=30))
    clips = [scene_clip(s) for s in scenes]
    video = concatenate_videoclips(clips, method="compose")
    out = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking_motion_no_voice.mp4"
    video.write_videofile(
        str(out),
        fps=FPS,
        codec="libx264",
        preset="medium",
        audio=False,
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )
    main_out = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking.mp4"
    main_out.write_bytes(out.read_bytes())
    print(out)


if __name__ == "__main__":
    main()
