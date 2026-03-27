#import "/.typst/A4-Ame-Serif.typ": *
#show: a4_ame_init

= 動画/音声圧縮スクリプト

FFmpegとSVT-AV1コーデック（動画）およびMP3コーデック（音声）を使用した動画・音声圧縮用Pythonスクリプト。

最新の内容はREADME.mdファイルに記載されています。

== 機能

=== 動画圧縮

- 最大解像度: 4K (3840x2160)
- コーデック: SVT-AV1（高速AV1コーデック）
- CRF（品質）: デフォルト25（0-63、低い値=高品質、高い値=小さいファイルサイズ）
- オーディオコーデック: AAC
- オーディオビットレート: 最大320kbps
- 最大FPS: 120fps

=== 音声圧縮（MP3）

- 対応形式: MP3, WAV, FLAC, AAC, M4A, OGG, WMA, APE, ALAC
- コーデック: libmp3lame（LAME MP3エンコーダー）
- ビットレート: 32k - 320kbps
- メタデータ: 元のメタデータを保持（タイトル、アーティストなど）

=== 共通機能

- 進捗表示: ETA、FPS、速度インジケーター付きのリアルタイムプログレスバー
- 音量調整: 自動または手動の音量ゲインで音声の明瞭性を向上
- ノイズ除去: バックグラウンドノイズを低減するオーディオノイズ除去フィルター

#pagebreak()

== 前提条件

このスクリプトを使用するには、以下が必要です：

=== FFmpegのインストール

*オプション1: システム全体へのインストール*

*Windows:*

1. #link("https://ffmpeg.org/download.html")[公式ウェブサイト]からFFmpegをダウンロード
2. ディレクトリに展開して配置（例：`C:\ffmpeg`）
3. FFmpegのbinディレクトリをシステムPATHに追加（例：`C:\ffmpeg\bin`）
4. インストールを確認：`ffmpeg -version` と `ffprobe -version`

*またはChocolateyを使用:*

```powershell
choco install ffmpeg
```

*またはwingetを使用:*

```powershell
winget install ffmpeg
```

*macOS:*

```bash
brew install ffmpeg
```

*Linux (Ubuntu/Debian):*

```bash
sudo apt update
sudo apt install ffmpeg
```

*オプション2: ローカルFFmpeg（ポータビリティ推奨）*

FFmpegの実行ファイルをスクリプトと同じディレクトリに配置できます：

- Windows: `ffmpeg.exe` と `ffprobe.exe`
- macOS/Linux: `ffmpeg` と `ffprobe`

ローカルの実行ファイルが存在する場合、スクリプトは自動的に検出して使用します。

#pagebreak()

== 使用方法

=== 基本的な動画圧縮

```bash
python compress_video.py input_video.mp4
```

出力ファイルは自動的に `input_video_compressed.mp4` として作成されます。

=== 基本的な音声圧縮（MP3へ）

```bash
python compress_video.py music.mp3 --audio-bitrate 128k
```

出力ファイルは自動的に `music_compressed.mp3` として作成されます。

対応音声形式: `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma`, `.ape`, `.alac`

=== インタラクティブモード（入力ファイル未指定時）

入力ファイルを指定せずにスクリプトを実行すると、パスの入力を求められます：

```bash
python compress_video.py
```

```text
Enter the path to the video file to compress: input_video.mp4
```

#quote[
  注意: スクリプトは自動的にファイルパスの前後のダブルクォートを削除するため、`"C:\Videos\my video.mp4"` のようなパスも正しく動作します。
]

=== 出力ファイル名を指定

```bash
python compress_video.py input_video.mp4 -o output_video.mp4
```

=== CRF値の変更（品質調整）

```bash
python compress_video.py input_video.mp4 --crf 23
```

- CRF 0-23: 高品質（ファイルサイズ大）
- CRF 25: デフォルト（品質とサイズのバランス）
- CRF 26-40: 中品質
- CRF 40-63: 低品質（ファイルサイズ小）

=== オーディオビットレートの変更（動画）

```bash
python compress_video.py input_video.mp4 --audio-bitrate 256k
```

