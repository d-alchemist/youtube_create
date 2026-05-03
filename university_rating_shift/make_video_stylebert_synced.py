from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build_stylebert"
FFMPEG = "/opt/anaconda3/bin/ffmpeg"
FFPROBE = "/opt/anaconda3/bin/ffprobe"
FPS = 24


@dataclass
class StyleBertConfig:
    server_url: str = "http://127.0.0.1:5000"
    model_id: int | None = None
    model_name: str | None = None
    speaker_id: int | None = None
    speaker_name: str | None = None
    style: str | None = None
    preferred_model_keywords: list[str] = field(default_factory=list)
    preferred_speaker_keywords: list[str] = field(default_factory=list)
    preferred_style_keywords: list[str] = field(default_factory=list)
    style_weight: float = 1.0
    sdp_ratio: float = 0.25
    noise: float = 0.6
    noisew: float = 0.8
    length: float = 0.95
    language: str = "JP"
    auto_split: bool = True
    split_interval: float = 0.35
    assist_text: str | None = None
    assist_text_weight: float = 1.0
    reference_audio_path: str | None = None
    encoding: str | None = None
    api_key: str | None = None
    api_key_header: str = "Authorization"
    timeout: int = 180
    validate_voice: bool = True


@dataclass
class VoiceSelection:
    model_id: int | None
    model_name: str | None
    speaker_id: int | None
    speaker_name: str | None
    speaker_label: str | None
    style: str | None


ENV_ALIASES = {
    "server_url": ("STYLEBERTVITS2_SERVER_URL",),
    "model_id": ("STYLEBERTVITS2_MODEL_ID", "NEXT_PUBLIC_STYLEBERTVITS2_MODEL_ID"),
    "model_name": ("STYLEBERTVITS2_MODEL_NAME",),
    "speaker_id": ("STYLEBERTVITS2_SPEAKER_ID",),
    "speaker_name": ("STYLEBERTVITS2_SPEAKER_NAME",),
    "style": ("STYLEBERTVITS2_STYLE", "NEXT_PUBLIC_STYLEBERTVITS2_STYLE"),
    "preferred_model_keywords": ("STYLEBERTVITS2_PREFERRED_MODEL_KEYWORDS",),
    "preferred_speaker_keywords": ("STYLEBERTVITS2_PREFERRED_SPEAKER_KEYWORDS",),
    "preferred_style_keywords": ("STYLEBERTVITS2_PREFERRED_STYLE_KEYWORDS",),
    "style_weight": ("STYLEBERTVITS2_STYLE_WEIGHT",),
    "sdp_ratio": ("STYLEBERTVITS2_SDP_RATIO", "NEXT_PUBLIC_STYLEBERTVITS2_SDP_RATIO"),
    "noise": ("STYLEBERTVITS2_NOISE",),
    "noisew": ("STYLEBERTVITS2_NOISEW",),
    "length": ("STYLEBERTVITS2_LENGTH", "NEXT_PUBLIC_STYLEBERTVITS2_LENGTH"),
    "language": ("STYLEBERTVITS2_LANGUAGE",),
    "split_interval": ("STYLEBERTVITS2_SPLIT_INTERVAL",),
    "assist_text": ("STYLEBERTVITS2_ASSIST_TEXT",),
    "assist_text_weight": ("STYLEBERTVITS2_ASSIST_TEXT_WEIGHT",),
    "reference_audio_path": ("STYLEBERTVITS2_REFERENCE_AUDIO_PATH",),
    "encoding": ("STYLEBERTVITS2_ENCODING",),
    "api_key": ("STYLEBERTVITS2_API_KEY",),
    "api_key_header": ("STYLEBERTVITS2_API_KEY_HEADER",),
    "timeout": ("STYLEBERTVITS2_TIMEOUT",),
}

INT_FIELDS = {"model_id", "speaker_id", "timeout"}
FLOAT_FIELDS = {
    "style_weight",
    "sdp_ratio",
    "noise",
    "noisew",
    "length",
    "split_interval",
    "assist_text_weight",
}
BOOL_FIELDS = {"auto_split", "validate_voice"}
LIST_FIELDS = {"preferred_model_keywords", "preferred_speaker_keywords", "preferred_style_keywords"}

