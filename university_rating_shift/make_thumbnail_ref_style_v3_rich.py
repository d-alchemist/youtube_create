from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
REF = ROOT / "assets" / "ref_engineering_ranking_maxres.jpg"
W, H = 1280, 720
FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


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


def make_base():
    src = Image.open(REF).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    # Keep the original richness, but blur away its exact typography.
    bg = src.filter(ImageFilter.GaussianBlur(26))
    bg = ImageEnhance.Contrast(bg).enhance(1.12)
    bg = ImageEnhance.Color(bg).enhance(1.18)

    # Recolor the reference toward a premium teal-burgundy palette while retaining its tonal depth.
    teal = Image.new("RGB", (W, H), (0, 78, 82))
    burgundy = Image.new("RGB", (W, H), (42, 13, 55))
    split = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(split)
    for x in range(W):
        sd.line((x, 0, x, H), fill=int(255 * x / W))
    colorwash = Image.composite(teal, burgundy, split)
    bg = Image.blend(bg, colorwash, 0.40)
    bg = ImageEnhance.Brightness(bg).enhance(0.84)

    # Dark vignette to restore the cinematic edge of the original.
    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    for i in range(0, 260, 2):
        alpha = int(190 * (i / 260) ** 1.8)
        vd.rectangle((i, i, W - i, H - i), outline=255 - alpha, width=2)
    vignette = ImageOps.invert(vignette).filter(ImageFilter.GaussianBlur(34))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.composite(dark, bg, vignette.point(lambda p: int(p * 0.42)))

    return bg.convert("RGBA")


def badge(base):
    layer = Image.new("RGBA", (280, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.rounded_rectangle((14, 14, 266, 116), 13, fill=(214, 50, 74, 255), outline=(255, 145, 164, 108), width=2)
    draw_text(d, (140, 42), "決定版", 42, (255, 255, 255, 255), True, anchor="ma")
    layer = layer.rotate(357, expand=True, resample=Image.Resampling.BICUBIC)
    shadow = layer.filter(ImageFilter.GaussianBlur(5))
    base.alpha_composite(shadow, (30, 28))
    base.alpha_composite(layer, (28, 24))


def pill(base):
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((986, 40, 1248, 98), 29, fill=(9, 22, 43, 238), outline=(255, 255, 255, 24), width=1)
    draw_text(d, (1117, 55), "独自ランキング", 30, (91, 221, 236, 255), True, anchor="ma")


def white_title(base):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    draw_text(d, (646, 250), "親世代と評価が変わった\n大学ランキング", 76, (0, 0, 0, 150), True, anchor="ma", stroke=3, stroke_fill=(0, 0, 0, 170), spacing=6)
    draw_text(d, (640, 242), "親世代と評価が変わった\n大学ランキング", 76, (252, 252, 255, 255), True, anchor="ma", stroke=1, stroke_fill=(30, 24, 42, 210), spacing=6)
    base.alpha_composite(layer)


def gold_year(base):
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    draw_text(gd, (640, 468), "2026", 118, (255, 219, 82, 220), True, anchor="ma", stroke=2, stroke_fill=(72, 38, 0, 160))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(7)))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    draw_text(d, (646, 475), "2026", 118, (0, 0, 0, 125), True, anchor="ma", stroke=2, stroke_fill=(0, 0, 0, 120))
    draw_text(d, (640, 468), "2026", 118, (255, 218, 78, 255), True, anchor="ma", stroke=2, stroke_fill=(74, 43, 3, 220))
    # subtle lower warm pass
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle((0, 470, W, 570), fill=130)
    lower = Image.new("RGBA", (W, H), (190, 111, 8, 105))
    layer = Image.alpha_composite(layer, Image.composite(lower, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask))
    base.alpha_composite(layer)


def bottom_band(base):
    band = Image.new("RGBA", (W, 92), (0, 0, 0, 0))
    d = ImageDraw.Draw(band, "RGBA")
    for x in range(W):
        t = x / W
        r = int(14 * (1 - t) + 23 * t)
        g = int(52 * (1 - t) + 118 * t)
        b = int(105 * (1 - t) + 130 * t)
        d.line((x, 0, x, 92), fill=(r, g, b, 232))
    base.alpha_composite(band, (0, 630))
    d = ImageDraw.Draw(base, "RGBA")
    d.line((0, 626, W, 626), fill=(0, 0, 0, 120), width=3)
    d.line((0, 630, W, 630), fill=(255, 255, 255, 58), width=1)
    draw_text(d, (640, 654), "志願者数・就職・学部改革データ完全集計", 43, (255, 224, 92, 255), True, anchor="ma", stroke=2, stroke_fill=(0, 0, 0, 230))


def main():
    DIST.mkdir(exist_ok=True)
    img = make_base()
    d = ImageDraw.Draw(img, "RGBA")
    draw_text(d, (640, 102), "V A L U E   S H I F T", 34, (238, 236, 248, 230), True, anchor="ma")
    badge(img)
    pill(img)
    white_title(img)
    gold_year(img)
    bottom_band(img)
    out = DIST / "thumbnail_ref_style_v3_rich_recolor.jpg"
    img.convert("RGB").save(out, quality=95)
    img.convert("RGB").save(DIST / "thumbnail_oyasedai_hyouka_daigaku.jpg", quality=95)
    print(out)


if __name__ == "__main__":
    main()
