from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import ImageDraw

from make_15min_slides_no_voice import (
    BLUE,
    GOLD,
    WHITE,
    Slide,
    draw_gold_badge,
    fit_text,
    footer,
    header,
    make_background,
    neon_line,
    neon_rounded,
)


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
OUT_DIR = DIST / "ab_test"


@dataclass(frozen=True)
class ABVariant:
    id: str
    label: str
    filename_stem: str
    title: str
    thumbnail_main: str
    thumbnail_subtitle: str
    badge: str
    point: str
    hypothesis: str


VARIANTS = [
    ABVariant(
        id="A",
        label="定番ランキング訴求",
        filename_stem="thumbnail_A_ranking_top10",
        title="親世代と評価が変わった大学ランキングTOP10｜偏差値だけでは見えない“今選ばれる大学”",
        thumbnail_main="親世代と評価が変わった\n大学ランキング TOP10",
        thumbnail_subtitle="偏差値だけでは見えない、いま選ばれる大学の変化を見る",
        badge="意外と知らない大学評価の変化",
        point="名前のイメージではなく、いま選ばれている理由に注目します。",
        hypothesis="既存サムネに近い王道型。ランキング目的の視聴者に最も誤解なく刺さるかを見る。",
    ),
    ABVariant(
        id="B",
        label="違和感・問いかけ訴求",
        filename_stem="thumbnail_B_parent_image_old",
        title="親世代の大学イメージはもう古い？評価が変わった大学TOP10をデータで解説",
        thumbnail_main="親世代の常識、\nもう古い？",
        thumbnail_subtitle="志願者数・就職・学部改革で評価が変わった大学",
        badge="大学ランキング TOP10",
        point="昔の知名度ではなく、いまの数字で見ます。",
        hypothesis="疑問形でクリック前の違和感を作る型。親子世代の認識差に反応する層を狙う。",
    ),
    ABVariant(
        id="C",
        label="データ根拠訴求",
        filename_stem="thumbnail_C_data_selected",
        title="志願者数・就職実績で見る「今選ばれる大学」TOP10｜親世代と評価が変わった大学",
        thumbnail_main="今選ばれる大学は\nどこが違う？",
        thumbnail_subtitle="親世代のイメージから評価が更新された大学をデータで検証",
        badge="志願者数・就職実績で比較",
        point="上位校ほど、評価が変わった理由が数字で見えます。",
        hypothesis="ランキングより根拠を前に出す型。受験・進路情報として保存価値を感じる層を狙う。",
    ),
]


def draw_ab_thumbnail(variant: ABVariant, index: int, out_png: Path, out_jpg: Path) -> None:
    img = make_background(40 + index).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    fake_slide = Slide("thumbnail", 0, "", "", [], "title")
    header(draw, fake_slide, 0, 18)
    footer(draw, fake_slide)

    fit_text(
        draw,
        (105, 185, 1815, 430),
        variant.thumbnail_main,
        104,
        68,
        WHITE,
        True,
        "center",
        "center",
        3,
        (0, 0, 0, 245),
    )
    neon_line(draw, [(245, 472), (820, 472), (960, 465), (1100, 472), (1675, 472)], BLUE, 2)
    fit_text(
        draw,
        (210, 502, 1710, 570),
        variant.thumbnail_subtitle,
        42,
        27,
        (238, 244, 246, 245),
        True,
        "center",
        "center",
        1,
        (0, 0, 0, 180),
    )
    draw_gold_badge(draw, (430, 635, 1490, 732), variant.badge)

    y = 805
    neon_rounded(draw, (95, y, 1825, y + 124), 18, (2, 10, 25, 232), BLUE, 3)
    draw.ellipse((138, y + 28, 210, y + 100), fill=GOLD, outline=(255, 247, 180, 255), width=2)
    fit_text(draw, (138, y + 28, 210, y + 100), "1", 42, 28, (12, 12, 20, 255), True, "center", "center")
    fit_text(
        draw,
        (255, y + 22, 1770, y + 102),
        variant.point,
        44,
        26,
        WHITE,
        True,
        "left",
        "center",
        1,
        (0, 0, 0, 190),
    )
    img.convert("RGB").save(out_png)
    img.convert("RGB").save(out_jpg, quality=96)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    title_lines = []
    meta = {
        "purpose": "YouTube A/Bテスト用のサムネイル3種・タイトル3種",
        "pairing": "基本は同じID同士のサムネイルとタイトルを組み合わせます。",
        "variants": [],
    }

    for index, variant in enumerate(VARIANTS):
        out_png = OUT_DIR / f"{variant.filename_stem}.png"
        out_jpg = OUT_DIR / f"{variant.filename_stem}.jpg"
        draw_ab_thumbnail(variant, index, out_png, out_jpg)

        title_lines.append(f"{variant.id}. {variant.title}")
        meta["variants"].append(
            {
                "id": variant.id,
                "label": variant.label,
                "title": variant.title,
                "thumbnail_png": str(out_png),
                "thumbnail_jpg": str(out_jpg),
                "hypothesis": variant.hypothesis,
            }
        )

    titles_path = OUT_DIR / "titles_ab_test.txt"
    titles_path.write_text("\n".join(title_lines) + "\n", encoding="utf-8")
    meta["titles_txt"] = str(titles_path)

    json_path = OUT_DIR / "ab_test_outputs.json"
    json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
