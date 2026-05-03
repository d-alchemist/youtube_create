from __future__ import annotations

import json
import math
import os
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
W, H = 1920, 1080

FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"


SOURCES = [
    {
        "label": "千葉工業大学 2025年度一般選抜志願者数 私大1位",
        "url": "https://s.resemom.jp/article/2025/04/11/81582.html",
    },
    {
        "label": "近畿大学 2026年度一般入試・総志願者数 過去最多",
        "url": "https://www.sentankyo.jp/articles/8bad7624-7d85-4e9b-bfdf-6e0d6cec0f1e",
    },
    {
        "label": "東洋大学 TOYO Data 2025 志願者数 私立大学全国4位",
        "url": "https://www.toyo.ac.jp/toyo2025/digest/",
    },
    {
        "label": "芝浦工業大学 THE日本大学ランキング2025 私立7位",
        "url": "https://www.shibaura-it.ac.jp/headline/detail/20250403-7070-002.html",
    },
    {
        "label": "名城大学 実就職率ランキング 15年連続 全国No.1",
        "url": "https://www.meijo-u.ac.jp/news/detail_31767.html",
    },
    {
        "label": "東京電機大学 就職内定率99.2%、求人社数17,545社",
        "url": "https://www.dendai.ac.jp/about/career/support/job.html",
    },
    {
        "label": "武蔵野大学 データサイエンス学部・AI/ビッグデータ教育",
        "url": "https://www.musashino-u.ac.jp/academics/faculty/data_science/",
    },
    {
        "label": "金沢工業大学 プロジェクトデザイン教育",
        "url": "https://www.kanazawa-it.ac.jp/kyoiku/pd/index.html",
    },
]


RANKING = [
    {
        "rank": 10,
        "name": "東京都市大学",
        "score": 78,
        "old": "武蔵工大の理工系イメージ",
        "now": "都市・環境・情報まで広がる実学系大学",
        "reason": "理工系の土台に、都市生活・環境・情報系の見え方が加わり、親世代の学校名イメージから変化。",
        "tag": "理工系＋都市領域",
    },
    {
        "rank": 9,
        "name": "國學院大學",
        "score": 80,
        "old": "文学・神道の伝統校",
        "now": "渋谷立地と堅実就職で再評価",
        "reason": "伝統色が強かった大学が、都心立地と人文・法・経済系の堅実な進路で受験生に再発見されている。",
        "tag": "伝統校の再評価",
    },
    {
        "rank": 8,
        "name": "金沢工業大学",
        "score": 82,
        "old": "地方の工業大学",
        "now": "PBL型の実践教育で評価",
        "reason": "全学生必修のプロジェクトデザイン教育など、実践型エンジニア育成が時代に合っている。",
        "tag": "PBL・実践教育",
    },
    {
        "rank": 7,
        "name": "武蔵野大学",
        "score": 84,
        "old": "女子大・文系中心の印象",
        "now": "AI・データサイエンスも持つ総合大学",
        "reason": "データサイエンス、アントレプレナーシップ、サステナビリティなど新領域の展開が早い。",
        "tag": "新学部改革",
    },
    {
        "rank": 6,
        "name": "東京電機大学",
        "score": 86,
        "old": "電機・工学の専門校",
        "now": "メーカー・ITに強い技術者大学",
        "reason": "2025年3月卒業生・修了生の就職内定率99.2%。求人社数17,545社という企業接点も強い。",
        "tag": "就職内定率99.2%",
    },
    {
        "rank": 5,
        "name": "名城大学",
        "score": 88,
        "old": "中部の大規模私大",
        "now": "実就職率で全国級の評価",
        "reason": "学部卒業生2,000人以上の大学で、実就職率ランキング15年連続全国No.1という実績が強い。",
        "tag": "実就職率に強い",
    },
    {
        "rank": 4,
        "name": "芝浦工業大学",
        "score": 90,
        "old": "地味な工業大学",
        "now": "首都圏理工系の有力校",
        "reason": "THE日本大学ランキング2025で総合32位、私立7位。理工系人気と国際性評価で存在感が上昇。",
        "tag": "理工系ブランド上昇",
    },
    {
        "rank": 3,
        "name": "東洋大学",
        "score": 92,
        "old": "中堅私大の一角",
        "now": "首都圏の人気総合大学",
        "reason": "2025年度の志願者数は113,762名で、私立大学全国4位。学部規模と都心キャンパスの強さが見える。",
        "tag": "志願者数 全国4位",
    },
    {
        "rank": 2,
        "name": "近畿大学",
        "score": 95,
        "old": "関西の大規模私大",
        "now": "実学・広報・改革の全国ブランド",
        "reason": "2026年度の総志願者数は234,245人で過去最多。実学教育と新学部展開で親世代の印象を更新。",
        "tag": "総志願者23万人超",
    },
    {
        "rank": 1,
        "name": "千葉工業大学",
        "score": 98,
        "old": "工業系の単科大学イメージ",
        "now": "AI・宇宙・半導体で志願者数トップ級",
        "reason": "2025年度一般選抜の志願者数は162,005人で私立大学1位。宇宙・半導体など時代に直結する改革が強い。",
        "tag": "2025 私大志願者1位",
    },
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def wrap_jp(text: str, max_chars: int) -> list[str]:
    lines = []
    for paragraph in text.split("\n"):
        buf = ""
        for ch in paragraph:
            buf += ch
            if len(buf) >= max_chars:
                lines.append(buf)
                buf = ""
        if buf:
            lines.append(buf)
    return lines


def draw_text(draw, xy, text, size, fill=(245, 248, 246), bold=False, anchor=None, spacing=12):
    draw.multiline_text(xy, text, font=font(size, bold), fill=fill, anchor=anchor, spacing=spacing)


def gradient_bg(accent=(10, 138, 103)):
    img = Image.new("RGB", (W, H), (7, 11, 13))
    pix = img.load()
    for y in range(H):
        for x in range(W):
            d1 = math.hypot((x - 230) / W, (y - 230) / H)
            d2 = math.hypot((x - 1660) / W, (y - 860) / H)
            glow = max(0, 1 - d1 * 2.4) * 70 + max(0, 1 - d2 * 2.1) * 45
            r = int(7 + glow * accent[0] / 255)
            g = int(11 + glow * accent[1] / 255)
            b = int(13 + glow * accent[2] / 255)
            pix[x, y] = (r, g, b)
    return img


def card(draw, box, fill=(14, 42, 37), outline=(35, 118, 97), width=2):
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=width)