PRESETS = {
    "tsumugi-female": {
        "preferred_model_keywords": ["つむぎ", "tsumugi", "女性", "female", "girl"],
        "preferred_speaker_keywords": ["つむぎ", "tsumugi", "女性", "female", "girl"],
        "preferred_style_keywords": ["Neutral", "通常", "ノーマル", "Talk", "Normal"],
        "style_weight": 0.9,
        "sdp_ratio": 0.28,
        "noise": 0.48,
        "noisew": 0.68,
        "length": 0.93,
        "split_interval": 0.3,
        "assist_text": (
            "若い女性の自然なナレーション。明るく親しみやすいが軽すぎず、"
            "教育系YouTubeとして滑舌が明瞭。春日部つむぎ系の聞き取りやすさと、"
            "落ち着いたニュース解説の信頼感を両立する。"
        ),
        "assist_text_weight": 0.7,
    }
}


def coerce_value(name: str, value: Any) -> Any:
    if value is None:
        return None
    if name in LIST_FIELDS:
        if isinstance(value, list):
            return [str(item) for item in value if str(item)]
        return [item.strip() for item in str(value).split(",") if item.strip()]
    if name in INT_FIELDS:
        return int(value)
    if name in FLOAT_FIELDS:
        return float(value)
    if name in BOOL_FIELDS:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
    return str(value)


def env_config() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, env_names in ENV_ALIASES.items():
        for env_name in env_names:
            raw = os.environ.get(env_name)
            if raw not in (None, ""):
                values[key] = coerce_value(key, raw)
                break
    return values


def load_config_file(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    config_path = Path(path).expanduser()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"設定JSONはオブジェクトにしてください: {config_path}")
    allowed = {f.name for f in fields(StyleBertConfig)}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise SystemExit(f"未対応の設定キーがあります: {', '.join(unknown)}")
    return {key: coerce_value(key, value) for key, value in data.items()}


def merge_config(args: argparse.Namespace) -> StyleBertConfig:
    values = asdict(StyleBertConfig())
    if args.preset:
        values.update(PRESETS[args.preset])
    values.update(env_config())
    values.update(load_config_file(args.config))
    cli_values = {
        "server_url": args.server_url,
        "model_id": args.model_id,
        "model_name": args.model_name,
        "speaker_id": args.speaker_id,
        "speaker_name": args.speaker_name,
        "style": args.style,
        "preferred_model_keywords": coerce_value("preferred_model_keywords", args.preferred_model_keywords)
        if args.preferred_model_keywords is not None
        else None,
        "preferred_speaker_keywords": coerce_value("preferred_speaker_keywords", args.preferred_speaker_keywords)
        if args.preferred_speaker_keywords is not None
        else None,
        "preferred_style_keywords": coerce_value("preferred_style_keywords", args.preferred_style_keywords)
        if args.preferred_style_keywords is not None
        else None,
        "style_weight": args.style_weight,
        "sdp_ratio": args.sdp_ratio,
        "noise": args.noise,
        "noisew": args.noisew,
        "length": args.length,
        "language": args.language,
        "split_interval": args.split_interval,
        "assist_text": args.assist_text,
        "assist_text_weight": args.assist_text_weight,
        "reference_audio_path": args.reference_audio_path,
        "encoding": args.encoding,
        "api_key": args.api_key,
        "api_key_header": args.api_key_header,
        "timeout": args.timeout,
    }
    values.update({key: value for key, value in cli_values.items() if value is not None})
    if args.auto_split is not None:
        values["auto_split"] = args.auto_split
    if args.no_validate_voice:
        values["validate_voice"] = False
    values["server_url"] = values["server_url"].rstrip("/")
    return StyleBertConfig(**values)


def auth_headers(config: StyleBertConfig) -> dict[str, str]:
    if not config.api_key:
        return {}
    if config.api_key_header.lower() == "authorization":
        value = config.api_key if config.api_key.lower().startswith("bearer ") else f"Bearer {config.api_key}"
        return {"Authorization": value}
    return {config.api_key_header: config.api_key}


def request_bytes(config: StyleBertConfig, path: str, method: str = "GET") -> bytes:
    req = urllib.request.Request(
        f"{config.server_url}{path}",
        data=b"" if method == "POST" else None,
        headers=auth_headers(config),
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=config.timeout) as res:
            return res.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(str(e.reason)) from e


