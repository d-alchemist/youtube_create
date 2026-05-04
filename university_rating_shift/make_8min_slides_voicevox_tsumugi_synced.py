from __future__ import annotations

import argparse
import hashlib
import json
from json import JSONDecodeError
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build_voicevox_8min"
FFMPEG = "/opt/anaconda3/bin/ffmpeg"
FFPROBE = "/opt/anaconda3/bin/ffprobe"
FPS = 24

SPEAKER_ID = 8  # VOICEVOX: 春日部つむぎ
LOCAL_ENGINE = "http://127.0.0.1:50021"
TTS_QUEST = "https://api.tts.quest/v3/voicevox/synthesis"

HIRAGANA_TEXT_BY_SLUG = {
    "title": (
        "おやせだいとひょうかがかわった、だいがくらんきんぐ、とっぷてん。"
        "へんさちだけではみえない、いまえらばれるだいがくのへんかをみる。"
        "いがいとしらないだいがくひょうかのへんか。"
        "なまえのいめえじではなく、いまえらばれているりゆうにちゅうもくします。"
    ),
    "premise": (
        "おやせだいのいめえじと、いまのひょうかはちがう。"
        "こうめい、むかしのへんさち、そつぎょうせいのいんしょうだけでは、げんざいのだいがくかちはみえにくい。"
        "おやせだいのひょうかは、むかしのちめいどやこうめいいめえじにひっぱられやすいです。"
        "いまのひょうかは、しがんしゃすう、しゅうしょくじっせき、がくぶかいかく、しゃかいにいずとのせつぞくでかわります。"
        "このらんきんぐでは、おやせだいのいんしょうからどれだけひょうかがこうしんされたかをみます。"
    ),
    "method": (
        "ひょうかじくはよっつ。"
        "にんき、しゅうしょく、かいかく、いんしょうさを、こうかいじょうほうべえすでどくじしゅうけい。"
        "しがんしゃすうは、いまじゅけんせいにえらばれているかをみるしひょうです。"
        "しゅうしょくじっせきとがくぶかいかくは、きぎょうやしゃかいからのひょうかにつながるしひょうです。"
    ),
    "score_chart": (
        "ぜんたいぞう。どくじひょうかすこあ。"
        "じょういほど、おやせだいのいんしょうからげんざいのひょうかへのへんかがおおきい。"
    ),
    "applicant_chart": (
        "こんきょぐらふ。しがんしゃすうでみるへんか。"
        "いちぶのだいがくは、じゅけんせいからのえらばれかたがすうじではっきりみえる。"
        "きんきだいがく、ちばこうぎょうだいがく、とうようだいがくは、"
        "しがんしゃすうというみえやすいすうじでひょうかのへんかをしめしています。"
    ),
    "rank_10": (
        "だいじゅうい、とうきょうとしだいがく。りこうけいぷらすとしりょういき。"
        "おやせだいのいんしょう、むさしこうだいのりこうけいいめえじ。"
        "いまのひょうか、とし、かんきょう、じょうほうまでひろがるじつがくけいだいがく。"
        "おやせだいには、むさしこうだいというりこうけいのいんしょうがのこりやすいだいがくです。"
        "いまはとしせいかつ、かんきょう、じょうほう、けんちくなど、しゃかいかだいにちかいりょういきまでみえかたがひろがっています。"
        "なまえのへんこうだけでなく、りこうけいのどだいをげんだいてきなじつがくへせつぞくしているてんをひょうかしました。"
        "こんきょ、とし、かんきょう、じょうほうりょういきへひろがるじつがくけいぶらんど。"
    ),
    "rank_09": (
        "だいきゅうい、こくがくいんだいがく。でんとうこうのさいひょうか。"
        "おやせだいのいんしょう、ぶんがく、しんとうのでんとうこう。"
        "いまのひょうか、しぶやりっちとけんじつしゅうしょくでさいひょうか。"
        "おやせだいにはぶんがく、しんとう、にほんぶんかのでんとうこうといういめえじがつよいだいがくです。"
        "げんざいはしぶやというりっち、じんぶんけいのあつみ、ほう、けいざい、かんこうけいのてんかいで、"
        "けんじつなそうごうだいがくとしてみられています。"
        "はでなかいかくではなく、でんとうをいまのしんろかちへつなげなおしているてんがへんかです。"
        "こんきょ、しぶやりっちとでんとうぶんやのさいひょうか。"
    ),
    "rank_08": (
        "だいはちい、かなざわこうぎょうだいがく。ぴいびいえる、じっせんきょういく。"
        "おやせだいのいんしょう、ちほうのこうぎょうだいがく。"
        "いまのひょうか、ぴいびいえるがたのじっせんきょういくでひょうか。"
        "ちほうのこうぎょうだいがくというみられかたから、じっせんがたえんじにあきょういくのだいがくへいんしょうがかわっています。"
        "ぷろじぇくとでざいんきょういくのように、かだいはっけんからせっけい、じっそうまでをまなぶしくみがとくちょうです。"
        "きぎょうがもとめるじつむせつぞくがたのまなびとあいしょうがよく、"
        "おやせだいのたんじゅんなちめいどひょうかでははかりにくいだいがくです。"
        "こんきょ、ぷろじぇくとでざいんきょういく、ぴいびいえるがたのじっせんきょういく。"
    ),
    "rank_07": (
        "だいなない、むさしのだいがく。しんがくぶかいかく。"
        "おやせだいのいんしょう、じょしだい、ぶんけいちゅうしんのいんしょう。"
        "いまのひょうか、ええあい、でえたさいえんすももつそうごうだいがく。"
        "おやせだいにはじょしだい、ぶんけいちゅうしんといういんしょうがのこりやすいだいがくです。"
        "いまはええあい、でえたさいえんす、あんとれぷれなあしっぷ、さすてなびりてぃなど、あたらしいまなびのてんかいがはやいです。"
        "こうめいいめえじとじっさいのがくぶこうせいのさがおおきく、ひょうかがかわっただいがくとしていれています。"
        "こんきょ、でえたさいえんすがくぶ、ええあい、びっぐでえたきょういく。"
    ),
    "rank_06": (
        "だいろくい、とうきょうでんきだいがく。しゅうしょくないていりつ、きゅうじゅうきゅうてんにぱあせんと。"
        "おやせだいのいんしょう、でんき、こうがくのせんもんこう。"
        "いまのひょうか、めえかあ、あいてぃいにつよいぎじゅつしゃだいがく。"
        "でんき、こうがくのせんもんこうといういんしょうはいまもつよいですが、"
        "げんだいではあいてぃい、めえかあ、じょうほうけいじんざいへのひょうかにつながっています。"
        "にせんにじゅうごねんさんがつそつぎょうせい、しゅうりょうせいのしゅうしょくないていりつは、"
        "きゅうじゅうきゅうてんにぱあせんと。"
        "きゅうじんしゃすうは、いちまんななせんごひゃくよんじゅうごしゃというきぎょうせってんがおおきなこんきょです。"
        "じみにみえるぎじゅつけいだいがくほど、しゅうしょくしじょうでのひょうかがみなおされやすくなっています。"
        "こんきょ、にせんにじゅうごねんさんがつそつ、しゅうしょくないていりつきゅうじゅうきゅうてんにぱあせんと、"
        "きゅうじんしゃすういちまんななせんごひゃくよんじゅうごしゃ。"
    ),
    "rank_05": (
        "だいごい、めいじょうだいがく。じつしゅうしょくりつにつよい。"
        "おやせだいのいんしょう、ちゅうぶのだいきぼしだい。"
        "いまのひょうか、じつしゅうしょくりつでぜんこくきゅうのひょうか。"
        "ちゅうぶのだいきぼしだいといういんしょうから、しゅうしょくじっせきでぜんこくてきにみられるだいがくへへんかしています。"
        "がくぶそつぎょうせいにせんにんいじょうのだいがくで、じつしゅうしょくりつらんきんぐじゅうごねんれんぞくぜんこくなんばあわんというじっせきがつよいです。"
        "だいがくめいのぜんこくてきなはでさより、そつぎょうごのせいかをすうじでしめせるてんをひょうかしました。"
        "こんきょ、じつしゅうしょくりつらんきんぐ、じゅうごねんれんぞくぜんこくなんばあわん。"
    ),
    "rank_04": (
        "だいよんい、しばうらこうぎょうだいがく。りこうけいぶらんどじょうしょう。"
        "おやせだいのいんしょう、じみなこうぎょうだいがく。"
        "いまのひょうか、しゅとけんりこうけいのゆうりょくこう。"
        "おやせだいにはじみなこうぎょうだいがくといういんしょうをもたれがちでした。"
        "げんざいはしゅとけんりこうけいのゆうりょくこうとして、りこうけいにんき、こくさいせい、きぎょうひょうかのめんでそんざいかんがあります。"
        "たいむずはいああえでゅけえしょんにほんだいがくらんきんぐ、にせんにじゅうごで、"
        "そうごうさんじゅうにい、しりつなないというがいぶひょうかも、みかたのへんかをささえています。"
        "こんきょ、たいむずはいああえでゅけえしょんにほんだいがくらんきんぐにせんにじゅうご、そうごうさんじゅうにい、しりつなない。"
    ),
    "rank_03": (
        "だいさんい、とうようだいがく。しがんしゃすう、ぜんこくよんい。"
        "おやせだいのいんしょう、ちゅうけんしだいのいっかく。"
        "いまのひょうか、しゅとけんのにんきそうごうだいがく。"
        "ちゅうけんしだいのいっかくというみかたから、しゅとけんのにんきそうごうだいがくというみかたへかわっています。"
        "にせんにじゅうごねんどのしがんしゃすうは、じゅういちまんさんぜんななひゃくろくじゅうにめいで、しりつだいがくぜんこくよんいです。"
        "きゃんぱすりっち、がくぶきぼ、じゅけんせいからのえらばれかたが、おやせだいのいめえじをこうしんしています。"
        "こんきょ、にせんにじゅうごねんどしがんしゃすう、じゅういちまんさんぜんななひゃくろくじゅうにめい、しりつだいがくぜんこくよんい。"
    ),
    "rank_02": (
        "だいにい、きんきだいがく。そうしがんしゃ、にじゅうさんまんにんちょう。"
        "おやせだいのいんしょう、かんさいのだいきぼしだい。"
        "いまのひょうか、じつがく、こうほう、かいかくのぜんこくぶらんど。"
        "かんさいのだいきぼしだいといういんしょうから、じつがく、こうほう、かいかくのぜんこくぶらんどへかわっています。"
        "にせんにじゅうろくねんどいっぱんにゅうしのそうしがんしゃすうは、にじゅうさんまんよんせんにひゃくよんじゅうごにんで、かこさいたです。"
        "すいさん、いりょう、じょうほう、けんちくなどのじつがくしょくにくわえ、つたえかたのつよさもひょうかをおしあげています。"
        "こんきょ、にせんにじゅうろくねんどいっぱんにゅうし、そうしがんしゃすうにじゅうさんまんよんせんにひゃくよんじゅうごにん、かこさいた。"
    ),
    "rank_01": (
        "だいいちい、ちばこうぎょうだいがく。にせんにじゅうご、しだいしがんしゃいちい。"
        "おやせだいのいんしょう、こうぎょうけいのたんかだいがくいめえじ。"
        "いまのひょうか、ええあい、うちゅう、はんどうたいでしがんしゃすうとっぷきゅう。"
        "こうぎょうけいのたんかだいがくといういんしょうから、ええあい、うちゅう、はんどうたいでちゅうもくされるだいがくへかわっています。"
        "にせんにじゅうごねんどいっぱんせんばつのしがんしゃすうは、じゅうろくまんにせんごにんで、しりつだいがくいちいです。"
        "じだいがもとめるりょういきにだいがくのうちだしがかみあい、おやせだいのちめいどひょうかをおおきくこえています。"
        "こんきょ、にせんにじゅうごねんどいっぱんせんばつ、しがんしゃすうじゅうろくまんにせんごにん、しりつだいがくいちい。"
    ),
    "common_patterns": (
        "ひょうかがかわるだいがくのきょうつうてん。"
        "むかしのちめいどではなく、いまのしゃかいにあうまなびをつくれている。"
        "ええあい、でえた、はんどうたい、とし、かんきょうなど、しゃかいにいずにちょっけつするりょういきをのばしています。"
        "しゅうしょくじっせき、しがんしゃすう、がいぶらんきんぐなど、へんかをすうじでしめせるだいがくがつよいです。"
        "おやせだいのこうめいいめえじをこえるだけの、ぐたいてきなかいかくすとおりいがあります。"
    ),
    "update_view": (
        "おやせだいのみかたをあっぷでえとする。"
        "だいがくめいだけでなく、のびているりゆうをみる。"
        "だいがくえらびでは、むかしのへんさちじょれつだけでなく、いまのがくぶこうせいとしゅうしょくのつよさをみるべきです。"
        "とくにりこうけい、じょうほうけい、じつがくけいは、しゃかいのへんかによってひょうかがうごきやすいりょういきです。"
        "おやせだいのあんしんかんと、げんだいのじつりょくひょうかをわけてかんがえることがたいせつです。"
    ),
    "closing": (
        "けつろん。だいがくえらびはいまのりゆうをみるじだいへ。"
        "なまえのいんしょうより、のびているこんきょをかくにんする。"
        "このらんきんぐは、だいがくのゆうれつではなく、ひょうかのへんかをかしかするためのものです。"
        "おやせだいのあんしんかんと、いまのじつりょくひょうかをわけてみることがたいせつです。"
    ),
}


