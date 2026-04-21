# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.6] - 2025-04-20

### Added

- Settings view with language, theme, FFmpeg path, and default compression settings
- Centralized color palette for consistent light/dark theme support (`gui/theme/colors.py`)
- FFmpeg path mode (auto-detect / manual) in settings
- Default compression settings (CRF, preset, audio bitrate) in settings

### Changed

- Improved UI text refresh on language change
- Enhanced volume section component

## [1.0.5] - 2025-04-19

### Added

- Volume adjustment UI with modes (disabled/auto/multiplier/dB)
- Noise reduction UI with level slider and presets (light/medium/strong)
- Visual volume level meter
- Background volume analysis thread

## [1.0.4] - 2025-04-18

### Added

- Progress panel with per-file and overall progress bars
- Cancel and pause/resume support for batch processing
- Error log display in progress panel

## [1.0.3] - 2025-04-17

### Added

- Batch file processing UI with file list management
- Drag-and-drop file selection (Windows)
- File reordering and removal

## [1.0.2] - 2025-04-16

### Added

- Audio compression view (MP3 conversion)
- Input file info display with background loading
- Audio bitrate slider (32k-320k)

## [1.0.1] - 2025-04-15

### Added

- GUI mode with CustomTkinter (`--gui` flag)
- Dark/light/system theme support
- Sidebar navigation (video/audio/settings)
- Internationalization (English/Japanese)
- Video compression view with CRF, preset, resolution, FPS settings

## [1.0.0] - 2025-04-14

### Added

- Video compression with SVT-AV1 codec
- Audio compression to MP3 with libmp3lame
- CLI interface with argparse
- Batch processing support
- Volume analysis and adjustment (auto/multiplier/dB)
- Noise reduction with afftdn filter
- Real-time progress bar
- FFmpeg auto-detection (local bin/ or system PATH)
- Resolution scaling with aspect ratio preservation
- FPS limiting
