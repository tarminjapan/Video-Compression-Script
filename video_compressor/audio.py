"""
Audio compression functionality.
"""

import subprocess
import sys
from pathlib import Path

from .config import (
    DEFAULT_MP3_BITRATE,
    MP3_BITRATE_MAX,
    MP3_BITRATE_MIN,
    MP3_CODEC,
    TARGET_VOLUME_LEVEL,
)
from .ffmpeg import get_audio_info
from .progress import show_final_progress, update_progress
from .utils import format_time, parse_bitrate
from .volume import (
    analyze_volume_level,
    build_audio_filter,
    parse_volume_gain,
    validate_denoise_level,
)


def compress_audio(
    input_path,
    output_path=None,
    bitrate=None,
    volume_gain=None,
    denoise=None,
    analyze_only=False,
    ffmpeg_path="ffmpeg",
    ffprobe_path="ffprobe",
):
    """
    Compress audio file to MP3 using FFmpeg.

    Args:
        input_path (str): Input audio file path
        output_path (str): Output audio file path (optional)
        bitrate (str): MP3 bitrate (default: DEFAULT_MP3_BITRATE)
        volume_gain (str): Volume gain (e.g., "2.0", "10dB", "auto", None)
        denoise (float): Denoise level 0.0-1.0 (None = disabled)
        analyze_only (bool): Only analyze volume, don't compress
        ffmpeg_path (str): Path to ffmpeg executable
        ffprobe_path (str): Path to ffprobe executable
    """
    # Set default values
    if bitrate is None:
        bitrate = DEFAULT_MP3_BITRATE
    input_path = Path(input_path)

    # Validate input file
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    # Set default output path (always .mp3)
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_compressed.mp3"
    else:
        output_path = Path(output_path)
        # Ensure output is .mp3
        if output_path.suffix.lower() != ".mp3":
            output_path = output_path.with_suffix(".mp3")

    # Get audio information
    print(f"Analyzing audio: {input_path}")
    audio_info = get_audio_info(input_path, ffprobe_path)

    total_duration = audio_info["duration"] or 0
    original_bitrate = audio_info["bitrate"]
    sample_rate = audio_info["sample_rate"]
    channels = audio_info["channels"]

    if original_bitrate:
        print(f"Original bitrate: {original_bitrate // 1000} kbps")
    if sample_rate:
        print(f"Sample rate: {sample_rate} Hz")
    if channels:
        channel_str = (
            "Mono"
            if channels == 1
            else "Stereo"
            if channels == 2
            else f"{channels} channels"
        )
        print(f"Channels: {channel_str}")
    if total_duration:
        print(f"Duration: {format_time(total_duration)}")

    # Handle volume analysis only mode
    if analyze_only:
        print("\nAnalyzing volume level...")
        volume_info = analyze_volume_level(input_path, ffmpeg_path)

        if volume_info["mean_volume"] is not None:
            print("-" * 60)
            print("Volume Analysis Results:")
            print(f"  Mean volume: {volume_info['mean_volume']:.1f} dB")
            print(f"  Max volume:  {volume_info['max_volume']:.1f} dB")
            if volume_info["recommended_gain"] is not None:
                print(f"  Recommended gain: {volume_info['recommended_gain']:+.1f} dB")
                print(f"  Target level: {TARGET_VOLUME_LEVEL} dB")
            print("-" * 60)
        else:
            print("Error: Could not analyze volume level.")
        return

    # Parse volume gain
    volume_gain_db = None
    if volume_gain is not None:
        volume_gain_db, is_auto = parse_volume_gain(volume_gain)
        if is_auto:
            # Analyze and calculate auto gain
            print("\nAnalyzing volume level for auto gain...")
            volume_info = analyze_volume_level(input_path, ffmpeg_path)
            if volume_info["recommended_gain"] is not None:
                volume_gain_db = volume_info["recommended_gain"]
                print(f"Auto volume gain: {volume_gain_db:+.1f} dB")
                print(f"  Current mean volume: {volume_info['mean_volume']:.1f} dB")
                print(f"  Current max volume: {volume_info['max_volume']:.1f} dB")
            else:
                print("Warning: Could not analyze volume, skipping volume adjustment")

    # Validate denoise level
    denoise = validate_denoise_level(denoise)
    if denoise is not None:
        print(f"Denoise level: {denoise}")

    # Validate and cap bitrate
    bitrate_kbps = parse_bitrate(bitrate)
    if bitrate_kbps < MP3_BITRATE_MIN:
        print(
            f"Warning: Bitrate adjusted to minimum {MP3_BITRATE_MIN}k (requested: {bitrate})"
        )
        bitrate = f"{MP3_BITRATE_MIN}k"
    elif bitrate_kbps > MP3_BITRATE_MAX:
        print(f"Warning: Bitrate capped to {MP3_BITRATE_MAX}k (requested: {bitrate})")
        bitrate = f"{MP3_BITRATE_MAX}k"

    # Build ffmpeg command
    cmd = [ffmpeg_path, "-i", str(input_path), "-y"]  # -y to overwrite output

    # Build audio filter
    audio_filter = build_audio_filter(volume_gain_db, denoise)
    if audio_filter:
        cmd.extend(["-af", audio_filter])

    # MP3 codec settings
    cmd.extend(
        [
            "-c:a",
            MP3_CODEC,
            "-b:a",
            bitrate,
            "-map_metadata",
            "0",  # Preserve metadata
        ]
    )

    # Output file
    cmd.append(str(output_path))

    # Display command for reference
    print(f"\nFFmpeg command: {' '.join(cmd)}\n")
    print("Starting MP3 compression...")
    print("-" * 60)

    # Execute ffmpeg command
    process = None
    stats = {"fps_list": [], "speed_list": [], "frame_list": [], "rolling_data": []}

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            encoding="utf-8",
            errors="replace",
        )

        # Display progress in real-time
        if process.stdout:
            for line in process.stdout:
                # Try to parse and display progress
                if not update_progress(line, total_duration, stats):
                    # Only show non-progress lines that are errors or important info
                    line_stripped = line.strip()
                    if line_stripped and (
                        "error" in line_stripped.lower()
                        or "warning" in line_stripped.lower()
                    ):
                        print(f"\n  {line_stripped}")

        process.wait()

        if process.returncode == 0:
            # Show 100% progress bar
            if total_duration > 0:
                show_final_progress(total_duration)
            print()  # New line after progress bar
            print("-" * 60)
            print("✓ MP3 compression completed successfully!")
            print(f"  Output: {output_path}")

            # Get output file size
            output_size = output_path.stat().st_size / (1024 * 1024)  # MB
            input_size = input_path.stat().st_size / (1024 * 1024)  # MB
            compression_ratio = (1 - output_size / input_size) * 100

            print(f"  Input size: {input_size:.2f} MB")
            print(f"  Output size: {output_size:.2f} MB")
            print(f"  Compression: {compression_ratio:.1f}% reduction")
            print(f"  MP3 bitrate: {bitrate}")
        else:
            print(f"\n✗ Compression failed (return code: {process.returncode})")
            sys.exit(1)

    except FileNotFoundError:
        print(
            "Error: FFmpeg not found. Please ensure FFmpeg is installed and added to PATH."
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nCompression interrupted by user.")
        if process is not None:
            process.terminate()
        sys.exit(1)