def http_json(config: StyleBertConfig, path: str, method: str = "GET") -> dict[str, Any]:
    return json.loads(request_bytes(config, path, method).decode("utf-8"))


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


def first_int_key(values: dict[str, Any]) -> int:
    return int(sorted(values.keys(), key=lambda x: int(x))[0])


def contains_keyword(value: str, keywords: list[str]) -> bool:
    text = value.lower()
    return any(keyword.lower() in text for keyword in keywords)


def preferred_model_id(models: dict[str, Any], keywords: list[str]) -> int | None:
    if not keywords:
        return None
    for model_id, info in sorted(models.items(), key=lambda item: int(item[0])):
        candidates = [
            Path(str(info.get("model_path", ""))).parent.name,
            Path(str(info.get("config_path", ""))).parent.name,
            str(info.get("model_path", "")),
            str(info.get("config_path", "")),
        ]
        if any(contains_keyword(candidate, keywords) for candidate in candidates):
            return int(model_id)
    return None


def preferred_speaker_id(speakers: dict[str, Any], keywords: list[str]) -> int | None:
    if not keywords:
        return None
    for speaker_id, speaker_name in sorted(speakers.items(), key=lambda item: int(item[0])):
        if contains_keyword(str(speaker_name), keywords):
            return int(speaker_id)
    return None


def preferred_style_name(styles: dict[str, Any], keywords: list[str]) -> str | None:
    if not keywords:
        return None
    for keyword in keywords:
        for style_name in styles:
            if style_name.lower() == keyword.lower():
                return style_name
    for style_name in styles:
        if contains_keyword(style_name, keywords):
            return style_name
    return None


def resolve_voice(config: StyleBertConfig, models: dict[str, Any]) -> VoiceSelection:
    if config.model_name:
        matches = [
            int(model_id)
            for model_id, info in models.items()
            if Path(str(info.get("config_path", ""))).parent.name == config.model_name
            or Path(str(info.get("model_path", ""))).parent.name == config.model_name
        ]
        model_id = matches[0] if len(matches) == 1 else config.model_id
        model_name = config.model_name
    else:
        model_id = config.model_id
        if model_id is None:
            model_id = preferred_model_id(models, config.preferred_model_keywords)
        if model_id is None:
            model_id = first_int_key(models)
        model_name = None

    if model_id is None:
        raise SystemExit(f"model_name={config.model_name} に一致するモデルを特定できません。--list-voicesで確認してください。")
    model_key = str(model_id)
    if model_key not in models:
        raise SystemExit(f"model_id={model_id} が /models/info にありません。--list-voicesで確認してください。")

    info = models[model_key]
    styles = info.get("style2id") or {}
    if config.style:
        style = config.style
        if config.validate_voice and style not in styles:
            raise SystemExit(f"style={style} が model_id={model_id} にありません。候補: {', '.join(styles.keys())}")
    else:
        style = preferred_style_name(styles, config.preferred_style_keywords)
        if style is None:
            style = "Neutral" if "Neutral" in styles else next(iter(styles.keys()), None)

    if config.speaker_name:
        speaker_name = config.speaker_name
        speaker_id = None
        speaker_label = speaker_name
        spk2id = info.get("spk2id") or {}
        if config.validate_voice and speaker_name not in spk2id:
            raise SystemExit(f"speaker_name={speaker_name} が model_id={model_id} にありません。候補: {', '.join(spk2id.keys())}")
    else:
        id2spk = info.get("id2spk") or {}
        speaker_id = config.speaker_id
        if speaker_id is None:
            speaker_id = preferred_speaker_id(id2spk, config.preferred_speaker_keywords)
        if speaker_id is None:
            speaker_id = first_int_key(id2spk)
        speaker_name = None
        speaker_label = id2spk.get(str(speaker_id))
        if config.validate_voice and str(speaker_id) not in id2spk:
            raise SystemExit(f"speaker_id={speaker_id} が model_id={model_id} にありません。候補: {', '.join(id2spk.keys())}")

    return VoiceSelection(
        model_id=model_id,
        model_name=model_name,
        speaker_id=speaker_id,
        speaker_name=speaker_name,
        speaker_label=speaker_label,
        style=style,
    )


