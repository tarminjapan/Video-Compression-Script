#import "/.typst/A4-Ame-Serif.typ": *
#show: a4_ame_init

= Video/Audio Compression Script

A Python script for video and audio compression using FFmpeg with SVT-AV1 codec (video) and MP3 codec (audio).

The latest information is described in the README.md file.

== Features

=== Video Compression

- Maximum Resolution: 4K (3840x2160)
- Codec: SVT-AV1 (fast AV1 codec)
- CRF (Quality): Default 25 (0-63, lower = higher quality, higher = smaller file size)
- Audio Codec: AAC
- Audio Bitrate: Maximum 320kbps
- Maximum FPS: 120fps

=== Audio Compression (MP3)

- Supported Formats: MP3, WAV, FLAC, AAC, M4A, OGG, WMA, APE, ALAC
- Codec: libmp3lame (LAME MP3 encoder)
- Bitrate: 32k - 320kbps
- Metadata: Preserves original metadata (title, artist, etc.)

=== Common Features

- Progress Display: Real-time progress bar with ETA, FPS, and speed indicators
- Volume Adjustment: Automatic or manual volume gain for better audio clarity
- Noise Reduction: Audio denoise filter to reduce background noise

#pagebreak()

== Prerequisites

To use this script, you need the following:

=== FFmpeg Installation

*Option 1: System-wide Installation*

*Windows:*

1. Download FFmpeg from the #link("https://ffmpeg.org/download.html")[official website]
2. Extract and place it in a directory (e.g., `C:\ffmpeg`)
3. Add the FFmpeg bin directory to your system PATH (e.g., `C:\ffmpeg\bin`)
4. Verify installation: `ffmpeg -version` and `ffprobe -version`

*Or using Chocolatey:*

```powershell
choco install ffmpeg
```

*Or using winget:*

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

*Option 2: Local FFmpeg (Recommended for Portability)*

You can place FFmpeg executables in the same directory as the script:

- Windows: `ffmpeg.exe` and `ffprobe.exe`
- macOS/Linux: `ffmpeg` and `ffprobe`

The script will automatically detect and use local executables if they exist.

#pagebreak()

== Usage

=== Basic Video Compression

```bash
python compress_video.py input_video.mp4
```

The output file will be automatically created as `input_video_compressed.mp4`.

=== Basic Audio Compression (to MP3)

```bash
python compress_video.py music.mp3 --audio-bitrate 128k
```

The output file will be automatically created as `music_compressed.mp3`.

Supported audio formats: `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma`, `.ape`, `.alac`

=== Interactive Mode (No Input File Specified)

If you run the script without specifying an input file, you will be prompted to enter the path:

```bash
python compress_video.py
```

```text
Enter the path to the video file to compress: input_video.mp4
```

#quote[
  Note: The script automatically removes surrounding double quotes from file paths, so paths like `"C:\Videos\my video.mp4"` will work correctly.
]

=== Specify Output File Name

```bash
python compress_video.py input_video.mp4 -o output_video.mp4
```

=== Change CRF Value (Quality Adjustment)

```bash
python compress_video.py input_video.mp4 --crf 23
```

- CRF 0-23: High quality (larger file size)
- CRF 25: Default (balance between quality and size)
- CRF 26-40: Medium quality
- CRF 40-63: Low quality (smaller file size)

=== Change Audio Bitrate (Video)

```bash
python compress_video.py input_video.mp4 --audio-bitrate 256k
```

=== Audio Compression Examples

```bash
# Compress MP3 to 128kbps
python compress_video.py music.mp3 --audio-bitrate 128k

# Convert WAV to MP3
python compress_video.py audio.wav --audio-bitrate 192k

# Convert FLAC to MP3 with custom output
python compress_video.py song.flac -o compressed.mp3
```

=== Disable Audio

```bash
python compress_video.py input_video.mp4 --no-audio
```

=== Limit Resolution

```bash
python compress_video.py input_video.mp4 --resolution 1920x1080
```

=== Limit FPS

```bash
python compress_video.py input_video.mp4 --fps 30
```

#pagebreak()

=== Volume Adjustment

The script supports automatic or manual volume adjustment for better audio clarity.

*Analyze volume only (no compression):*

```bash
python compress_video.py --analyze-volume
```

*Automatic volume adjustment:*

```bash
python compress_video.py meeting.mp4 --volume-gain auto
```

*Manual volume adjustment (multiplier):*

```bash
python compress_video.py meeting.mp4 --volume-gain 2.0
```

*Manual volume adjustment (dB):*

```bash
python compress_video.py meeting.mp4 --volume-gain 10dB
```

=== Noise Reduction

Reduce background noise for clearer audio.

*Enable noise reduction (default level 0.15):*

```bash
python compress_video.py meeting.mp4 --denoise
```

*Custom noise reduction level (0.0-1.0):*

```bash
python compress_video.py meeting.mp4 --denoise 0.3
```

=== Combine Volume Adjustment and Noise Reduction

```bash
python compress_video.py meeting.mp4 --volume-gain auto --denoise 0.2
```

=== All Options Combined

```bash
python compress_video.py input_video.mp4 -o output_video.mp4 --crf 23 --audio-bitrate 256k --resolution 1920x1080 --fps 60
```

#pagebreak()

== Options