def run(cmd: list[str], *, quiet: bool = True) -> None:
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL if quiet else None,
        stderr=subprocess.DEVNULL if quiet else None,
    )


def duration(path: Path) -> float:
    res = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(res.stdout.strip())


def http_bytes(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None, timeout: int = 180) -> bytes:
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read()


def http_json(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None, timeout: int = 180) -> Any:
    body = http_bytes(url, data=data, headers=headers, timeout=timeout).decode("utf-8", errors="replace")
    return json.loads(body)


def local_engine_available(engine_url: str) -> bool:
    try:
        http_bytes(f"{engine_url.rstrip('/')}/version", timeout=2)
        return True
    except Exception:
        return False


def normalize_text_line(line: str) -> str:
    text = " ".join(line.replace("\n", "、").split())
    text = text.replace(":", "、").replace("/", "、")
    text = text.replace("TOP10", "トップテン")
    text = text.replace("PBL", "ピー ビー エル")
    text = text.replace("THE日本大学ランキング", "タイムズ ハイヤー エデュケーション日本大学ランキング")
    text = text.replace("AI", "エーアイ")
    return text


def slide_text(slide: dict[str, Any]) -> str:
    slug = slide.get("slug")
    if slug in HIRAGANA_TEXT_BY_SLUG:
        return HIRAGANA_TEXT_BY_SLUG[slug]
    lines = [normalize_text_line(line) for line in slide["visible_text"] if normalize_text_line(line)]
    joined = "。".join(line.rstrip("。") for line in lines)
    if not joined.endswith("。"):
        joined += "。"
    return joined


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def synthesize_local(engine_url: str, text: str, out: Path) -> None:
    base = engine_url.rstrip("/")
    query = urllib.parse.urlencode({"text": text, "speaker": SPEAKER_ID})
    audio_query = http_json(f"{base}/audio_query?{query}", data=b"", timeout=180)
    audio_query["speedScale"] = 1.06
    audio_query["pitchScale"] = 0.02
    audio_query["intonationScale"] = 1.18
    audio_query["volumeScale"] = 1.0
    audio_query["prePhonemeLength"] = 0.12
    audio_query["postPhonemeLength"] = 0.18
    body = json.dumps(audio_query, ensure_ascii=False).encode("utf-8")
    synth_query = urllib.parse.urlencode({"speaker": SPEAKER_ID})
    wav = http_bytes(
        f"{base}/synthesis?{synth_query}",
        data=body,
        headers={"Content-Type": "application/json"},
        timeout=300,
    )
    out.write_bytes(wav)