def header(draw, title, subtitle="DATA ALCHEMIST"):
    draw_text(draw, (80, 54), subtitle, 28, fill=(124, 221, 182), bold=True)
    draw_text(draw, (80, 92), title, 58, bold=True)
    draw.line((80, 170, 1840, 170), fill=(31, 99, 84), width=2)


def save_title_slide(path: Path):
    img = gradient_bg((8, 170, 125))
    d = ImageDraw.Draw(img)
    draw_text(d, (92, 120), "親世代と評価が変わった", 72, bold=True)
    draw_text(d, (92, 215), "大学ランキング", 118, fill=(255, 206, 91), bold=True)
    draw_text(d, (96, 365), "偏差値だけでは見えない、いま選ばれる大学", 44, fill=(218, 237, 230), bold=True)
    d.rounded_rectangle((92, 470, 760, 548), 16, fill=(255, 206, 91))
    draw_text(d, (122, 488), "独自スコア TOP10", 42, fill=(12, 26, 24), bold=True)
    d.text((1090, 210), "TOP\n10", font=font(220, True), fill=(26, 127, 103), spacing=-18)
    draw_text(d, (96, 920), "評価軸：志願者数 / 就職実績 / 学部改革 / 時代適合性", 34, fill=(170, 205, 193), bold=True)
    img.save(path)


def save_method_slide(path: Path):
    img = gradient_bg((11, 127, 103))
    d = ImageDraw.Draw(img)
    header(d, "ランキングの見方")
    items = [
        ("1", "親世代のイメージ", "昔の校名・学部構成・地域イメージ"),
        ("2", "いまの評価", "志願者数、就職、改革、社会ニーズ"),
        ("3", "変化の大きさ", "有名かどうかではなく、印象がどれだけ更新されたか"),
    ]
    y = 240
    for num, ttl, desc in items:
        card(d, (110, y, 1810, y + 170))
        d.ellipse((150, y + 42, 230, y + 122), fill=(255, 206, 91))
        draw_text(d, (190, y + 57), num, 36, fill=(11, 28, 25), bold=True, anchor="ma")
        draw_text(d, (270, y + 38), ttl, 48, bold=True)
        draw_text(d, (270, y + 100), desc, 34, fill=(196, 224, 215))
        y += 205
    draw_text(d, (120, 935), "※公開情報をもとにした独自ランキングです。偏差値だけの順位ではありません。", 31, fill=(255, 225, 143), bold=True)
    img.save(path)


