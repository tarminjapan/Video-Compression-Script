# AmeCompression

FFmpeg (SVT-AV1) を使用した高性能な動画・音声圧縮ツール。
Electron、React、および Flask を活用した、モダンで直感的なインターフェースを提供します。

## 🚀 主な機能

- **モダンな Web インターフェース**: Electron + React により、洗練されたレスポンシブな操作感を実現。
- **動画圧縮**: SVT-AV1 を採用し、高い圧縮率と画質を両立。
- **音声圧縮**: 各種フォーマットを高品質な MP3 (libmp3lame) へ変換。
- **スマートツール**: 自動音量調整（ノーマライズ）およびノイズ除去機能を搭載。
- **バッチ処理**: 複数ファイルを同時に、進捗を確認しながら一括処理可能。
- **多言語対応**: 日本語と英語をサポート。

## 📥 インストール

### 1. 前提条件 (FFmpeg)

システムに FFmpeg がインストールされている必要があります。

- **Windows**: `choco install ffmpeg` または [ffmpeg.org](https://ffmpeg.org/download.html) からダウンロード
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

*注意: プロジェクトルートの `bin/` フォルダ内に `ffmpeg` と `ffprobe` の実行ファイルを配置することでも動作します。*

### 2. ソースから実行

```bash
# バックエンドのセットアップ
uv sync --extra dev

# フロントエンドのセットアップ
cd frontend
npm install
npm run electron:dev
```

## 📄 ドキュメント

- [移行ガイド (英語)](documents/migration_guide.md) - アーキテクチャとセットアップの詳細。
- [開発計画](documents/development_plan.md) - プロジェクトのロードマップと目標。

## 🖥️ GUI の使い方

1. **起動**: `npm run electron:dev` (開発時) またはビルド済みの実行ファイルを起動します。
2. **ファイルの追加**: 動画または音声ファイルをウィンドウにドラッグ＆ドロップします。
3. **設定**: CRF（品質）、プリセット（速度）、ノイズ除去や音量調整を設定します。
4. **実行**: 出力先フォルダを選択し、**開始** ボタンをクリックします。

## 💻 CLI の使い方

コアエンジンは CLI ツールとしても利用可能です。

```bash
# 単一ファイルの圧縮
uv run python -m video_compressor input.mp4

# 複数ファイルの一括圧縮
uv run python -m video_compressor file1.mp4 file2.mp4
```

| オプション | 説明 | デフォルト |
| :--- | :--- | :--- |
| `--crf` | 品質 (0-63, 低いほど高品質) | 25 |
| `--preset` | 速度 (0-13, 高いほど高速) | 6 |
| `--volume-gain` | 音量調整 (`auto`, `2.0`, `10dB`) | - |
| `--denoise` | ノイズ除去の有効化 (0.0-1.0) | - |
| `--resolution` | 最大解像度 (例: `1920x1080`) | 4K |

詳細なオプションは `uv run python -m video_compressor --help` で確認できます。

## 🛠️ 開発とビルド

```bash
# バックエンド
uv sync --extra dev

# フロントエンド
cd frontend
npm install
npm run build

# スタンドアロンビルド (PyInstaller を使用)
uv run scripts/build.py
```

## 🧪 テスト

```bash
# 全テストの実行
uv run pytest

# カバレッジレポート付きで実行
uv run pytest --cov

# リント・フォーマットチェック
uv run ruff check
uv run ruff format --check

# 厳格な型チェック（warningも失敗扱い）
uv run pyright --warnings

# フロントエンドの厳格チェック
npm --prefix frontend run lint:strict
npm --prefix frontend run format:check
```

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