=== 音声圧縮の例

```bash
# MP3を128kbpsに圧縮
python compress_video.py music.mp3 --audio-bitrate 128k

# WAVをMP3に変換
python compress_video.py audio.wav --audio-bitrate 192k

# FLACをMP3に変換（カスタム出力先）
python compress_video.py song.flac -o compressed.mp3
```

=== オーディオを無効化

```bash
python compress_video.py input_video.mp4 --no-audio
```

=== 解像度を制限

```bash
python compress_video.py input_video.mp4 --resolution 1920x1080
```

=== FPSを制限

```bash
python compress_video.py input_video.mp4 --fps 30
```

=== 音量調整

スクリプトは自動または手動の音量調整に対応し、音声の明瞭性を向上させます。

*音量解析のみ（圧縮なし）:*

```bash
python compress_video.py --analyze-volume
```

*自動音量調整:*

```bash
python compress_video.py meeting.mp4 --volume-gain auto
```

*手動音量調整（倍率）:*

```bash
python compress_video.py meeting.mp4 --volume-gain 2.0
```

*手動音量調整（dB）:*

```bash
python compress_video.py meeting.mp4 --volume-gain 10dB
```

=== ノイズ除去

バックグラウンドノイズを低減し、音声を明瞭にします。

*ノイズ除去を有効化（デフォルトレベル 0.15）:*

```bash
python compress_video.py meeting.mp4 --denoise
```

*カスタムノイズ除去レベル（0.0-1.0）:*

```bash
python compress_video.py meeting.mp4 --denoise 0.3
```

=== 音量調整とノイズ除去の組み合わせ

```bash
python compress_video.py meeting.mp4 --volume-gain auto --denoise 0.2
```

=== 全オプションの組み合わせ

```bash
python compress_video.py input_video.mp4 -o output_video.mp4 --crf 23 --audio-bitrate 256k --resolution 1920x1080 --fps 60
```

#pagebreak()

== オプション

#table(
  columns: (4fr, 6fr, 5fr),
  align: (left, left, left),
  stroke: none,
  table.hline(),
  [*オプション*], [*説明*], [*デフォルト値*],
  table.hline(stroke: 0.5pt),
  [`input`], [入力動画/音声ファイルパス（任意、未指定時は入力を求められます）], [-],
  [`-o`, `--output`],
  [出力ファイルパス],
  [動画: `{入力ファイル名}_compressed.{拡張子}`, 音声: `{入力ファイル名}_compressed.mp3`],
  [`--crf`], [AV1 CRF値（0-63、動画のみ）], [25],
  [`--audio-bitrate`], [オーディオビットレート（動画: 最大320k、音声: 32k-320k）], [192k],
  [`--no-audio`], [オーディオトラックを無効化（動画のみ）], [オーディオ有効],
  [`--fps`], [最大FPS（最大: 120、動画のみ）], [元のFPS],
  [`--resolution`], [WxH形式の最大解像度（例: 1920x1080、動画のみ）], [3840x2160],
  [`--volume-gain`], [音量ゲイン: 倍率（例: `2.0`）、dB（例: `10dB`）、または `auto`], [無効],
  [`--analyze-volume`], [音量レベルを解析し、推奨ゲインを表示（圧縮なし）], [無効],
  [`--denoise`], [オーディオノイズ除去を有効化（レベル: 0.0-1.0）], [無効],
  table.hline(),
)

== ヘルプ

```bash
python compress_video.py --help
```

#pagebreak()

== 機能詳細

=== 解像度制限

- 元の動画が4K（3840x2160）を超える場合、アスペクト比を維持したまま縮小されます
- 解像度が制限内の場合、元の解像度が保持されます
- `--resolution`でカスタム解像度制限を設定できます

=== FPS制限

- 元の動画のFPSが指定された最大値を超える場合、削減されます
- デフォルトの最大値は120fpsです
- FPSが制限内の場合、元のFPSが保持されます

=== SVT-AV1コーデック

- Intelが開発した高速AV1エンコーダー
- libaom-av1と比較して10-100倍高速なエンコード
- 高い圧縮効率を持つ最新の動画圧縮規格
- CRFモードエンコード（品質ベースの可変ビットレート）
- 自動マルチスレッド対応

