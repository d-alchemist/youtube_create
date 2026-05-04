from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build_bgm"
FFMPEG = "/opt/anaconda3/bin/ffmpeg"
FFPROBE = "/opt/anaconda3/bin/ffprobe"

BGM_ROOT = Path(
    "/Users/mikitooba/Library/CloudStorage/GoogleDrive-mikimiki.4on@gmail.com/"
    "マイドライブ/Mic/著作権/BGM"
)
BGM_TRACKS = [
    BGM_ROOT / "clear-vision.mp3",
    BGM_ROOT / "smooth-optimization.mp3",
    BGM_ROOT / "algorithm-symphony.mp3",
]


def duration(path: Path) -> float:
    res = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(res.stdout.strip())


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def make_bgm_bed(target_seconds: float, out: Path) -> None:
    fade = 4.0
    fade_out_start = max(0.0, target_seconds - fade)
    filter_complex = (
        "[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
        "afade=t=in:st=0:d=3,asetpts=PTS-STARTPTS[a0];"
        "[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,asetpts=PTS-STARTPTS[a1];"
        "[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,asetpts=PTS-STARTPTS[a2];"
        f"[a0][a1]acrossfade=d={fade}:c1=tri:c2=tri[x1];"
        f"[x1][a2]acrossfade=d={fade}:c1=tri:c2=tri,"
        f"atrim=0:{target_seconds:.3f},afade=t=out:st={fade_out_start:.3f}:d={fade},volume=0.5[bgm]"
    )
    run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(BGM_TRACKS[0]),
            "-i",
            str(BGM_TRACKS[1]),
            "-i",
            str(BGM_TRACKS[2]),
            "-filter_complex",
            filter_complex,
            "-map",
            "[bgm]",
            "-c:a",
            "pcm_s16le",
            str(out),
        ]
    )


def mix(video: Path, bgm: Path, out: Path) -> None:
    run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(video),
            "-i",
            str(bgm),
            "-filter_complex",
            "[0:a]volume=1.0[voice];"
            "[1:a]volume=1.0[bgm];"
            "[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2,"
            "alimiter=limit=0.95[aout]",
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(out),
        ]
    )


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    src = DIST / "oyasedai_hyouka_daigaku_8min_voicevox_tsumugi_synced.mp4"
    bgm = DIST / "selected_bgm_clear_smooth_algorithm_50pct.wav"
    out = DIST / "oyasedai_hyouka_daigaku_8min_voicevox_tsumugi_synced_bgm.mp4"
    target_seconds = duration(src)
    make_bgm_bed(target_seconds, bgm)
    mix(src, bgm, out)
    meta = {
        "input_video": str(src),
        "output": str(out),
        "duration": round(duration(out), 3),
        "bgm_wav": str(bgm),
        "bgm_volume": "50%",
        "fade_seconds": 4,
        "tracks": [str(path) for path in BGM_TRACKS],
    }
    (DIST / "voicevox_tsumugi_bgm_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
