# 親世代と評価が変わった大学ランキング 制作仕様

このディレクトリは、データの錬金術師向けの「大学ランキング解説動画」を同じ品質で再生成するための制作レシピです。

## 仕上がり

- テーマ: 親世代と評価が変わった大学ランキング TOP10
- 画面: 1920x1080 / ネオン系データ番組デザイン
- 構成: 18スライド
- 無音スライド版: 約8分
- ナレーション入り版: スライド文章を読み切る尺に自動調整
- 音声: VOICEVOX 春日部つむぎ
- BGM: Google Drive の `Mic/著作権/BGM/` から選曲し、50%音量でミックス

## 主要ファイル

- `make_15min_slides_no_voice.py`
  - 現在は `TARGET_LABEL = "8min"` の8分版生成スクリプトです。
  - ファイル名は過去互換のままですが、出力は8分版です。
- `make_8min_slides_voicevox_tsumugi_synced.py`
  - スライド単位でVOICEVOX音声を生成し、音声尺に合わせて動画を再構成します。
  - `HIRAGANA_TEXT_BY_SLUG` で読み間違いが出やすい語をひらがな送信用に固定します。
- `add_bgm_to_voicevox_video.py`
  - 選んだBGMをフェード接続し、50%音量でナレーションにミックスします。
- `dist/ranking.json`
  - ランキング本体のデータです。
- `dist/description.txt`
  - YouTube概要欄です。

## 再生成手順

```bash
python3 university_rating_shift/make_15min_slides_no_voice.py
python3 university_rating_shift/make_8min_slides_voicevox_tsumugi_synced.py --provider ttsquest
python3 university_rating_shift/add_bgm_to_voicevox_video.py
```

ローカルVOICEVOX Engineを使う場合は、Engineを起動したうえで次のようにします。

```bash
python3 university_rating_shift/make_8min_slides_voicevox_tsumugi_synced.py --provider local --engine-url http://127.0.0.1:50021
```

## VOICEVOX読み指定

VOICEVOXには、原則としてスライド本文をそのまま送らず、`HIRAGANA_TEXT_BY_SLUG` の読み用テキストを送信します。

特に固定している読み:

- 親世代: `おやせだい`
- 國學院大學: `こくがくいんだいがく`
- AI: `ええあい`
- PBL: `ぴいびいえる`
- THE日本大学ランキング: `たいむずはいああえでゅけえしょんにほんだいがくらんきんぐ`

新しい企画に流用する場合は、固有名詞、英字、数字、大学名を必ずひらがな読みにしてからVOICEVOXへ送ります。

## デザイン仕様

- 背景: 黒、濃紺、ブルーのサイバー空間
- 左上: 赤いページカウンター
- 右上: `DATA ALCHEMIST` ロゴ
- 本文カード: 青ネオン枠、黒塗り、黄色の番号バッジ
- 強調バッジ: 金色グラデーション
- 注意書き: 下部に小さく表示

タイトルスライドのD案文言:

- 金色バッジ: `意外と知らない大学評価の変化`
- 1番カード: `名前のイメージではなく、いま選ばれている理由に注目します。`

## BGM仕様

使用曲:

- `clear-vision.mp3`
- `smooth-optimization.mp3`
- `algorithm-symphony.mp3`

処理:

- 曲間は4秒クロスフェード
- 冒頭は3秒フェードイン
- 末尾は4秒フェードアウト
- BGM音量は50%
- ナレーションとミックス後にリミッターを適用

## 品質チェック

最低限、以下を確認します。

```bash
python3 -m py_compile university_rating_shift/make_15min_slides_no_voice.py
python3 -m py_compile university_rating_shift/make_8min_slides_voicevox_tsumugi_synced.py
python3 -m py_compile university_rating_shift/add_bgm_to_voicevox_video.py
jq '[.slides[] | select(.duration < .audio_duration)] | length' university_rating_shift/dist/voicevox_tsumugi_8min_synced_metadata.json
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 university_rating_shift/dist/oyasedai_hyouka_daigaku_8min_voicevox_tsumugi_synced_bgm.mp4
```

同期チェックが `0` なら、読み終わる前に次のスライドへ進む箇所はありません。

## Google Drive納品先

完成版は以下へ保存します。

`GoogleDrive/マイドライブ/Codex専用/親世代と評価が変わった大学ランキング/voicevox_tsumugi_synced_bgm/`

主な納品物:

- `oyasedai_hyouka_daigaku_8min_voicevox_tsumugi_synced_bgm.mp4`
- `thumbnail_final_D.jpg`
- `thumbnail_final_D.png`
- `description.txt`
- `voicevox_tsumugi_8min_synced_metadata.json`
- `voicevox_tsumugi_bgm_metadata.json`
