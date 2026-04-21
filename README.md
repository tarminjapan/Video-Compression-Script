# Video/Audio Compression Tool

A Python tool for video and audio compression using FFmpeg with SVT-AV1 codec (video) and MP3 codec (audio). Supports both CLI and GUI modes.

## Features

### Video Compression

- **Maximum Resolution**: 4K (3840x2160)
- **Codec**: SVT-AV1 (fast AV1 codec)
- **CRF (Quality)**: Default 25 (0-63, lower = higher quality, higher = smaller file size)
- **Audio Codec**: AAC
- **Audio Bitrate**: Maximum 320kbps
- **Maximum FPS**: 120fps

### Audio Compression (MP3)

- **Supported Formats**: MP3, WAV, FLAC, AAC, M4A, OGG, WMA, APE, ALAC
- **Codec**: libmp3lame (LAME MP3 encoder)
- **Bitrate**: 32k - 320kbps
- **Metadata**: Preserves original metadata (title, artist, etc.)

### Common Features

- **Batch Processing**: Compress multiple files at once with progress summary
- **Progress Display**: Real-time progress bar with ETA, FPS, and speed indicators
- **Volume Adjustment**: Automatic or manual volume gain for better audio clarity
- **Noise Reduction**: Audio denoise filter to reduce background noise
- **GUI Mode**: Intuitive graphical interface with drag-and-drop, dark/light themes, and multilingual support (English/Japanese)

## Quick Start

### GUI Mode

```bash
python -m video_compressor --gui
```

The GUI provides:
- **Drag & Drop**: Drop video/audio files directly into the window
- **Sidebar Navigation**: Switch between Video, Audio, and Settings views
- **Real-time Progress**: Track compression with progress bars, FPS, and ETA
- **Dark/Light Theme**: Toggle appearance via Settings
- **English/Japanese**: Switch language at any time

### CLI Mode

```bash
python -m video_compressor input_video.mp4
```

