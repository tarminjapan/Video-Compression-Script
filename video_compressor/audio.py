"""Audio compression functionality.

This module provides both CLI-oriented functions and service-layer functions
for audio compression. The service layer functions return structured results
without side effects (print/exit), making them suitable for API and GUI use.
"""

import subprocess
import sys
import time
from pathlib import Path

from .config import (
    DEFAULT_MP3_BITRATE,
    MP3_BITRATE_MAX,
    MP3_BITRATE_MIN,
    MP3_CODEC,
    TARGET_VOLUME_LEVEL,
)
from .ffmpeg import get_audio_info, get_audio_info_safe
from .models import (
    AudioCompressionResult,
    CompressionStatus,
    VolumeAnalysisResult,
)
from .progress_handler import (
    CancellationSource,
    CLIProgressReporter,
    OutputCallback,
    ProgressCallback,
    ProgressParser,
)
from .utils import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    RED,
    RESET,
    YELLOW,
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


def compress_audio(  # noqa: PLR0912, PLR0913, PLR0915
    input_path: str | Path,
    output_path: str | Path | None = None,
    bitrate: str | None = None,
    volume_gain: str | None = None,
    denoise: float | None = None,
    analyze_only: bool = False,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
):
    """Compress audio file to MP3 using FFmpeg.

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

    if not audio_info or audio_info.get("duration") is None:
        print("Error: Could not retrieve audio information.")
        sys.exit(1)

    total_duration = audio_info["duration"] or 0
    original_bitrate = audio_info["bitrate"]
    sr_val = audio_info.get("sample_rate")
    ch_val = audio_info.get("channels")
    sample_rate = int(sr_val) if sr_val is not None else None
    channels = int(ch_val) if ch_val is not None else None

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
        print(f"\n  {DIM}Analyzing volume level...{RESET}")
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
                            YELLOW,
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
            print(f"\n  {DIM}Analyzing volume level for auto gain...{RESET}")
            volume_info = analyze_volume_level(input_path, ffmpeg_path)
            if volume_info["recommended_gain"] is not None:
                volume_gain_db = volume_info["recommended_gain"]
                volume_rows = [
                    (
                        "Volume gain:  ",
                        (f"{volume_gain_db:+.1f} dB (auto)", YELLOW),
                    ),
                    ("Mean volume:  ", f"{volume_info['mean_volume']:.1f} dB"),
                    ("Max volume:   ", f"{volume_info['max_volume']:.1f} dB"),
                ]
            else:
                print(
                    f"  {YELLOW}Warning: Could not analyze volume, skipping volume adjustment{RESET}"
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

    # Print settings section
    print_header(
        "Compression Settings",
        [
            ("Codec:   ", f"MP3 ({MP3_CODEC})"),
            ("Bitrate: ", bitrate),
        ],
    )

    # Print progress header
    print(f"\n  {BOLD}Starting MP3 compression...{RESET}")
    print(f"  {CYAN}{'─' * 48}{RESET}")

    # Execute via service layer
    reporter = CLIProgressReporter(total_duration)

    def on_output(line: str) -> None:
        line_stripped = line.strip()
        if line_stripped and (
            "error" in line_stripped.lower() or "warning" in line_stripped.lower()
        ):
            print(f"\n  {line_stripped}")

    try:
        result = compress_audio_service(
            input_path=input_path,
            output_path=output_path,
            bitrate=bitrate,
            volume_gain_db=volume_gain_db,
            denoise_level=denoise,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            on_progress=reporter.report,
            on_output=on_output,
        )

        if result.is_success:
            # Show 100% progress bar
            if total_duration > 0:
                reporter.report_complete()
            print()  # New line after progress bar
            print(f"  {CYAN}{'─' * 48}{RESET}")

            # Build results section
            output_size_mb = result.output_size / (1024 * 1024)
            input_size_mb = result.input_size / (1024 * 1024)

            result_rows = [
                ("Input:      ", f"{input_size_mb:.2f} MB"),
                ("Output:     ", f"{output_size_mb:.2f} MB"),
                ("Reduction:  ", (f"{result.compression_ratio:.1f}%", GREEN)),
                ("MP3 bitrate:", result.bitrate),
            ]

            # Display average statistics
            stats = result.metadata
            if stats and stats.get("avg_speed"):
                result_rows.append(
                    (
                        "Avg speed:  ",
                        f"{stats['avg_speed']:.2f}x",
                    )
                )

            print_header("Compression Results", result_rows, color=GREEN)
            print()

        elif result.is_cancelled:
            print("\n\n  Compression interrupted by user.")
            sys.exit(1)
        else:
            print(f"\n  {RED}Error: {result.error_message}{RESET}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n  Compression interrupted by user.")
        sys.exit(1)


def compress_audio_service(  # noqa: PLR0911, PLR0912, PLR0913, PLR0915
    input_path: str | Path,
    output_path: str | Path | None = None,
    bitrate: str | None = None,
    volume_gain_db: float | None = None,
    denoise_level: float | None = None,
    keep_metadata: bool = True,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    on_progress: ProgressCallback | None = None,
    on_output: OutputCallback | None = None,
    cancellation_source: CancellationSource | None = None,
) -> AudioCompressionResult:
    """Compress audio file to MP3 using FFmpeg (service layer).

    This function is designed for API/GUI use and returns structured results
    without side effects (no print/exit). Progress is reported via callback.

    Args:
        input_path: Input audio file path
        output_path: Output audio file path (optional, defaults to .mp3)
        bitrate: MP3 bitrate (default: DEFAULT_MP3_BITRATE)
        volume_gain_db: Volume gain in dB (default: None)
        denoise_level: Denoise level 0.0-1.0 (default: None)
        keep_metadata: Whether to preserve metadata (default: True)
        ffmpeg_path: Path to ffmpeg executable
        ffprobe_path: Path to ffprobe executable
        on_progress: Callback for progress updates
        on_output: Callback for raw output lines
        cancellation_source: Source for cancellation requests

    Returns:
        AudioCompressionResult with status and metadata
    """
    if bitrate is None:
        bitrate = DEFAULT_MP3_BITRATE

    input_path = Path(input_path)

    if not input_path.exists():
        return AudioCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message=f"Input file '{input_path}' does not exist",
        )

    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_compressed.mp3"
    else:
        output_path = Path(output_path)
        if output_path.suffix.lower() != ".mp3":
            output_path = output_path.with_suffix(".mp3")

    audio_info = get_audio_info_safe(input_path, ffprobe_path)

    if not audio_info:
        return AudioCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message="Could not retrieve audio information",
        )

    total_duration = audio_info["duration"] or 0
    original_bitrate = audio_info["bitrate"]
    sr_val = audio_info.get("sample_rate")
    ch_val = audio_info.get("channels")
    sample_rate = int(sr_val) if sr_val is not None else None
    channels = int(ch_val) if ch_val is not None else None

    bitrate_kbps = parse_bitrate(bitrate)
    if bitrate_kbps < MP3_BITRATE_MIN:
        bitrate = f"{MP3_BITRATE_MIN}k"
    elif bitrate_kbps > MP3_BITRATE_MAX:
        bitrate = f"{MP3_BITRATE_MAX}k"

    cmd = [ffmpeg_path, "-i", str(input_path), "-y"]

    audio_filter = build_audio_filter(volume_gain_db, denoise_level)
    if audio_filter:
        cmd.extend(["-af", audio_filter])

    cmd.extend(
        [
            "-c:a",
            MP3_CODEC,
            "-b:a",
            bitrate,
        ]
    )

    if keep_metadata:
        cmd.extend(["-map_metadata", "0"])

    cmd.append(str(output_path))

    input_size = input_path.stat().st_size
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

        parser = ProgressParser(total_duration)
        parser.set_start_time(time.time())

        if process.stdout:
            for line in process.stdout:
                if cancellation_source and cancellation_source.is_cancelled:
                    process.terminate()
                    process.wait()
                    return AudioCompressionResult(
                        status=CompressionStatus.CANCELLED,
                        input_path=str(input_path),
                        output_path=str(output_path),
                        input_size=input_size,
                        duration=total_duration,
                        sample_rate=sample_rate,
                        channels=channels,
                        audio_codec=MP3_CODEC,
                        bitrate=bitrate,
                    )

                event = parser.parse_line(line)
                if event:
                    if event.fps > 0 and event.speed > 0:
                        stats["fps_list"].append(event.fps)
                        stats["speed_list"].append(event.speed)
                        stats["frame_list"].append(event.frame)

                    if on_progress:
                        on_progress(event)
                elif on_output:
                    on_output(line)

        process.wait()

        if process.returncode == 0:
            output_size = output_path.stat().st_size
            compression_ratio = (1 - output_size / input_size) * 100

            return AudioCompressionResult(
                status=CompressionStatus.SUCCESS,
                input_path=str(input_path),
                output_path=str(output_path),
                input_size=input_size,
                output_size=output_size,
                compression_ratio=compression_ratio,
                duration=total_duration,
                sample_rate=sample_rate,
                channels=channels,
                audio_codec=MP3_CODEC,
                bitrate=bitrate,
                metadata={
                    "original_bitrate": original_bitrate,
                    "avg_fps": sum(stats["fps_list"]) / len(stats["fps_list"])
                    if stats["fps_list"]
                    else 0,
                    "avg_speed": sum(stats["speed_list"]) / len(stats["speed_list"])
                    if stats["speed_list"]
                    else 0,
                },
            )
        else:
            return AudioCompressionResult(
                status=CompressionStatus.FAILED,
                input_path=str(input_path),
                input_size=input_size,
                duration=total_duration,
                error_message=f"FFmpeg exited with code {process.returncode}",
                sample_rate=sample_rate,
                channels=channels,
                audio_codec=MP3_CODEC,
                bitrate=bitrate,
            )

    except FileNotFoundError:
        return AudioCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            input_size=input_size,
            error_message="FFmpeg not found",
        )
    except Exception as e:
        return AudioCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            input_size=input_size,
            error_message=str(e),
        )
    finally:
        if process and process.poll() is None:
            process.terminate()
            process.wait()


def analyze_audio_volume_service(
    input_path: str | Path,
    ffmpeg_path: str = "ffmpeg",
) -> VolumeAnalysisResult:
    """Analyze volume level of audio file (service layer).

    Args:
        input_path: Input audio file path
        ffmpeg_path: Path to ffmpeg executable

    Returns:
        VolumeAnalysisResult with volume information
    """
    input_path = Path(input_path)

    if not input_path.exists():
        return VolumeAnalysisResult(
            mean_volume=None,
            max_volume=None,
            recommended_gain=None,
            target_level=TARGET_VOLUME_LEVEL,
        )

    volume_info = analyze_volume_level(input_path, ffmpeg_path)

    return VolumeAnalysisResult(
        mean_volume=volume_info["mean_volume"],
        max_volume=volume_info["max_volume"],
        recommended_gain=volume_info["recommended_gain"],
        target_level=TARGET_VOLUME_LEVEL,
    )
