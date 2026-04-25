# AmeCompression

A high-performance video and audio compression tool using FFmpeg with SVT-AV1.
Featuring a modern, intuitive GUI with drag-and-drop support, batch processing, and multilingual support.

## 🚀 Features

- **Modern Web Interface**: Now powered by Electron + React for a sleek, responsive experience.
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

### 2. Run from Source (Desktop App)

```bash
# Backend setup
uv sync --extra dev

# Frontend setup
cd web
npm install
npm run electron:dev
```

*For the legacy CustomTkinter GUI, use `python -m video_compressor --gui`.*

## 📄 Documentation

- [Migration & Release Guide](documents/migration_guide.md) - Details on the new architecture and setup.
- [Development Plan](documents/development_plan.md) - Original GUI roadmap.

## 🖥️ GUI Usage

1. **Launch**: Run `python -m video_compressor --gui`.
2. **Add Files**: Drag and drop video/audio files into the application.
3. **Configure**: Adjust CRF (quality), Preset (speed), or enable Noise Reduction/Volume Gain.
4. **Process**: Select an output directory and click **Start**.

## 💻 CLI Usage

Basic command:

```bash
# Single file compression
python -m video_compressor input.mp4

# Batch compression (multiple files)
python -m video_compressor file1.mp4 file2.mp4
```

| Option | Description | Default |
| :--- | :--- | :--- |
| `--gui` | Launch graphical interface | - |
| `--crf` | Quality (0-63, lower is better) | 25 |
| `--preset` | Speed (0-13, higher is faster) | 6 |
| `--volume-gain` | Adjust volume (`auto`, `2.0`, `10dB`) | - |
| `--denoise` | Enable noise reduction (0.0-1.0) | - |
| `--resolution` | Max resolution (e.g. `1920x1080`) | 4K |

Run `python -m video_compressor --help` for full details.

## 🛠️ Development & Build

```bash
# Setup with uv (recommended)
uv sync --extra dev

# Build executable
python scripts/build.py
```

## 📄 License

This project is licensed under the MIT License.