def save_rank_slide(path: Path, item: dict):
    img = gradient_bg((11, 135, 103))
    d = ImageDraw.Draw(img)
    header(d, f"第{item['rank']}位")
    d.text((112, 225), item["name"], font=font(102, True), fill=(255, 206, 91))
    d.rounded_rectangle((112, 350, 610, 420), 14, fill=(21, 111, 88))
    draw_text(d, (140, 364), item["tag"], 38, bold=True)
    card(d, (112, 485, 860, 735), fill=(14, 38, 35))
    draw_text(d, (150, 520), "親世代の印象", 34, fill=(127, 217, 181), bold=True)
    draw_text(d, (150, 585), "\n".join(wrap_jp(item["old"], 17)), 46, bold=True)
    card(d, (940, 485, 1810, 735), fill=(31, 49, 39), outline=(190, 134, 56))
    draw_text(d, (980, 520), "いまの評価", 34, fill=(255, 206, 91), bold=True)
    draw_text(d, (980, 585), "\n".join(wrap_jp(item["now"], 18)), 46, bold=True)
    draw_text(d, (130, 800), "\n".join(wrap_jp(item["reason"], 44)), 38, fill=(220, 237, 231), bold=True)
    d.rounded_rectangle((112, 930, 1810, 975), 22, fill=(20, 42, 37))
    d.rounded_rectangle((112, 930, 112 + int(1698 * item["score"] / 100), 975), 22, fill=(255, 206, 91))
    draw_text(d, (1460, 900), f"変化スコア {item['score']}", 38, fill=(255, 206, 91), bold=True)
    img.save(path)


def save_summary_slide(path: Path):
    img = gradient_bg((11, 135, 103))
    d = ImageDraw.Draw(img)
    header(d, "結論")
    draw_text(d, (120, 240), "親世代の評価が変わる大学には、共通点があります。", 58, bold=True)
    bullets = [
        "時代に合う学部を早く作る",
        "就職実績を数字で示せる",
        "入試や広報で受験生に届いている",
        "昔の校名イメージを超える強みがある",
    ]
    y = 375
    for b in bullets:
        d.rounded_rectangle((130, y + 10, 178, y + 58), 8, fill=(255, 206, 91))
        draw_text(d, (210, y), b, 48, fill=(235, 246, 240), bold=True)
        y += 112
    draw_text(d, (120, 860), "大学選びは、知名度よりも「いま伸びている理由」を見る時代です。", 44, fill=(255, 225, 143), bold=True)
    img.save(path)


def save_thumbnail(path: Path):
    img = gradient_bg((14, 150, 112))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((70, 62, 315, 148), 16, fill=(228, 63, 63))
    draw_text(d, (95, 82), "親世代は知らない", 32, bold=True)
    draw_text(d, (82, 210), "評価が", 100, fill=(245, 248, 246), bold=True)
    draw_text(d, (82, 330), "変わった大学", 112, fill=(255, 206, 91), bold=True)
    draw_text(d, (82, 490), "ランキング", 86, fill=(245, 248, 246), bold=True)
    d.text((1240, 118), "TOP\n10", font=font(210, True), fill=(28, 149, 116), spacing=-16)
    d.rounded_rectangle((88, 810, 1730, 925), 18, fill=(13, 34, 31), outline=(255, 206, 91), width=3)
    draw_text(d, (125, 837), "偏差値だけでは見えない“いま選ばれる大学”", 48, fill=(255, 225, 143), bold=True)
    img.save(path, quality=94)


