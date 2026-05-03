from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

from moviepy.editor import concatenate_videoclips

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_video_motion import DIST, Scene, scene_clip  # noqa: E402


ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build_openai_tts"
FFMPEG = "/opt/anaconda3/bin/ffmpeg"
FFPROBE = "/opt/anaconda3/bin/ffprobe"

MODEL = os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
VOICE = os.environ.get("OPENAI_TTS_VOICE", "coral")
API_URL = "https://api.openai.com/v1/audio/speech"
INSTRUCTIONS = (
    "日本語の落ち着いた女性ナレーター。"
    "受験・教育系YouTubeの解説として、明瞭で自然、少し知的で聞き疲れしないテンポ。"
    "数字と大学名は丁寧に読み、煽りすぎず、信頼感のあるトーンで話す。"
)


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
            f"{seconds:.3f}",
            "-c:a",
            "pcm_s16le",
            str(out),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def synthesize(text: str, idx: int) -> Path:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY が未設定です。APIキーを環境変数に設定してから再実行してください。")

    payload = {
        "model": MODEL,
        "voice": VOICE,
        "input": text,
        "instructions": INSTRUCTIONS,
        "response_format": "wav",
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    raw = BUILD / f"openai_tts_scene_{idx:02d}.wav"
    with urllib.request.urlopen(req, timeout=180) as res:
        raw.write_bytes(res.read())

    normalized = BUILD / f"openai_tts_scene_{idx:02d}_norm.wav"
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(raw),
            "-ar",
            "44100",
            "-ac",
            "1",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            str(normalized),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return normalized


def build_scenes(ranking: list[dict]):
    ranking = sorted(ranking, key=lambda x: x["rank"], reverse=True)
    scenes = [
        (
            Scene("title", 1, seed=1),
            "親世代が知っている大学の評価と、いま受験生が見ている評価は、かなり変わっています。",
        ),
        (
            Scene("method", 1, seed=2),
            "今回は偏差値だけではなく、志願者数、就職実績、学部改革、親世代のイメージからの変化幅で見ていきます。",
        ),
    ]
    for item in ranking:
        text = f"第{item['rank']}位、{item['name']}。{item['old']}から、{item['now']}へ。"
        scenes.append((Scene("rank", 1, data=item, seed=10 + item["rank"]), text))
    scenes.append(
        (
            Scene("final", 1, seed=30),
            "大学選びは、名前の印象よりも、いま伸びている理由を見る時代です。",
        )
    )
    return scenes


def main():
    BUILD.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    ranking = json.loads((DIST / "ranking.json").read_text(encoding="utf-8"))
    scene_specs = build_scenes(ranking)

    audio_parts = []
    clips = []
    meta_scenes = []

    for idx, (scene, narration) in enumerate(scene_specs):
        wav = synthesize(narration, idx)
        wav_dur = duration(wav)
        pad = 0.55 if idx < len(scene_specs) - 1 else 0.35
        scene.duration = max(wav_dur + pad, 3.0)
        silence = BUILD / f"openai_tts_silence_{idx:02d}.wav"
        make_silence(silence, scene.duration - wav_dur)
        audio_parts.extend([wav, silence])
        clips.append(scene_clip(scene))
        meta_scenes.append({"index": idx, "kind": scene.kind, "duration": round(scene.duration, 3), "text": narration})

    concat_audio = BUILD / "openai_tts_audio_concat.txt"
    concat_audio.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in audio_parts), encoding="utf-8")
    narration_wav = DIST / "openai_gpt4o_mini_tts_narration_synced.wav"
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_audio), "-c:a", "pcm_s16le", str(narration_wav)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    video = concatenate_videoclips(clips, method="compose")
    silent_mp4 = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking_openai_tts_silent_synced.mp4"
    video.write_videofile(
        str(silent_mp4),
        fps=24,
        codec="libx264",
        preset="medium",
        audio=False,
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )

    out = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking_openai_gpt4o_mini_tts.mp4"
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(silent_mp4),
            "-i",
            str(narration_wav),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
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
        "model": MODEL,
        "voice": VOICE,
        "instructions": INSTRUCTIONS,
        "duration": round(duration(out), 3),
        "scenes": meta_scenes,
        "output": str(out),
    }
    (DIST / "openai_gpt4o_mini_tts_synced_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