def get_ttsquest_json(url: str) -> dict[str, Any]:
    try:
        return http_json(url, timeout=180)
    except JSONDecodeError:
        # The public API occasionally returns a truncated status payload. Treat it as a transient wait state.
        return {"success": False, "retryAfter": 8, "transientJsonError": True}
    except (TimeoutError, urllib.error.URLError):
        return {"success": False, "retryAfter": 15, "transientNetworkError": True}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except Exception:
            data = {"success": False, "status": e.code, "body": body}
        if e.code == 429:
            data.setdefault("retryAfter", 30)
            return data
        raise


def download_with_retries(url: str, out: Path) -> None:
    last_error: Exception | None = None
    for _ in range(12):
        try:
            out.write_bytes(http_bytes(url, timeout=240))
            if out.stat().st_size > 1000:
                return
        except (TimeoutError, urllib.error.URLError) as e:
            last_error = e
        time.sleep(10)
    raise TimeoutError(f"VOICEVOX audio download failed: {last_error}")


def synthesize_ttsquest(text: str, out: Path) -> None:
    query = urllib.parse.urlencode({"text": text, "speaker": SPEAKER_ID})
    url = f"{TTS_QUEST}?{query}"

    for _ in range(30):
        data = get_ttsquest_json(url)
        if data.get("success"):
            status_url = data["audioStatusUrl"]
            wav_url = data["wavDownloadUrl"]
            break
        retry = int(data.get("retryAfter", 20))
        time.sleep(max(8, retry))
    else:
        raise TimeoutError("VOICEVOX synthesis request was not accepted.")

    for _ in range(120):
        status = get_ttsquest_json(status_url)
        if status.get("isAudioReady"):
            download_with_retries(wav_url, out)
            return
        if status.get("isAudioError"):
            raise RuntimeError(f"VOICEVOX synthesis failed: {text[:80]}")
        time.sleep(2)
    raise TimeoutError(f"VOICEVOX synthesis timed out: {text[:80]}")