def make_metadata():
    title = "親世代と評価が変わった大学ランキングTOP10｜偏差値だけでは見えない“今選ばれる大学”"
    description = """今回は「親世代のイメージ」と「いまの受験生・企業からの評価」が大きく変わった大学を、公開情報をもとに独自ランキング化しました。

偏差値だけではなく、志願者数、就職実績、学部改革、AI・データサイエンス・半導体などの時代適合性を重視しています。

※このランキングは公開情報をもとにした独自集計です。大学の優劣を断定するものではなく、大学選びの視点を増やすためのコンテンツです。

▼評価軸
・志願者数、人気の変化
・就職実績、企業からの評価
・学部、学科改革のスピード
・親世代のイメージからの変化幅

▼参考情報
""" + "\n".join(f"・{s['label']}\n  {s['url']}" for s in SOURCES) + """

#大学ランキング #大学受験 #親世代と評価が変わった大学 #就職に強い大学 #データの錬金術師"""
    (DIST / "title.txt").write_text(title + "\n", encoding="utf-8")
    (DIST / "description.txt").write_text(description, encoding="utf-8")
    (DIST / "sources.json").write_text(json.dumps(SOURCES, ensure_ascii=False, indent=2), encoding="utf-8")
    (DIST / "ranking.json").write_text(json.dumps(RANKING, ensure_ascii=False, indent=2), encoding="utf-8")
    script = [
        "親世代が知っている大学の評価と、いま受験生が見ている大学の評価は、かなり変わっています。",
        "今回は偏差値だけではなく、志願者数、就職実績、学部改革、そして時代に合っているかをもとに、評価が変わった大学をランキング化しました。",
    ]
    for item in RANKING:
        script.append(f"第{item['rank']}位、{item['name']}。親世代の印象は、{item['old']}。しかし今は、{item['now']}。{item['reason']}")
    script.append("ランキング上位に共通するのは、昔の知名度ではなく、今の社会が求める学びを早く形にしていることです。大学選びでは、名前のイメージだけでなく、いま伸びている理由を見ることが大切です。")
    (DIST / "narration_script.txt").write_text("\n\n".join(script), encoding="utf-8")


def say_audio(text: str, out: Path):
    subprocess.run(["say", "-v", "Kyoko", "-r", "183", "-o", str(out), text], check=True)


def ffprobe_duration(path: Path) -> float:
    res = subprocess.run(
        ["/opt/anaconda3/bin/ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(res.stdout.strip())


def make_video():
    slides = []
    title = BUILD / "slide_00.png"
    save_title_slide(title)
    slides.append((title, "親世代と評価が変わった大学ランキング。偏差値だけでは見えない、いま選ばれる大学を見ていきます。"))

    method = BUILD / "slide_01.png"
    save_method_slide(method)
    slides.append((method, "このランキングは公開情報をもとにした独自集計です。親世代のイメージと、いまの志願者数、就職実績、学部改革、時代適合性の差に注目します。"))

    for i, item in enumerate(RANKING, start=2):
        p = BUILD / f"slide_{i:02d}.png"
        save_rank_slide(p, item)
        slides.append((p, f"第{item['rank']}位、{item['name']}。親世代の印象は、{item['old']}。今は、{item['now']}。{item['reason']}"))

    summary = BUILD / "slide_99.png"
    save_summary_slide(summary)
    slides.append((summary, "上位校に共通するのは、昔の知名度ではなく、今の社会が求める学びを早く形にしていることです。大学選びでは、名前のイメージだけでなく、いま伸びている理由を見てください。"))

    parts = []
    for idx, (slide, narration) in enumerate(slides):
        aiff = BUILD / f"audio_{idx:02d}.aiff"
        mp4 = BUILD / f"part_{idx:02d}.mp4"
        say_audio(narration, aiff)
        dur = ffprobe_duration(aiff) + 0.55
        subprocess.run(
            [
                "/opt/anaconda3/bin/ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(slide),
                "-i",
                str(aiff),
                "-t",
                f"{dur:.2f}",
                "-vf",
                "format=yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-tune",
                "stillimage",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-shortest",
                str(mp4),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        parts.append(mp4)

    concat = BUILD / "concat.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    subprocess.run(
        [
            "/opt/anaconda3/bin/ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-c",
            "copy",
            str(DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking.mp4"),
        ],
        check=True,
    )


def main():
    ASSETS.mkdir(exist_ok=True)
    BUILD.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    save_thumbnail(DIST / "thumbnail_oyasedai_hyouka_daigaku.jpg")
    make_metadata()
    make_video()
    print("done")


if __name__ == "__main__":
    main()