#table(
  columns: (4fr, 6fr, 5fr),
  align: (left, left, left),
  stroke: none,
  table.hline(),
  [*Option*], [*Description*], [*Default*],
  table.hline(stroke: 0.5pt),
  [`input`], [Input video/audio file path (optional, will prompt if not provided)], [-],
  [`-o`, `--output`],
  [Output file path],
  [Video: `{input_filename}_compressed.{extension}`, Audio: `{input_filename}_compressed.mp3`],
  [`--crf`], [AV1 CRF value (0-63, video only)], [25],
  [`--audio-bitrate`], [Audio bitrate (video: max 320k, audio: 32k-320k)], [192k],
  [`--no-audio`], [Disable audio track (video only)], [Audio enabled],
  [`--fps`], [Maximum FPS (max: 120, video only)], [Original FPS],
  [`--resolution`], [Maximum resolution in WxH format (e.g., 1920x1080, video only)], [3840x2160],
  [`--volume-gain`], [Volume gain: multiplier (e.g., `2.0`), dB (e.g., `10dB`), or `auto`], [Disabled],
  [`--analyze-volume`], [Analyze volume level and show recommended gain (no compression)], [Disabled],
  [`--denoise`], [Enable audio noise reduction (level: 0.0-1.0)], [Disabled],
  table.hline(),
)

== Help

```bash
python compress_video.py --help
```

#pagebreak()

== Feature Details

=== Resolution Limit

- If the original video exceeds 4K (3840x2160), it will be scaled down while maintaining aspect ratio
- If the resolution is within limits, the original resolution is preserved
- Custom resolution limits can be set with `--resolution`

=== FPS Limit

- If the original video FPS exceeds the specified maximum, it will be reduced
- Default maximum is 120fps
- If the FPS is within limits, the original FPS is preserved

=== SVT-AV1 Codec

- Fast AV1 encoder developed by Intel
- 10-100x faster encoding compared to libaom-av1
- Latest video compression standard with high compression efficiency
- CRF mode encoding (quality-based variable bitrate)
- Automatic multi-threading support

=== Audio Processing (Video)

- Converted to AAC format
- Maximum 320kbps bitrate
- Can be disabled with `--no-audio`

=== Audio Compression (Audio Files)

- Converts various audio formats to MP3
- Uses libmp3lame encoder (high quality MP3)
- Bitrate range: 32k - 320kbps
- Preserves metadata (title, artist, album, etc.)
- Automatic file type detection based on extension

#pagebreak()

=== Progress Display

During compression, a real-time progress bar is displayed showing:

- Progress percentage with visual bar
- Current time / Total time
- ETA (Estimated Time Remaining)
- Encoding FPS
- Speed multiplier
- Frame count

=== Volume Adjustment

The script can analyze audio levels and automatically adjust volume for better clarity:

- *Auto Mode*: Analyzes the audio and calculates optimal gain to reach target loudness (-16dB)
- *Multiplier Mode*: Specify a multiplier like `2.0` to double the volume
- *dB Mode*: Specify gain in decibels like `10dB`
- *Analysis Only*: Use `--analyze-volume` to see current levels and recommended gain without compression

The automatic gain calculation prevents clipping by considering the maximum volume level.

=== Noise Reduction

The script uses FFmpeg's `afftdn` filter for audio noise reduction:

- *Level Range*: 0.0 (minimal) to 1.0 (aggressive)
- *Default Level*: 0.15 (light noise reduction)
- Higher values remove more noise but may affect audio quality

#pagebreak()

== Examples

=== Compress 8K Video to 4K

```bash
python compress_video.py 8k_video.mp4 -o compressed_4k.mp4
```

Output: Resolution will be scaled down to 3840x2160 or below

=== Compress for Web (1080p, 30fps)

```bash
python compress_video.py video.mp4 --resolution 1920x1080 --fps 30
```

=== High Quality Compression

```bash
python compress_video.py video.mp4 --crf 20 --audio-bitrate 320k
```

=== Small File Size Priority

```bash
python compress_video.py video.mp4 --crf 35 --audio-bitrate 128k
```

=== Video Only (No Audio)

```bash
python compress_video.py video.mp4 --no-audio
```

=== Audio Compression Examples

```bash
# Compress high-bitrate MP3
python compress_video.py high_quality.mp3 --audio-bitrate 128k

# Convert lossless FLAC to MP3
python compress_video.py lossless.flac --audio-bitrate 320k

# Convert WAV to MP3
python compress_video.py recording.wav --audio-bitrate 192k
```

== Notes

- AV1 encoding is CPU-intensive; high-resolution videos may take longer to process
- Press Ctrl+C during encoding to interrupt the process
- If the output file already exists, it will be overwritten automatically

== Troubleshooting

=== `FFmpeg not found` Error

- Ensure FFmpeg is correctly installed
- Check that FFmpeg is included in your system PATH
- Alternatively, place `ffmpeg` and `ffprobe` executables in the script directory
- Verify by running `ffmpeg -version` in the command line

=== Video/Audio Info Retrieval Error

- Verify that the input file exists
- Check if the file is corrupted
- Ensure the file is a valid video or audio format

=== Unsupported File Type Error

- Check the file extension
- Supported video formats: `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.ts`, `.mts`, `.m2ts`
- Supported audio formats: `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma`, `.ape`, `.alac`

=== Progress Bar Not Displaying

- The progress bar requires video duration information
- Some video formats may not provide duration metadata
- The compression will still complete successfully