def normalize_audio(src: Path, out: Path) -> None:
    if out.exists() and out.stat().st_size > 1000:
        return
    run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(src),
            "-ar",
            "44100",
            "-ac",
            "1",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11,volume=1.08",
            str(out),
        ]
    )


def make_silence(out: Path, seconds: float) -> None:
    run(
        [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=mono:sample_rate=44100",
            "-t",
            f"{seconds:.3f}",
            "-c:a",
            "pcm_s16le",
            str(out),
        ]
    )


def make_padded_audio(audio: Path, out: Path, total_seconds: float) -> None:
    audio_dur = duration(audio)
    silence = BUILD / f"{out.stem}_silence.wav"
    make_silence(silence, max(0.05, total_seconds - audio_dur))
    concat = BUILD / f"{out.stem}_concat.txt"
    concat.write_text(
        f"file '{audio.resolve().as_posix()}'\nfile '{silence.resolve().as_posix()}'\n",
        encoding="utf-8",
    )
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c:a", "pcm_s16le", str(out)])


def make_segment(image: Path, audio: Path, out: Path, seconds: float) -> None:
    run(
        [
            FFMPEG,
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(image),
            "-i",
            str(audio),
            "-t",
            f"{seconds:.3f}",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-vf",
            "scale=1920:1080,format=yuv420p",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out),
        ]
    )