See [CLI Usage](#usage) below for all available options.

## Prerequisites

To use this script, you need the following:

### FFmpeg Installation

**Option 1: System-wide Installation**

**Windows:**

1. Download FFmpeg from the [official website](https://ffmpeg.org/download.html)
2. Extract and place it in a directory (e.g., `C:\ffmpeg`)
3. Add the FFmpeg bin directory to your system PATH (e.g., `C:\ffmpeg\bin`)
4. Verify installation: `ffmpeg -version` and `ffprobe -version`

**Or using Chocolatey:**

```powershell
choco install ffmpeg
```

**Or using winget:**

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

**Option 2: Local FFmpeg (Recommended for Portability)**

You can place FFmpeg executables in the project's `bin` directory:

- Windows: `bin/ffmpeg.exe` and `bin/ffprobe.exe`
- macOS/Linux: `bin/ffmpeg` and `bin/ffprobe`

The script will automatically detect and use executables from the `bin` directory if they exist.

## Usage

### Basic Video Compression

```bash
python -m video_compressor input_video.mp4
```

The output file will be automatically created as `input_video_compressed.mp4`.

### Basic Audio Compression (to MP3)

```bash
python -m video_compressor music.mp3 --audio-bitrate 128k
```

The output file will be automatically created as `music_compressed.mp3`.

Supported audio formats: `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma`, `.ape`, `.alac`

### Interactive Mode (No Input File Specified)

If you run the script without specifying an input file, you will be prompted to enter the path:

```bash
python -m video_compressor
```

```text
Enter the path(s) to the file(s) to compress: input_video.mp4
```

> **Note**: The script automatically removes surrounding double quotes from file paths, so paths like `"C:\Videos\my video.mp4"` will work correctly.

### Batch Processing (Multiple Files)

You can compress multiple files at once by specifying multiple input paths. Paths can be separated by spaces, commas, or newlines:

```bash
# Space-separated
python -m video_compressor "file1.mp4" "file2.mp4" "file3.mp4"

# Comma-separated
python -m video_compressor "file1.mp4", "file2.mp4", "file3.mp4"

# With output directory
python -m video_compressor file1.mp4 file2.mp4 -o /path/to/output_dir/
```

When processing multiple files:

- A progress indicator `[1/3]`, `[2/3]`, etc. is shown for each file
- If one file fails, processing continues with the remaining files
- A summary showing success/failure counts is displayed at the end

You can also enter multiple files in interactive mode:

```text
Enter the path(s) to the file(s) to compress: "C:\Videos\video1.mp4", "C:\Videos\video2.mp4"
```

### Specify Output File Name

```bash
python -m video_compressor input_video.mp4 -o output_video.mp4
```

When processing multiple files, specify a directory instead:

```bash
# Output to an existing directory
python -m video_compressor file1.mp4 file2.mp4 -o /path/to/output_dir/

# Output to a new directory (will be created)
python -m video_compressor file1.mp4 file2.mp4 -o /path/to/new_dir/
```

> **Note**: For multiple files, `--output` must be a directory path. For a single file, you can specify either a file or directory path.

### Change CRF Value (Quality Adjustment)

```bash
python -m video_compressor input_video.mp4 --crf 23
```

- CRF 0-23: High quality (larger file size)
- CRF 25: Default (balance between quality and size)
- CRF 26-40: Medium quality
- CRF 40-63: Low quality (smaller file size)

### Change Encoding Preset

```bash
python -m video_compressor input_video.mp4 --preset 10
```

- Preset 0-4: Slower encoding, better compression efficiency (smaller file)
- Preset 5-7: Default (balance between speed and compression)
- Preset 8-13: Faster encoding, lower compression efficiency (larger file)

### Change Audio Bitrate (Video)

```bash
python -m video_compressor input_video.mp4 --audio-bitrate 256k
```

### Audio Compression Examples

```bash
# Compress MP3 to 128kbps
python -m video_compressor music.mp3 --audio-bitrate 128k

# Convert WAV to MP3
python -m video_compressor audio.wav --audio-bitrate 192k

# Convert FLAC to MP3 with custom output
python -m video_compressor song.flac -o compressed.mp3
```

### Disable Audio

```bash
python -m video_compressor input_video.mp4 --no-audio
```

### Limit Resolution

```bash
python -m video_compressor input_video.mp4 --resolution 1920x1080
```

### Limit FPS

```bash
python -m video_compressor input_video.mp4 --fps 30
```

### Volume Adjustment

The script supports automatic or manual volume adjustment for better audio clarity.

**Analyze volume only (no compression):**

```bash
python -m video_compressor --analyze-volume
```

**Analyze media file only (no compression):**

```bash
python -m video_compressor --analyze input.mp4
```

This will display detailed information including:

- File format (full name, short name)
- Duration
- File size
- Overall bitrate

For each video stream:

- Codec name (full name, short name)
- Profile
- Level
- Resolution
- Aspect ratio
- Frame rate
- Bit depth
- Pixel format
- Color space
- Color range
- Bitrate
- HDR information

For each audio stream:

- Codec name (full name, short name)
- Profile
- Sample rate
- Channels
- Channel layout
- Bit depth
- Bitrate
- Language

Metadata (if present):

- Title
- Artist
- Album
- Creation date
- Other

**Automatic volume adjustment:**

```bash
python -m video_compressor meeting.mp4 --volume-gain auto
```

**Manual volume adjustment (multiplier):**

```bash
python -m video_compressor meeting.mp4 --volume-gain 2.0
```

**Manual volume adjustment (dB):**

```bash
python -m video_compressor meeting.mp4 --volume-gain 10dB
```

### Noise Reduction

Reduce background noise for clearer audio.

**Enable noise reduction (default level 0.15):**

```bash
python -m video_compressor meeting.mp4 --denoise
```

**Custom noise reduction level (0.0-1.0):**

```bash
python -m video_compressor meeting.mp4 --denoise 0.3
```

### Combine Volume Adjustment and Noise Reduction

```bash
python -m video_compressor meeting.mp4 --volume-gain auto --denoise 0.2
```

### All Options Combined

```bash
python -m video_compressor input_video.mp4 -o output_video.mp4 --crf 23 --audio-bitrate 256k --resolution 1920x1080 --fps 60
```

## Options

| Option | Description | Default |
| - | - | - |
| `input` | Input file path(s). Multiple files can be separated by spaces, commas, or newlines. (optional, will prompt if not provided) | - |
| `-o`, `--output` | Output file or directory path. For multiple files, specify a directory. | Video: `{input_filename}_compressed.{extension}`, Audio: `{input_filename}_compressed.mp3` |
| `--crf` | AV1 CRF value (0-63, video only) | 25 |
| `--preset` | Encoding speed preset (0-13, higher = faster, video only) | 6 |
| `--audio-bitrate` | Audio bitrate (video: max 320k, audio: 32k-320k) | 192k |
| `--no-audio` | Disable audio track (video only) | Audio enabled |
| `--fps` | Maximum FPS (max: 120, video only) | Original FPS |
| `--resolution` | Maximum resolution in WxH format (e.g., 1920x1080, video only) | 3840x2160 |
| `--volume-gain` | Volume gain: multiplier (e.g., `2.0`), dB (e.g., `10dB`), or `auto` | Disabled |
| `--analyze-volume` | Analyze volume level and show recommended gain (no compression) | Disabled |
| `--analyze` | Analyze media file and show detailed information (codec, resolution, bitrate, etc.) | Disabled |
| `--denoise` | Enable audio noise reduction (level: 0.0-1.0) | Disabled |

## Help

```bash
python -m video_compressor --help
```

## Feature Details

### Resolution Limit

- If the original video exceeds 4K (3840x2160), it will be scaled down while maintaining aspect ratio
- If the resolution is within limits, the original resolution is preserved
- Custom resolution limits can be set with `--resolution`

### FPS Limit

- If the original video FPS exceeds the specified maximum, it will be reduced
- Default maximum is 120fps
- If the FPS is within limits, the original FPS is preserved

### SVT-AV1 Codec

- Fast AV1 encoder developed by Intel
- 10-100x faster encoding compared to libaom-av1
- Latest video compression standard with high compression efficiency
- CRF mode encoding (quality-based variable bitrate)
- Automatic multi-threading support

### Audio Processing (Video)

- Converted to AAC format
- Maximum 320kbps bitrate
- Can be disabled with `--no-audio`

### Audio Compression (Audio Files)

- Converts various audio formats to MP3
- Uses libmp3lame encoder (high quality MP3)
- Bitrate range: 32k - 320kbps
- Preserves metadata (title, artist, album, etc.)
- Automatic file type detection based on extension

### Progress Display

During compression, a real-time progress bar is displayed showing:

- Progress percentage with visual bar
- Current time / Total time
- ETA (Estimated Time Remaining)
- Encoding FPS
- Speed multiplier
- Frame count

### Volume Adjustment

The script can analyze audio levels and automatically adjust volume for better clarity:

- **Auto Mode**: Analyzes the audio and calculates optimal gain to reach target loudness (-16dB)
- **Multiplier Mode**: Specify a multiplier like `2.0` to double the volume
- **dB Mode**: Specify gain in decibels like `10dB`
- **Analysis Only**: Use `--analyze-volume` to see current levels and recommended gain without compression

The automatic gain calculation prevents clipping by considering the maximum volume level.

### Noise Reduction

The script uses FFmpeg's `afftdn` filter for audio noise reduction:

- **Level Range**: 0.0 (minimal) to 1.0 (aggressive)
- **Default Level**: 0.15 (light noise reduction)
- Higher values remove more noise but may affect audio quality

## Examples

### Compress 8K Video to 4K

```bash
python -m video_compressor 8k_video.mp4 -o compressed_4k.mp4
```

Output: Resolution will be scaled down to 3840x2160 or below

### Compress for Web (1080p, 30fps)

```bash
python -m video_compressor video.mp4 --resolution 1920x1080 --fps 30
```

### High Quality Compression

```bash
python -m video_compressor video.mp4 --crf 20 --audio-bitrate 320k
```

### Small File Size Priority

```bash
python -m video_compressor video.mp4 --crf 35 --audio-bitrate 128k
```

### Video Only (No Audio)

```bash
python -m video_compressor video.mp4 --no-audio
```

### Audio Compression Examples

```bash
# Compress high-bitrate MP3
python -m video_compressor high_quality.mp3 --audio-bitrate 128k

# Convert lossless FLAC to MP3
python -m video_compressor lossless.flac --audio-bitrate 320k

# Convert WAV to MP3
python -m video_compressor recording.wav --audio-bitrate 192k
```

## Notes

- AV1 encoding is CPU-intensive; high-resolution videos may take longer to process
- Press Ctrl+C during encoding to interrupt the process
- If the output file already exists, it will be overwritten automatically

## Troubleshooting

### `FFmpeg not found` Error

- Ensure FFmpeg is correctly installed
- Check that FFmpeg is included in your system PATH
- Alternatively, place `ffmpeg` and `ffprobe` executables in the `bin` directory
- Verify by running `ffmpeg -version` in the command line

### Video/Audio Info Retrieval Error

- Verify that the input file exists
- Check if the file is corrupted
- Ensure the file is a valid video or audio format

### Unsupported File Type Error

- Check the file extension
- Supported video formats: `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.ts`, `.mts`, `.m2ts`
- Supported audio formats: `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma`, `.ape`, `.alac`

### Progress Bar Not Displaying

- The progress bar requires video duration information
- Some video formats may not provide duration metadata
- The compression will still complete successfully

## GUI Usage

Launch the GUI with:

```bash
python -m video_compressor --gui
```

### Video Compression

1. Select **Video Compression** from the sidebar
2. Drag and drop video files or click **Browse** to select files
3. Adjust compression settings:
   - **CRF**: Quality level (0-63, default 25)
   - **Preset**: Encoding speed (0-13, default 6)
   - **Resolution**: Max resolution (4K, 2K, 1080p, etc.)
   - **FPS**: Max frame rate
   - **Audio Bitrate**: Audio quality
4. Optionally enable volume adjustment or noise reduction
5. Set output folder and click **Start Compression**

### Audio Compression

1. Select **Audio Compression** from the sidebar
2. Drag and drop audio files or click **Browse**
3. Set the MP3 bitrate (32k-320k)
4. Optionally enable volume adjustment or noise reduction
5. Click **Start Compression**

### Settings

- **Language**: Switch between English and Japanese
- **Theme**: Choose Dark, Light, or System theme
- **FFmpeg Path**: Auto-detect or manually specify FFmpeg location
- **Default Compression**: Set default CRF, preset, and audio bitrate

## Building from Source

### Development Setup

```bash
# Clone the repository
git clone https://github.com/tarminjapan/AmeCompression.git
cd AmeCompression

# Install uv (Python package manager)
# See: https://docs.astral.sh/uv/getting-started/installation/

# Install dependencies
uv sync --extra dev

# Run linting
uv run ruff check video_compressor

# Run type checking
uv run pyright video_compressor

# Run tests
uv run pytest tests -v
```

### Building the Executable

```bash
# Directory mode (recommended for distribution with FFmpeg)
python scripts/build.py

# Single file mode
python scripts/build.py --onefile

# Bundle FFmpeg (requires ffmpeg.exe and ffprobe.exe in bin/)
python scripts/build.py --with-ffmpeg
```

## License

This script is free to use, modify, and distribute.
