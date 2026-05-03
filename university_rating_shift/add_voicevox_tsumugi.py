from __future__ import annotations

import json
import subprocess
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build_voicevox"
FFMPEG = "/opt/anaconda3/bin/ffmpeg"
FFPROBE = "/opt/anaconda3/bin/ffprobe"


SPEAKER_ID = 8  # VOICEVOX:春日部つむぎ


LINES = [
    "親世代が知っている大学の評価と、いま受験生が見ている評価は、かなり変わっています。今回は、偏差値だけでは見えない、評価が変わった大学ランキングです。評価軸は、志願者数、就職実績、学部改革、そして親世代のイメージからの変化幅です。",
    "第10位、東京都市大学。武蔵工大の理工系イメージから、都市、環境、情報まで広がる実学系大学へ。第9位、國學院大學。文学と神道の伝統校という印象から、渋谷立地と堅実就職で再評価されています。第8位、金沢工業大学。地方の工業大学という見方から、実践型エンジニア教育で評価を上げています。",
    "第7位、武蔵野大学。女子大、文系中心の印象から、AI、データサイエンスも持つ総合大学へ。第6位、東京電機大学。電機、工学の専門校から、メーカー、ITに強い技術者大学へ。第5位、名城大学。中部の大規模私大という印象から、実就職率で全国級の評価を得ています。",
    "第4位、芝浦工業大学。地味な工業大学という印象から、首都圏理工系の有力校へ。第3位、東洋大学。中堅私大の一角から、首都圏の人気総合大学へ。第2位、近畿大学。関西の大規模私大から、実学、広報、改革の全国ブランドへ変わっています。",
    "第1位、千葉工業大学。工業系の単科大学イメージから、AI、宇宙、半導体で志願者数トップ級の大学へ。上位校に共通するのは、昔の知名度ではなく、いまの社会が求める学びを早く形にしていることです。大学選びは、名前の印象よりも、伸びている理由を見る時代です。",
]


def get_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=90) as res:
            return json.loads(res.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except Exception:
            data = {"success": False, "retryAfter": 30, "status": e.code, "body": body}
        if e.code == 429:
            data.setdefault("success", False)
            data.setdefault("retryAfter", 30)
            return data
        raise


def download(url: str, out: Path):
    with urllib.request.urlopen(url, timeout=120) as res:
        out.write_bytes(res.read())


def synthesize_line(text: str, idx: int) -> Path:
    encoded = urllib.parse.urlencode({"text": text, "speaker": SPEAKER_ID})
    url = f"https://api.tts.quest/v3/voicevox/synthesis?{encoded}"
    wav = BUILD / f"tsumugi_{idx:02d}.wav"

    # The public API may ask callers to slow down. Respect retryAfter.
    while True:
        data = get_json(url)
        if data.get("success"):
            status_url = data["audioStatusUrl"]
            wav_url = data["wavDownloadUrl"]
            break
        retry = int(data.get("retryAfter", 15))
        time.sleep(max(5, retry))

    for _ in range(90):
        status = get_json(status_url)
        if status.get("isAudioReady"):
            download(wav_url, wav)
            return wav
        if status.get("isAudioError"):
            raise RuntimeError(f"VOICEVOX synthesis failed for line {idx}: {text}")
        time.sleep(2)
    raise TimeoutError(f"VOICEVOX synthesis timed out for line {idx}: {text}")


def duration(path: Path) -> float:
    res = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(res.stdout.strip())


def make_silence(out: Path, seconds: float):
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=mono:sample_rate=44100",
            "-t",
            f"{seconds:.2f}",
            "-c:a",
            "pcm_s16le",
            str(out),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    BUILD.mkdir(exist_ok=True)
    wavs = []
    for i, line in enumerate(LINES):
        wav = synthesize_line(line, i)
        wavs.append(wav)
        # API courtesy pause.
        time.sleep(2)

    spaced = []
    for i, wav in enumerate(wavs):
        converted = BUILD / f"segment_{i:02d}.wav"
        subprocess.run(
            [
                FFMPEG,
                "-y",
                "-i",
                str(wav),
                "-ar",
                "44100",
                "-ac",
                "1",
                "-af",
                "volume=1.15,loudnorm=I=-16:TP=-1.5:LRA=11",
                str(converted),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        spaced.append(converted)
        silence = BUILD / f"silence_{i:02d}.wav"
        make_silence(silence, 0.55 if i < len(wavs) - 1 else 0.2)
        spaced.append(silence)

    concat = BUILD / "voicevox_concat.txt"
    concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in spaced), encoding="utf-8")
    voice = DIST / "voicevox_kasukabe_tsumugi_narration.wav"
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c:a", "pcm_s16le", str(voice)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    video = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking_motion_no_voice.mp4"
    out = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking_voicevox_tsumugi.mp4"

    # Keep the video length. If narration is shorter, pad silence; if longer, let the video continue with final frame not needed,
    # so trim audio to video duration.
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(video),
            "-i",
            str(voice),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-af",
            "apad",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out),
        ],
        check=True,
    )
    main_out = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking.mp4"
    main_out.write_bytes(out.read_bytes())

    meta = {
        "speaker": "VOICEVOX:春日部つむぎ",
        "speaker_id": SPEAKER_ID,
        "voice_duration_seconds": round(duration(voice), 3),
        "video_duration_seconds": round(duration(out), 3),
        "output": str(out),
    }
    (DIST / "voicevox_kasukabe_tsumugi_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