def synthesize_slide(provider: str, engine_url: str, text: str, index: int) -> Path:
    digest = text_hash(text)
    raw = BUILD / f"voicevox_slide_{index:02d}_{digest}_raw.wav"
    norm = BUILD / f"voicevox_slide_{index:02d}_{digest}_norm.wav"
    if not raw.exists() or raw.stat().st_size < 1000:
        if provider == "local":
            synthesize_local(engine_url, text, raw)
        else:
            synthesize_ttsquest(text, raw)
        time.sleep(1.2)
    normalize_audio(raw, norm)
    return norm


def build_video(args: argparse.Namespace) -> dict[str, Any]:
    BUILD.mkdir(exist_ok=True)
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides = manifest["slides"]

    provider = args.provider
    if provider == "auto":
        provider = "local" if local_engine_available(args.engine_url) else "ttsquest"

    parts: list[Path] = []
    audio_parts: list[Path] = []
    meta_slides: list[dict[str, Any]] = []
    current = 0.0

    for slide in slides:
        idx = int(slide["index"])
        text = slide_text(slide)
        print(f"[{idx + 1:02d}/{len(slides):02d}] synthesize {slide['slug']}", flush=True)
        voice = synthesize_slide(provider, args.engine_url, text, idx)
        voice_dur = duration(voice)
        pad = 0.65 if idx < len(slides) - 1 else 0.35
        clip_dur = max(float(slide["duration"]), voice_dur + pad)
        padded = BUILD / f"voicevox_slide_{idx:02d}_padded.wav"
        make_padded_audio(voice, padded, clip_dur)

        segment = BUILD / f"voicevox_slide_{idx:02d}.mp4"
        make_segment(Path(slide["image"]), padded, segment, clip_dur)
        parts.append(segment)
        audio_parts.append(padded)
        meta_slides.append(
            {
                "index": idx,
                "slug": slide["slug"],
                "start": round(current, 3),
                "end": round(current + clip_dur, 3),
                "duration": round(clip_dur, 3),
                "original_duration": slide["duration"],
                "audio_duration": round(voice_dur, 3),
                "text": text,
                "image": slide["image"],
            }
        )
        current += clip_dur

    concat = BUILD / "voicevox_video_concat.txt"
    concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    out = Path(args.output)
    run(
        [
            FFMPEG,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(out),
        ],
        quiet=False,
    )

    audio_concat = BUILD / "voicevox_audio_concat.txt"
    audio_concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in audio_parts), encoding="utf-8")
    narration = DIST / "voicevox_tsumugi_8min_synced_narration.wav"
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(audio_concat), "-c:a", "pcm_s16le", str(narration)])

    meta = {
        "speaker": "VOICEVOX:春日部つむぎ",
        "speaker_id": SPEAKER_ID,
        "provider": provider,
        "duration": round(duration(out), 3),
        "slide_count": len(slides),
        "output": str(out),
        "narration_wav": str(narration),
        "manifest": str(manifest_path),
        "slides": meta_slides,
    }
    Path(args.metadata).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="8分版スライドにVOICEVOX春日部つむぎ音声をスライド単位で同期します。")
    p.add_argument("--manifest", default=str(DIST / "slides_8min_no_voice_manifest.json"))
    p.add_argument("--output", default=str(DIST / "oyasedai_hyouka_daigaku_8min_voicevox_tsumugi_synced.mp4"))
    p.add_argument("--metadata", default=str(DIST / "voicevox_tsumugi_8min_synced_metadata.json"))
    p.add_argument("--provider", choices=["auto", "local", "ttsquest"], default="auto")
    p.add_argument("--engine-url", default=LOCAL_ENGINE)
    return p


def main() -> None:
    args = parser().parse_args()
    meta = build_video(args)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
