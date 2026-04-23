# AmeCompression

FFmpeg (SVT-AV1) を使用した高性能な動画・音声圧縮ツール。
ドラッグ＆ドロップ対応、一括処理、多言語対応を備えたモダンで直感的な GUI を提供します。

## 🚀 主な機能

- **動画圧縮**: SVT-AV1 を採用し、高い圧縮率と画質を両立。
- **音声圧縮**: 各種フォーマットを高品質な MP3 (libmp3lame) へ変換。
- **モダンな GUI**: CustomTkinter 製。ダーク/ライトモード、ドラッグ＆ドロップに対応。
- **スマートツール**: 自動音量調整（ノーマライズ）およびノイズ除去機能を搭載。
- **バッチ処理**: 複数ファイルを同時に、進捗を確認しながら一括処理可能。
- **多言語対応**: 日本語と英語をサポート。

## 📥 インストール

### 1. 前提条件 (FFmpeg)

システムに FFmpeg がインストールされている必要があります。

- **Windows**: `choco install ffmpeg` または [ffmpeg.org](https://ffmpeg.org/download.html) からダウンロード
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

*注意: プロジェクト直下の `bin/` フォルダ内に `ffmpeg` と `ffprobe` の実行ファイルを配置することでも動作します。*

### 2. ソースから実行

```bash
# 依存関係のインストール
pip install .

# GUI の起動
python -m video_compressor --gui
```

## 🖥️ GUI の使い方

1. **起動**: `python -m video_compressor --gui` を実行します。
2. **ファイルの追加**: 動画または音声ファイルをウィンドウにドラッグ＆ドロップします。
3. **設定**: CRF（品質）、プリセット（速度）、ノイズ除去や音量調整を設定します。
4. **実行**: 出力先フォルダを選択し、**開始** ボタンをクリックします。

## 💻 CLI の使い方

基本コマンド:

```bash
# 単一ファイルの圧縮
python -m video_compressor input.mp4

# 複数ファイルの一括圧縮
python -m video_compressor file1.mp4 file2.mp4
```

| オプション | 説明 | デフォルト |
| :--- | :--- | :--- |
| `--gui` | グラフィカルインターフェースを起動 | - |
| `--crf` | 品質 (0-63, 低いほど高品質) | 25 |
| `--preset` | 速度 (0-13, 高いほど高速) | 6 |
| `--volume-gain` | 音量調整 (`auto`, `2.0`, `10dB`) | - |
| `--denoise` | ノイズ除去の有効化 (0.0-1.0) | - |
| `--resolution` | 最大解像度 (例: `1920x1080`) | 4K |

詳細なオプションは `python -m video_compressor --help` で確認できます。

## 🛠️ 開発とビルド

```bash
# uv でのセットアップ (推奨)
uv sync --extra dev

# 実行ファイルのビルド
python scripts/build.py
```

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
