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
from .utils import (
    _BOLD,
    _CYAN,
    _DIM,
    _GREEN,
    _RESET,
    _YELLOW,
    format_time,
    parse_bitrate,
    print_header,
)
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
    audio_info = get_audio_info(input_path, ffprobe_path)

    total_duration = audio_info["duration"] or 0
    original_bitrate = audio_info["bitrate"]
    sample_rate = audio_info["sample_rate"]
    channels = audio_info["channels"]

    # Build analysis section
    analysis_rows = [
        ("Source:     ", str(input_path)),
    ]

    if original_bitrate:
        analysis_rows.append(("Bitrate:    ", f"{original_bitrate // 1000} kbps"))
    if sample_rate:
        analysis_rows.append(("Sample rate:", f"{sample_rate} Hz"))
    if channels:
        channel_str = (
            "Mono" if channels == 1 else "Stereo" if channels == 2 else f"{channels} channels"
        )
        analysis_rows.append(("Channels:   ", channel_str))
    if total_duration:
        analysis_rows.append(("Duration:   ", format_time(total_duration)))

    print_header(
        "Analysis",
        analysis_rows,
    )

    # Handle volume analysis only mode
    if analyze_only:
        print(f"\n  {_DIM}Analyzing volume level...{_RESET}")
        volume_info = analyze_volume_level(input_path, ffmpeg_path)

        if volume_info["mean_volume"] is not None:
            print_header(
                "Volume Analysis",
                [
                    ("Mean volume:     ", f"{volume_info['mean_volume']:.1f} dB"),
                    ("Max volume:      ", f"{volume_info['max_volume']:.1f} dB"),
                    (
                        "Recommended gain:",
                        (
                            f"{volume_info['recommended_gain']:+.1f} dB",
                            _YELLOW,
                        )
                        if volume_info["recommended_gain"] is not None
                        else "N/A",
                    ),
                    ("Target level:    ", f"{TARGET_VOLUME_LEVEL} dB"),
                ],
            )
        else:
            print("Error: Could not analyze volume level.")
        return

    # Parse volume gain
    volume_gain_db = None
    volume_rows = []
    if volume_gain is not None:
        volume_gain_db, is_auto = parse_volume_gain(volume_gain)
        if is_auto:
            # Analyze and calculate auto gain
            print(f"\n  {_DIM}Analyzing volume level for auto gain...{_RESET}")
            volume_info = analyze_volume_level(input_path, ffmpeg_path)
            if volume_info["recommended_gain"] is not None:
                volume_gain_db = volume_info["recommended_gain"]
                volume_rows = [
                    (
                        "Volume gain:  ",
                        (f"{volume_gain_db:+.1f} dB (auto)", _YELLOW),
                    ),
                    ("Mean volume:  ", f"{volume_info['mean_volume']:.1f} dB"),
                    ("Max volume:   ", f"{volume_info['max_volume']:.1f} dB"),
                ]
            else:
                print(
                    f"  {_YELLOW}Warning: Could not analyze volume, skipping volume adjustment{_RESET}"
                )

    # Validate denoise level
    denoise = validate_denoise_level(denoise)
    if denoise is not None:
        volume_rows.append(("Denoise:      ", f"{denoise}"))

    # Print audio/volume section if we have info
    if volume_rows:
        print_header(
            "Audio Analysis",
            volume_rows,
        )

    # Validate and cap bitrate
    bitrate_kbps = parse_bitrate(bitrate)
    if bitrate_kbps < MP3_BITRATE_MIN:
        print(
            f"  {_YELLOW}Warning: Bitrate adjusted to minimum {MP3_BITRATE_MIN}k (requested: {bitrate}){_RESET}"
        )
        bitrate = f"{MP3_BITRATE_MIN}k"
    elif bitrate_kbps > MP3_BITRATE_MAX:
        print(
            f"  {_YELLOW}Warning: Bitrate capped to {MP3_BITRATE_MAX}k (requested: {bitrate}){_RESET}"
        )
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

    # Print settings section
    print_header(
        "Compression Settings",
        [
            ("Codec:   ", f"MP3 ({MP3_CODEC})"),
            ("Bitrate: ", bitrate),
        ],
    )

    # Print progress header
    print(f"\n  {_BOLD}Starting MP3 compression...{_RESET}")
    print(f"  {_CYAN}{'─' * 48}{_RESET}")

    # Execute ffmpeg command
    process = None
    stats = {"fps_list": [], "speed_list": [], "frame_list": []}

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
                        "error" in line_stripped.lower() or "warning" in line_stripped.lower()
                    ):
                        print(f"\n  {line_stripped}")

        process.wait()

        if process.returncode == 0:
            # Show 100% progress bar
            if total_duration > 0:
                show_final_progress(total_duration)
            print()  # New line after progress bar
            print(f"  {_CYAN}{'─' * 48}{_RESET}")

            # Get output file size
            output_size = output_path.stat().st_size / (1024 * 1024)  # MB
            input_size = input_path.stat().st_size / (1024 * 1024)  # MB
            compression_ratio = (1 - output_size / input_size) * 100

            # Build results section
            result_rows = [
                ("Input:      ", f"{input_size:.2f} MB"),
                ("Output:     ", f"{output_size:.2f} MB"),
                ("Reduction:  ", (f"{compression_ratio:.1f}%", _GREEN)),
                ("MP3 bitrate:", bitrate),
            ]

            print_header(
                "✓ Compression Completed",
                result_rows,
                color=_GREEN,
            )
            print(f"\n  {_GREEN}Output: {output_path}{_RESET}")

        else:
            print(f"\n\n  ✗ Compression failed (return code: {process.returncode})")
            sys.exit(1)

    except FileNotFoundError:
        print("\n  Error: FFmpeg not found. Please ensure FFmpeg is installed and added to PATH.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n  Compression interrupted by user.")
        if process is not None:
            process.terminate()
        sys.exit(1)