def voice_params(config: StyleBertConfig, voice: VoiceSelection, text: str) -> dict[str, str]:
    params: dict[str, str] = {
        "text": text,
        "style_weight": str(config.style_weight),
        "sdp_ratio": str(config.sdp_ratio),
        "noise": str(config.noise),
        "noisew": str(config.noisew),
        "length": str(config.length),
        "language": config.language,
        "auto_split": str(config.auto_split).lower(),
        "split_interval": str(config.split_interval),
    }
    if voice.model_name:
        params["model_name"] = voice.model_name
    elif voice.model_id is not None:
        params["model_id"] = str(voice.model_id)
    if voice.speaker_name:
        params["speaker_name"] = voice.speaker_name
    elif voice.speaker_id is not None:
        params["speaker_id"] = str(voice.speaker_id)
    if voice.style:
        params["style"] = voice.style
    if config.assist_text:
        params["assist_text"] = config.assist_text
        params["assist_text_weight"] = str(config.assist_text_weight)
    if config.reference_audio_path:
        params["reference_audio_path"] = config.reference_audio_path
    if config.encoding:
        params["encoding"] = config.encoding
    return params


def synthesize(config: StyleBertConfig, voice: VoiceSelection, text: str, idx: int) -> Path:
    query = urllib.parse.urlencode(voice_params(config, voice, text))
    raw = BUILD / f"stylebert_scene_{idx:02d}.wav"
    raw.write_bytes(request_bytes(config, f"/voice?{query}", method="POST"))

    normalized = BUILD / f"stylebert_scene_{idx:02d}_norm.wav"
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


def build_scenes(ranking: list[dict[str, Any]], scene_cls: type) -> list[tuple[Any, str]]:
    ranking = sorted(ranking, key=lambda x: x["rank"], reverse=True)
    scenes = [
        (
            scene_cls("title", 1, seed=1),
            "親世代が知っている大学の評価と、いま受験生が見ている評価は、かなり変わっています。",
        ),
        (
            scene_cls("method", 1, seed=2),
            "偏差値だけでは見えない、志願者数、就職実績、学部改革、印象差で見ていきます。",
        ),
    ]
    for item in ranking:
        text = f"第{item['rank']}位、{item['name']}。{item['old']}から、{item['now']}へ。"
        scenes.append((scene_cls("rank", 1, data=item, seed=10 + item["rank"]), text))
    scenes.append(
        (
            scene_cls("final", 1, seed=30),
            "大学選びは、名前の印象よりも、伸びている理由を見る時代です。",
        )
    )
    return scenes


def print_voice_list(models: dict[str, Any]):
    for model_id, info in sorted(models.items(), key=lambda item: int(item[0])):
        model_path = Path(str(info.get("model_path", "")))
        config_path = Path(str(info.get("config_path", "")))
        model_name = model_path.parent.name or config_path.parent.name or "(unknown)"
        speakers = info.get("id2spk") or {}
        styles = info.get("style2id") or {}
        print(f"model_id={model_id} model_name={model_name}")
        print("  speakers: " + ", ".join(f"{sid}:{name}" for sid, name in sorted(speakers.items(), key=lambda x: int(x[0]))))
        print("  styles: " + ", ".join(styles.keys()))


