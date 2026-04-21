# 動画・音声圧縮ツール

FFmpegを使用した動画・音声圧縮用Pythonツール（動画: SVT-AV1コーデック、音声: MP3コーデック）。CLIとGUIの両モードに対応しています。

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

- **バッチ処理**: 複数ファイルを一括で圧縮し、処理結果のサマリーを表示
- **進捗表示**: ETA、FPS、速度インジケーター付きのリアルタイムプログレスバー
- **音量調整**: 自動または手動での音量ゲイン調整で音声を聞き取りやすく
- **ノイズ除去**: 背景ノイズを低減するオーディオノイズフィルター
- **GUIモード**: ドラッグ＆ドロップ、ダーク/ライトテーマ、多言語対応（日本語/英語）の直感的なグラフィカルインターフェース

## クイックスタート

### GUIモード

```bash
python -m video_compressor --gui
```

GUIの機能:
- **ドラッグ＆ドロップ**: 動画/音声ファイルを直接ウィンドウにドロップ
- **サイドバーナビゲーション**: 動画、音声、設定の各ビューを切り替え
- **リアルタイム進捗**: プログレスバー、FPS、ETAで圧縮状況を確認
- **ダーク/ライトテーマ**: 設定から外観を切り替え
- **日本語/英語**: いつでも言語を切り替え可能

### CLIモード

```bash
python -m video_compressor input_video.mp4
```

