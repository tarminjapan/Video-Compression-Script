# AmeCompression

A high-performance video and audio compression tool using FFmpeg with SVT-AV1.
Featuring a modern, intuitive interface powered by Electron, React, and Flask.

## 🚀 Features

- **Modern Web Interface**: Powered by Electron + React for a sleek, responsive experience.
- **Video Compression**: Powered by SVT-AV1 for high efficiency and quality.
- **Audio Compression**: Convert various formats to high-quality MP3 (libmp3lame).
- **Smart Tools**: Automatic volume adjustment (normalization) and noise reduction.
- **Batch Processing**: Compress multiple files simultaneously with clear progress tracking.
- **Multilingual**: Supports both English and Japanese.

## 📥 Installation

### 1. Prerequisites (FFmpeg)

You must have FFmpeg installed on your system.

- **Windows**: `choco install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

*Note: You can also place `ffmpeg` and `ffprobe` executables in a `bin/` folder inside the project root.*

### 2. Run from Source

```bash
# Backend setup
uv sync --extra dev

# Frontend setup
cd frontend
npm install
npm run electron:dev
```

## 📄 Documentation

- [Migration Guide](documents/migration_guide.md) - Details on the architecture and setup.
- [Development Plan](documents/development_plan.md) - Project roadmap and goals.

## 🖥️ GUI Usage

1. **Launch**: Start the app via `npm run electron:dev` (dev) or the built executable.
2. **Add Files**: Drag and drop video/audio files into the application.
3. **Configure**: Adjust CRF (quality), Preset (speed), or enable Noise Reduction/Volume Gain.
4. **Process**: Select an output directory and click **Start**.

## 💻 CLI Usage

The core engine is also available as a CLI tool:

```bash
# Single file compression
uv run python -m video_compressor input.mp4

# Batch compression (multiple files)
uv run python -m video_compressor file1.mp4 file2.mp4
```

| Option | Description | Default |
| :--- | :--- | :--- |
| `--crf` | Quality (0-63, lower is better) | 25 |
| `--preset` | Speed (0-13, higher is faster) | 6 |
| `--volume-gain` | Adjust volume (`auto`, `2.0`, `10dB`) | - |
| `--denoise` | Enable noise reduction (0.0-1.0) | - |
| `--resolution` | Max resolution (e.g. `1920x1080`) | 4K |

Run `uv run python -m video_compressor --help` for full details.

## 🛠️ Development & Build

```bash
# Backend
uv sync --extra dev

# Frontend
cd frontend
npm install
npm run build

# Build Standalone (using PyInstaller for backend)
uv run scripts/build.py
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov

# Run linter / formatter check
uv run ruff check
uv run ruff format --check

# Run strict type check (warnings fail)
uv run pyright --warnings

# Frontend strict checks
npm --prefix frontend run lint:strict
npm --prefix frontend run format:check
```

## 📄 License

This project is licensed under the MIT License.