def render_video(config: StyleBertConfig, voice: VoiceSelection) -> dict[str, Any]:
    from moviepy.editor import concatenate_videoclips
    from make_video_motion import Scene, scene_clip

    ranking = json.loads((DIST / "ranking.json").read_text(encoding="utf-8"))
    scene_specs = build_scenes(ranking, Scene)

    audio_parts: list[Path] = []
    clips = []
    meta_scenes = []

    for idx, (scene, narration) in enumerate(scene_specs):
        wav = synthesize(config, voice, narration, idx)
        wav_dur = duration(wav)
        pad = 0.55 if idx < len(scene_specs) - 1 else 0.35
        scene.duration = max(wav_dur + pad, 3.2)
        silence = BUILD / f"stylebert_silence_{idx:02d}.wav"
        make_silence(silence, scene.duration - wav_dur)
        audio_parts.extend([wav, silence])
        clips.append(scene_clip(scene))
        meta_scenes.append(
            {
                "index": idx,
                "kind": scene.kind,
                "duration": round(scene.duration, 3),
                "audio_duration": round(wav_dur, 3),
                "text": narration,
            }
        )

    concat_audio = BUILD / "stylebert_audio_concat.txt"
    concat_audio.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in audio_parts), encoding="utf-8")
    narration_wav = DIST / "stylebert_vits2_narration_synced.wav"
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_audio), "-c:a", "pcm_s16le", str(narration_wav)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    video = concatenate_videoclips(clips, method="compose")
    silent_mp4 = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking_stylebert_silent_synced.mp4"
    video.write_videofile(
        str(silent_mp4),
        fps=FPS,
        codec="libx264",
        preset="medium",
        audio=False,
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )

    out = DIST / "oyasedai_hyouka_ga_kawatta_daigaku_ranking_stylebert_vits2.mp4"
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

    return {
        "config": {key: value for key, value in asdict(config).items() if key != "api_key"},
        "voice": asdict(voice),
        "duration": round(duration(out), 3),
        "narration_wav": str(narration_wav),
        "output": str(out),
        "main_output": str(main_out),
        "scenes": meta_scenes,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Style-Bert-VITS2 APIでナレーションを作り、音声尺に同期した動画を生成します。"
    )
    parser.add_argument("--preset", choices=sorted(PRESETS), help="声質・パラメータのプリセット。")
    parser.add_argument("--config", help="Style-Bert-VITS2設定JSON。CLI指定が最優先です。")
    parser.add_argument("--server-url", help="Style-Bert-VITS2 APIの接続先。例: http://127.0.0.1:5000")
    parser.add_argument("--model-id", type=int, help="/models/info の model_id。")
    parser.add_argument("--model-name", help="model_assets内のモデル名。指定時はmodel_idより優先されます。")
    parser.add_argument("--speaker-id", type=int, help="話者ID。")
    parser.add_argument("--speaker-name", help="話者名。指定時はspeaker_idより優先されます。")
    parser.add_argument("--style", help="音声スタイル。例: Neutral, Happy")
    parser.add_argument("--preferred-model-keywords", help="モデル自動選択キーワード。カンマ区切り。")
    parser.add_argument("--preferred-speaker-keywords", help="話者自動選択キーワード。カンマ区切り。")
    parser.add_argument("--preferred-style-keywords", help="スタイル自動選択キーワード。カンマ区切り。")
    parser.add_argument("--style-weight", type=float, help="スタイルの強さ。")
    parser.add_argument("--sdp-ratio", type=float, help="SDP/DP混合比。")
    parser.add_argument("--noise", type=float, help="サンプルノイズ。")
    parser.add_argument("--noisew", type=float, help="SDPノイズ。")
    parser.add_argument("--length", type=float, help="話速。1より大きいほど遅く、長くなります。")
    parser.add_argument("--language", help="読み上げ言語。通常は JP。")
    parser.add_argument("--auto-split", dest="auto_split", action="store_true", default=None, help="改行分割を有効化。")
    parser.add_argument("--no-auto-split", dest="auto_split", action="store_false", help="改行分割を無効化。")
    parser.add_argument("--split-interval", type=float, help="分割時に挟む無音秒数。")
    parser.add_argument("--assist-text", help="声音・感情の補助テキスト。")
    parser.add_argument("--assist-text-weight", type=float, help="補助テキストの強さ。")
    parser.add_argument("--reference-audio-path", help="参照音声パス。")
    parser.add_argument("--encoding", help="Style-Bert-VITS2側でtextをURLデコードするエンコーディング。")
    parser.add_argument("--api-key", help="RunPod等で必要なAPIキー。")
    parser.add_argument("--api-key-header", help="APIキーを入れるヘッダー名。既定はAuthorization。")
    parser.add_argument("--timeout", type=int, help="APIタイムアウト秒。")
    parser.add_argument("--no-validate-voice", action="store_true", help="/models/infoでの話者・スタイル検証を省略。")
    parser.add_argument("--list-voices", action="store_true", help="/models/infoを取得してモデル・話者・スタイル一覧を表示。")
    return parser


def main():
    args = build_arg_parser().parse_args()
    config = merge_config(args)
    BUILD.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)

    try:
        models = http_json(config, "/models/info")
    except Exception as e:
        raise SystemExit(
            "Style-Bert-VITS2 APIに接続できません。"
            f" server_url={config.server_url} を確認してください。元エラー: {e}"
        )

    if args.list_voices:
        print_voice_list(models)
        return

    voice = resolve_voice(config, models)
    meta = render_video(config, voice)
    (DIST / "stylebert_vits2_synced_metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