すべてのオプションについては、下記の[CLI使用方法](#使用方法)を参照してください。

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

FFmpegの実行ファイルをプロジェクトの `bin` ディレクトリに配置できます：

- Windows: `bin/ffmpeg.exe` と `bin/ffprobe.exe`
- macOS/Linux: `bin/ffmpeg` と `bin/ffprobe`

スクリプトは、`bin` ディレクトリに実行ファイルが存在する場合、自動的に検出して使用します。

## 使用方法

### 基本的な動画圧縮

```bash
python -m video_compressor input_video.mp4
```

出力ファイルは自動的に `input_video_compressed.mp4` として作成されます。

### 基本的な音声圧縮（MP3へ）

```bash
python -m video_compressor music.mp3 --audio-bitrate 128k
```

出力ファイルは自動的に `music_compressed.mp3` として作成されます。

対応音声フォーマット: `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma`, `.ape`, `.alac`

### インタラクティブモード（入力ファイル未指定時）

入力ファイルを指定せずにスクリプトを実行すると、パスの入力を求められます：

```bash
python -m video_compressor
```

```text
Enter the path(s) to the file(s) to compress: input_video.mp4
```

> **注意**: スクリプトは自動的にファイルパスの前後のダブルクォートを削除するため、`"C:\Videos\my video.mp4"` のようなパスも正しく動作します。

### バッチ処理（複数ファイルの一括圧縮）

複数の入力パスを指定することで、複数ファイルを一括で圧縮できます。パスはスペース、カンマ、改行で区切って指定できます：

```bash
# スペース区切り
python -m video_compressor "file1.mp4" "file2.mp4" "file3.mp4"

# カンマ区切り
python -m video_compressor "file1.mp4", "file2.mp4", "file3.mp4"

# 出力ディレクトリを指定
python -m video_compressor file1.mp4 file2.mp4 -o /path/to/output_dir/
```

複数ファイル処理時の動作：

- 各ファイルの処理状況 `[1/3]`、`[2/3]`... が表示されます
- 1つのファイルが失敗しても、残りのファイルの処理は継続されます
- 処理完了後に成功/失敗件数のサマリーが表示されます

インタラクティブモードでも複数ファイルを入力できます：

```text
Enter the path(s) to the file(s) to compress: "C:\Videos\video1.mp4", "C:\Videos\video2.mp4"
```

### 出力ファイル名を指定

```bash
python -m video_compressor input_video.mp4 -o output_video.mp4
```

複数ファイル処理時はディレクトリを指定します：

```bash
# 既存のディレクトリに出力
python -m video_compressor file1.mp4 file2.mp4 -o /path/to/output_dir/

# 新しいディレクトリを作成して出力
python -m video_compressor file1.mp4 file2.mp4 -o /path/to/new_dir/
```

> **注意**: 複数ファイルの場合、`--output` にはディレクトリパスを指定してください。単一ファイルの場合はファイルパスでもディレクトリパスでも指定可能です。

### CRF値の変更（品質調整）

```bash
python -m video_compressor input_video.mp4 --crf 23
```

- CRF 0-23: 高品質（ファイルサイズ大）
- CRF 25: デフォルト（品質とサイズのバランス）
- CRF 26-40: 中品質
- CRF 40-63: 低品質（ファイルサイズ小）

### エンコードプリセットの変更

```bash
python -m video_compressor input_video.mp4 --preset 10
```

- Preset 0-4: エンコード速度が遅い、圧縮効率が高い（ファイルサイズ小）
- Preset 5-7: デフォルト（速度と圧縮のバランス）
- Preset 8-13: エンコード速度が速い、圧縮効率が低い（ファイルサイズ大）

### オーディオビットレートの変更（動画）

```bash
python -m video_compressor input_video.mp4 --audio-bitrate 256k
```

### 音声圧縮の使用例

```bash
# MP3を128kbpsに圧縮
python -m video_compressor music.mp3 --audio-bitrate 128k

# WAVをMP3に変換
python -m video_compressor audio.wav --audio-bitrate 192k

# FLACをMP3に変換（出力先指定）
python -m video_compressor song.flac -o compressed.mp3
```

### オーディオを無効化

```bash
python -m video_compressor input_video.mp4 --no-audio
```

### 解像度を制限

```bash
python -m video_compressor input_video.mp4 --resolution 1920x1080
```

### FPSを制限

```bash
python -m video_compressor input_video.mp4 --fps 30
```

### 音量調整

スクリプトは自動または手動での音量調整に対応しており、音声を聞き取りやすくします。

**音量解析のみ（圧縮なし）:**

```bash
python -m video_compressor --analyze-volume
```

**メディア解析のみ（圧縮なし）:**

```bash
python -m video_compressor --analyze input.mp4
```

このとき、以下のような詳細情報が表示されます：

- ファイル形式（コン名、短縮形）
- 再生時間
- ファイルサイズ
- 美品質
- ビットレート

各ストリーム（動画・音声）について：

- コーデック名（正式名・短縮形）
- プロファイル
- レベル
- 解像度
- アスペクト比
- フレームレート
- ビット深度
- ピクセルフォーマット
- 色空間
- 色範囲
- ビットレート
- HDR情報

音声ストリームについて

- コーデック名（正式名・短縮形）
- プロファイル
- サンプリングレート
- チャンネル数
- チャンネルレイアウト
- ビット深度
- ビットレート
- 言語

メタデータ（存在する場合）

- タイトル
- アーティスト
- アルバム
- 作成日時
- その他

**自動音量調整:**

```bash
python -m video_compressor meeting.mp4 --volume-gain auto
```

**手動音量調整（倍率指定）:**

```bash
python -m video_compressor meeting.mp4 --volume-gain 2.0
```

**手動音量調整（dB指定）:**

```bash
python -m video_compressor meeting.mp4 --volume-gain 10dB
```

### ノイズ除去

背景ノイズを低減し、クリアな音声にします。

**ノイズ除去を有効化（デフォルトレベル 0.15）:**

```bash
python -m video_compressor meeting.mp4 --denoise
```

**カスタムノイズ除去レベル（0.0-1.0）:**

```bash
python -m video_compressor meeting.mp4 --denoise 0.3
```

### 音量調整とノイズ除去の組み合わせ

```bash
python -m video_compressor meeting.mp4 --volume-gain auto --denoise 0.2
```

### 全オプションの組み合わせ

```bash
python -m video_compressor input_video.mp4 -o output_video.mp4 --crf 23 --audio-bitrate 256k --resolution 1920x1080 --fps 60
```

## オプション

| オプション | 説明 | デフォルト値 |
| - | - | - |
| `input` | 入力ファイルパス（複数可。スペース、カンマ、改行で区切り。任意、未指定時は入力を求められます） | - |
| `-o`, `--output` | 出力ファイルまたはディレクトリパス。複数ファイル時はディレクトリを指定。 | 動画: `{入力ファイル名}_compressed.{拡張子}`, 音声: `{入力ファイル名}_compressed.mp3` |
| `--crf` | AV1 CRF値（0-63、動画のみ） | 25 |
| `--preset` | エンコード速度プリセット（0-13、高い値=高速、動画のみ） | 6 |
| `--audio-bitrate` | オーディオビットレート（動画: 最大320k、音声: 32k-320k） | 192k |
| `--no-audio` | オーディオトラックを無効化（動画のみ） | オーディオ有効 |
| `--fps` | 最大FPS（最大: 120、動画のみ） | 元のFPS |
| `--resolution` | WxH形式の最大解像度（例: 1920x1080、動画のみ） | 3840x2160 |
| `--volume-gain` | 音量ゲイン: 倍率（例: `2.0`）、dB（例: `10dB`）、または `auto` | 無効 |
| `--analyze-volume` | 音量レベルを解析し推奨ゲインを表示（圧縮なし） | 無効 |
| `--analyze` | メディアファイルを解析し詳細情報を表示（コーデック、解像度、ビットレートなど） | 無効 |
| `--denoise` | オーディオノイズ除去を有効化（レベル: 0.0-1.0） | 無効 |

## ヘルプ

```bash
python -m video_compressor --help
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

### 音量調整

スクリプトは音声レベルを解析し、聞き取りやすくするために自動的に音量を調整できます：

- **自動モード**: 音声を解析し、目標音圧レベル（-16dB）に到達するための最適なゲインを計算
- **倍率モード**: `2.0` のような倍率を指定して音量を調整
- **dBモード**: `10dB` のようにデシベルで指定
- **解析のみ**: `--analyze-volume` を使用すると、圧縮せずに現在のレベルと推奨ゲインを表示

自動ゲイン計算では、最大音量レベルを考慮してクリッピング（音割れ）を防止します。

### ノイズ除去

スクリプトはFFmpegの `afftdn` フィルターを使用してオーディオノイズを低減します：

- **レベル範囲**: 0.0（最小）〜 1.0（最大）
- **デフォルトレベル**: 0.15（軽いノイズ除去）
- 値が大きいほどノイズを除去しますが、音質に影響する可能性があります

## 使用例

### 8K動画を4Kに圧縮

```bash
python -m video_compressor 8k_video.mp4 -o compressed_4k.mp4
```

出力: 解像度は3840x2160以下に縮小されます

### Web用に圧縮（1080p、30fps）

```bash
python -m video_compressor video.mp4 --resolution 1920x1080 --fps 30
```

### 高品質圧縮

```bash
python -m video_compressor video.mp4 --crf 20 --audio-bitrate 320k
```

### ファイルサイズ優先

```bash
python -m video_compressor video.mp4 --crf 35 --audio-bitrate 128k
```

### 動画のみ（オーディオなし）

```bash
python -m video_compressor video.mp4 --no-audio
```

### 音声圧縮の使用例

```bash
# 高ビットレートMP3を圧縮
python -m video_compressor high_quality.mp3 --audio-bitrate 128k

# ロスレスFLACをMP3に変換
python -m video_compressor lossless.flac --audio-bitrate 320k

# WAVをMP3に変換
python -m video_compressor recording.wav --audio-bitrate 192k
```

## 注意事項

- AV1エンコードはCPU負荷が高いため、高解像度動画の処理には時間がかかる場合があります
- エンコード中にCtrl+Cを押すと処理を中断できます
- 出力ファイルが既に存在する場合、確認なしで上書きされます

## トラブルシューティング

### `FFmpeg not found` エラー

- FFmpegが正しくインストールされていることを確認してください
- FFmpegがシステムPATHに含まれていることを確認してください
- または、`ffmpeg`と`ffprobe`の実行ファイルを `bin` ディレクトリに配置してください
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

## GUI使用方法

GUIは以下のコマンドで起動します:

```bash
python -m video_compressor --gui
```

### 動画圧縮

1. サイドバーから**動画圧縮**を選択
2. 動画ファイルをドラッグ＆ドロップ、または**参照**をクリックしてファイルを選択
3. 圧縮設定を調整:
   - **CRF**: 品質レベル（0-63、デフォルト25）
   - **プリセット**: エンコード速度（0-13、デフォルト6）
   - **解像度**: 最大解像度（4K、2K、1080pなど）
   - **FPS**: 最大フレームレート
   - **音声ビットレート**: 音声品質
4. 必要に応じて音量調整やノイズ除去を有効化
5. 出力フォルダーを設定し、**圧縮開始**をクリック

### 音声圧縮

1. サイドバーから**音声圧縮**を選択
2. 音声ファイルをドラッグ＆ドロップ、または**参照**をクリック
3. MP3ビットレートを設定（32k-320k）
4. 必要に応じて音量調整やノイズ除去を有効化
5. **圧縮開始**をクリック

### 設定

- **言語**: 日本語と英語を切り替え
- **テーマ**: ダーク、ライト、システムから選択
- **FFmpegパス**: 自動検出または手動指定
- **デフォルト圧縮設定**: デフォルトのCRF、プリセット、音声ビットレートを設定

## ビルド方法

### 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/tarminjapan/AmeCompression.git
cd AmeCompression

# uv（Pythonパッケージマネージャー）をインストール
# 詳細: https://docs.astral.sh/uv/getting-started/installation/

# 依存関係をインストール
uv sync --extra dev

# リントを実行
uv run ruff check video_compressor

# 型チェックを実行
uv run pyright video_compressor

# テストを実行
uv run pytest tests -v
```

### 実行ファイルのビルド

```bash
# ディレクトリモード（FFmpeg同梱配布に推奨）
python scripts/build.py

# 単一ファイルモード
python scripts/build.py --onefile

# FFmpeg同梱（bin/にffmpeg.exeとffprobe.exeが必要）
python scripts/build.py --with-ffmpeg
```

## ライセンス

このスクリプトは自由に使用、改変、配布できます。