=== オーディオ処理（動画）

- AAC形式に変換
- 最大320kbpsビットレート
- `--no-audio`で無効化可能

=== 音声圧縮（音声ファイル）

- 各种音声形式をMP3に変換
- libmp3lameエンコーダーを使用（高品質MP3）
- ビットレート範囲: 32k - 320kbps
- メタデータを保持（タイトル、アーティスト、アルバムなど）
- 拡張子に基づく自動ファイルタイプ検出

#pagebreak()

=== 進捗表示

圧縮中、リアルタイムのプログレスバーが表示されます：

- ビジュアルバー付きの進捗パーセンテージ
- 現在時間 / 合計時間
- ETA（推定残り時間）
- エンコードFPS
- 速度倍率
- フレーム数

=== 音量調整

スクリプトは音声レベルを解析し、明瞭性を向上させるために音量を自動調整できます：

- *自動モード*: 音声を解析し、ターゲット音量（-16dB）に到達するための最適なゲインを計算
- *倍率モード*: `2.0` のような倍率を指定して音量を2倍にする
- *dBモード*: `10dB` のようにデシベルでゲインを指定
- *解析のみ*: `--analyze-volume` を使用すると、圧縮せずに現在のレベルと推奨ゲインを表示

自動ゲイン計算は、最大音量レベルを考慮してクリッピングを防止します。

=== ノイズ除去

スクリプトはFFmpegの `afftdn` フィルターを使用してオーディオノイズを低減します：

- *レベル範囲*: 0.0（最小）から 1.0（最大）
- *デフォルトレベル*: 0.15（軽いノイズ除去）
- 値を高くするとノイズがより除去されますが、音質に影響する可能性があります

#pagebreak()

== 使用例

=== 8K動画を4Kに圧縮

```bash
python compress_video.py 8k_video.mp4 -o compressed_4k.mp4
```

出力: 解像度は3840x2160以下に縮小されます

=== Web用に圧縮（1080p、30fps）

```bash
python compress_video.py video.mp4 --resolution 1920x1080 --fps 30
```

=== 高品質圧縮

```bash
python compress_video.py video.mp4 --crf 20 --audio-bitrate 320k
```

=== ファイルサイズ優先

```bash
python compress_video.py video.mp4 --crf 35 --audio-bitrate 128k
```

=== 動画のみ（オーディオなし）

```bash
python compress_video.py video.mp4 --no-audio
```

=== 音声圧縮の例

```bash
# 高ビットレートMP3を圧縮
python compress_video.py high_quality.mp3 --audio-bitrate 128k

# ロスレスFLACをMP3に変換
python compress_video.py lossless.flac --audio-bitrate 320k

# WAVをMP3に変換
python compress_video.py recording.wav --audio-bitrate 192k
```

== 注意事項

- AV1エンコードはCPU負荷が高いため、高解像度動画の処理には時間がかかる場合があります
- エンコード中にCtrl+Cを押すと処理を中断できます
- 出力ファイルが既に存在する場合、自動的に上書きされます

== トラブルシューティング

=== `FFmpeg not found` エラー

- FFmpegが正しくインストールされていることを確認してください
- FFmpegがシステムPATHに含まれていることを確認してください
- または、`ffmpeg`と`ffprobe`の実行ファイルをスクリプトディレクトリに配置してください
- コマンドラインで `ffmpeg -version` を実行して確認してください

=== 動画/音声情報取得エラー

- 入力ファイルが存在することを確認してください
- ファイルが破損していないか確認してください
- ファイルが有効な動画または音声形式であることを確認してください

=== サポートされていないファイル形式エラー

- ファイル拡張子を確認してください
- 対応動画形式: `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.ts`, `.mts`, `.m2ts`
- 対応音声形式: `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma`, `.ape`, `.alac`

=== プログレスバーが表示されない

- プログレスバーには動画の長さ情報が必要です
- 一部の動画形式では長さのメタデータが提供されない場合があります
- 圧縮は正常に完了します
