# 動画・音声圧縮スクリプト

FFmpegを使用した動画・音声圧縮用Pythonスクリプト（動画: SVT-AV1コーデック、音声: MP3コーデック）。

## 機能

### 動画圧縮

- **最大解像度**: 4K (3840x2160)
- **コーデック**: SVT-AV1（高速AV1コーデック）
- **CRF（品質）**: デフォルト25（0-63、低い値=高品質、高い値=小さいファイルサイズ）
- **オーディオコーデック**: AAC
- **オーディオビットレート**: 最大320kbps
- **最大FPS**: 120fps

### 音声圧縮（MP3）

- **対応フォーマット**: MP3, WAV, FLAC, AAC, M4A, OGG, WMA, APE, ALAC
- **コーデック**: libmp3lame（LAME MP3エンコーダー）
- **ビットレート**: 32k - 320kbps
- **メタデータ**: 元のメタデータ（タイトル、アーティスト等）を保持

### 共通機能

- **進捗表示**: ETA、FPS、速度インジケーター付きのリアルタイムプログレスバー

## 前提条件

このスクリプトを使用するには、以下が必要です：

### FFmpegのインストール

**オプション1: システム全体へのインストール**

**Windows:**

1. [公式ウェブサイト](https://ffmpeg.org/download.html)からFFmpegをダウンロード
2. ディレクトリに展開して配置（例：`C:\ffmpeg`）
3. FFmpegのbinディレクトリをシステムPATHに追加（例：`C:\ffmpeg\bin`）
4. インストール確認: `ffmpeg -version` と `ffprobe -version`

**またはChocolateyを使用:**

```powershell
choco install ffmpeg
```

**またはwingetを使用:**

```powershell
winget install ffmpeg
```

**macOS:**

```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install ffmpeg
```

**オプション2: ローカルFFmpeg（ポータビリティ推奨）**

FFmpegの実行ファイルをスクリプトと同じディレクトリに配置できます：

- Windows: `ffmpeg.exe` と `ffprobe.exe`
- macOS/Linux: `ffmpeg` と `ffprobe`

スクリプトは、ローカルの実行ファイルが存在する場合、自動的に検出して使用します。

## 使用方法

### 基本的な動画圧縮

```bash
python compress_video.py input_video.mp4
```

出力ファイルは自動的に `input_video_compressed.mp4` として作成されます。

### 基本的な音声圧縮（MP3へ）

```bash
python compress_video.py music.mp3 --audio-bitrate 128k
```

出力ファイルは自動的に `music_compressed.mp3` として作成されます。

対応音声フォーマット: `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma`, `.ape`, `.alac`

### インタラクティブモード（入力ファイル未指定時）

入力ファイルを指定せずにスクリプトを実行すると、パスの入力を求められます：

```bash
python compress_video.py
```

```text
Enter the path to the video file to compress: input_video.mp4
```

> **注意**: スクリプトは自動的にファイルパスの前後のダブルクォートを削除するため、`"C:\Videos\my video.mp4"` のようなパスも正しく動作します。

### 出力ファイル名を指定

```bash
python compress_video.py input_video.mp4 -o output_video.mp4
```

### CRF値の変更（品質調整）

```bash
python compress_video.py input_video.mp4 --crf 23
```

- CRF 0-23: 高品質（ファイルサイズ大）
- CRF 25: デフォルト（品質とサイズのバランス）
- CRF 26-40: 中品質
- CRF 40-63: 低品質（ファイルサイズ小）

### オーディオビットレートの変更（動画）

```bash
python compress_video.py input_video.mp4 --audio-bitrate 256k
```

### 音声圧縮の使用例

```bash
# MP3を128kbpsに圧縮
python compress_video.py music.mp3 --audio-bitrate 128k

# WAVをMP3に変換
python compress_video.py audio.wav --audio-bitrate 192k

# FLACをMP3に変換（出力先指定）
python compress_video.py song.flac -o compressed.mp3
```

### オーディオを無効化

```bash
python compress_video.py input_video.mp4 --no-audio
```

### 解像度を制限

```bash
python compress_video.py input_video.mp4 --resolution 1920x1080
```

### FPSを制限

```bash
python compress_video.py input_video.mp4 --fps 30
```

### 全オプションの組み合わせ

```bash
python compress_video.py input_video.mp4 -o output_video.mp4 --crf 23 --audio-bitrate 256k --resolution 1920x1080 --fps 60
```

## オプション

| オプション | 説明 | デフォルト値 |
| - | - | - |
| `input` | 入力動画/音声ファイルパス（任意、未指定時は入力を求められます） | - |
| `-o`, `--output` | 出力ファイルパス | 動画: `{入力ファイル名}_compressed.{拡張子}`, 音声: `{入力ファイル名}_compressed.mp3` |
| `--crf` | AV1 CRF値（0-63、動画のみ） | 25 |
| `--audio-bitrate` | オーディオビットレート（動画: 最大320k、音声: 32k-320k） | 192k |
| `--no-audio` | オーディオトラックを無効化（動画のみ） | オーディオ有効 |
| `--fps` | 最大FPS（最大: 120、動画のみ） | 元のFPS |
| `--resolution` | WxH形式の最大解像度（例: 1920x1080、動画のみ） | 3840x2160 |

## ヘルプ

```bash
python compress_video.py --help
```

## 機能詳細

### 解像度制限

- 元の動画が4K（3840x2160）を超える場合、アスペクト比を維持したまま縮小されます
- 解像度が制限内の場合、元の解像度が保持されます
- `--resolution`でカスタム解像度制限を設定できます

### FPS制限

- 元の動画のFPSが指定された最大値を超える場合、削減されます
- デフォルトの最大値は120fpsです
- FPSが制限内の場合、元のFPSが保持されます

### SVT-AV1コーデック

- Intelが開発した高速AV1エンコーダー
- libaom-av1と比較して10-100倍高速なエンコード
- 高い圧縮効率を持つ最新の動画圧縮規格
- CRFモードエンコード（品質ベースの可変ビットレート）
- 自動マルチスレッド対応

### オーディオ処理（動画）

- AAC形式に変換
- 最大320kbpsビットレート
- `--no-audio`で無効化可能

### 音声圧縮（音声ファイル）

- 各种音声フォーマットをMP3に変換
- libmp3lameエンコーダーを使用（高品質MP3）
- ビットレート範囲: 32k - 320kbps
- メタデータ（タイトル、アーティスト、アルバム等）を保持
- 拡張子に基づく自動ファイルタイプ判定

### 進捗表示

圧縮中、リアルタイムのプログレスバーが表示されます：

- ビジュアルバー付きの進捗パーセンテージ
- 現在時間 / 合計時間
- ETA（推定残り時間）
- エンコードFPS
- 速度倍率
- フレーム数

## 使用例

### 8K動画を4Kに圧縮

```bash
python compress_video.py 8k_video.mp4 -o compressed_4k.mp4
```

出力: 解像度は3840x2160以下に縮小されます

### Web用に圧縮（1080p、30fps）

```bash
python compress_video.py video.mp4 --resolution 1920x1080 --fps 30
```

### 高品質圧縮

```bash
python compress_video.py video.mp4 --crf 20 --audio-bitrate 320k
```

### ファイルサイズ優先

```bash
python compress_video.py video.mp4 --crf 35 --audio-bitrate 128k
```

### 動画のみ（オーディオなし）

```bash
python compress_video.py video.mp4 --no-audio
```

### 音声圧縮の使用例

```bash
# 高ビットレートMP3を圧縮
python compress_video.py high_quality.mp3 --audio-bitrate 128k

# ロスレスFLACをMP3に変換
python compress_video.py lossless.flac --audio-bitrate 320k

# WAVをMP3に変換
python compress_video.py recording.wav --audio-bitrate 192k
```

## 注意事項

- AV1エンコードはCPU負荷が高いため、高解像度動画の処理には時間がかかる場合があります
- エンコード中にCtrl+Cを押すと処理を中断できます
+ 出力ファイルが既に存在する場合、確認なしで上書きされます

## トラブルシューティング

### `FFmpeg not found` エラー

- FFmpegが正しくインストールされていることを確認してください
- FFmpegがシステムPATHに含まれていることを確認してください
- または、`ffmpeg`と`ffprobe`の実行ファイルをスクリプトディレクトリに配置してください
- コマンドラインで `ffmpeg -version` を実行して確認してください

### 動画/音声情報取得エラー

- 入力ファイルが存在することを確認してください
- ファイルが破損していないか確認してください
- ファイルが有効な動画または音声形式であることを確認してください

### サポートされていないファイルタイプエラー

- ファイル拡張子を確認してください
- 対応動画形式: `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.ts`, `.mts`, `.m2ts`
- 対応音声形式: `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma`, `.ape`, `.alac`

### プログレスバーが表示されない

- プログレスバーには動画の長さ情報が必要です
- 一部の動画形式では長さのメタデータが提供されない場合があります
- 圧縮は正常に完了します

## ライセンス

このスクリプトは自由に使用、改変、配布できます。
