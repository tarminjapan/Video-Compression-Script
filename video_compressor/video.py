"""Video compression functionality.

This module provides both CLI-oriented functions and service-layer functions
for video compression. The service layer functions return structured results
without side effects (print/exit), making them suitable for API and GUI use.
"""

import subprocess
import sys
import time
from pathlib import Path

from .config import (
    AUDIO_CODEC,
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_CRF,
    MAX_AUDIO_BITRATE,
    TARGET_VOLUME_LEVEL,
    VIDEO_CODEC,
    VIDEO_PRESET,
)
from .ffmpeg import get_detailed_media_info, get_video_info, get_video_info_safe
from .models import (
    CompressionStatus,
    VideoCompressionResult,
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
    calculate_scaled_resolution,
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


def format_bitrate(bitrate):
    """Format bitrate to human readable string."""
    if bitrate is None:
        return "Unknown"
    try:
        bitrate = int(bitrate)
        if bitrate >= 1000000:
            return f"{bitrate / 1000000:.2f} Mbps"
        elif bitrate >= 1000:
            return f"{bitrate / 1000:.0f} kbps"
        else:
            return f"{bitrate} bps"
    except (ValueError, TypeError):
        return "Unknown"


def format_duration(seconds):
    """Format duration seconds to HH:MM:SS.ms format."""
    if seconds is None:
        return "Unknown"
    try:
        seconds = float(seconds)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        else:
            return f"{minutes:02d}:{secs:06.3f}"
    except (ValueError, TypeError):
        return "Unknown"


def format_file_size(size_bytes):
    """Format file size to human readable string."""
    if size_bytes is None:
        return "Unknown"
    try:
        size_bytes = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    except (ValueError, TypeError):
        return "Unknown"


def analyze_media(  # noqa: PLR0912, PLR0915
    input_path,
    _ffmpeg_path="ffmpeg",
    ffprobe_path="ffprobe",
):
    """Analyze media file and display detailed information.

    Args:
        input_path (str): Input media file path
        ffmpeg_path (str): Path to ffmpeg executable
        ffprobe_path (str): Path to ffprobe executable
    """
    input_path = Path(input_path)

    # Validate input file
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    print("=" * 60)
    print("MEDIA ANALYSIS")
    print("=" * 60)
    print(f"\nFile: {input_path.name}")
    print(f"Path: {input_path.parent}")
    print("-" * 60)

    # Get detailed media info
    media_info = get_detailed_media_info(input_path, ffprobe_path)

    if not media_info:
        print("Error: Could not retrieve media information.")
        sys.exit(1)

    # Format information
    format_info = media_info.get("format", {})
    streams = media_info.get("streams", [])

    # General file information
    print("\n[General Information]")
    print(f"  Format:         {format_info.get('format_long_name', 'Unknown')}")
    print(f"  Format (short): {format_info.get('format_name', 'Unknown')}")
    print(f"  Duration:       {format_duration(format_info.get('duration'))}")
    print(f"  File size:      {format_file_size(format_info.get('size'))}")
    print(f"  Overall bitrate:{format_bitrate(format_info.get('bit_rate'))}")

    # Number of streams
    nb_streams = format_info.get("nb_streams", 0)
    print(
        f"  Streams:        {nb_streams} ({sum(1 for s in streams if s.get('codec_type') == 'video')} video, {sum(1 for s in streams if s.get('codec_type') == 'audio')} audio)"
    )

    # Metadata
    tags = format_info.get("tags", {})
    if tags:
        print("\n[Metadata]")
        for key, value in tags.items():
            print(f"  {key}: {value}")

    # Analyze each stream
    for i, stream in enumerate(streams):
        codec_type = stream.get("codec_type", "unknown")
        print("\n" + "-" * 60)
        print(f"[Stream #{i}] Type: {codec_type.upper()}")
        print("-" * 60)

        if codec_type == "video":
            print(
                f"  Codec:          {stream.get('codec_long_name', stream.get('codec_name', 'Unknown'))}"
            )
            print(f"  Codec (short):  {stream.get('codec_name', 'Unknown')}")
            print(f"  Profile:        {stream.get('profile', 'Unknown')}")
            print(f"  Level:          {stream.get('level', 'Unknown')}")

            # Resolution
            width = stream.get("width")
            height = stream.get("height")
            if width and height:
                print(f"  Resolution:     {width} x {height}")

            # Aspect ratio
            dar = stream.get("display_aspect_ratio")
            if dar:
                print(f"  Aspect Ratio:   {dar}")

            # Frame rate
            fps_str = stream.get("r_frame_rate") or stream.get("avg_frame_rate")
            if fps_str:
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    try:
                        if float(den) != 0:
                            fps = float(num) / float(den)
                            print(f"  Frame Rate:     {fps:.3f} fps ({fps_str})")
                        else:
                            print(f"  Frame Rate:     {fps_str}")
                    except ValueError:
                        print(f"  Frame Rate:     {fps_str}")
                else:
                    print(f"  Frame Rate:     {fps_str} fps")

            # Bit depth
            bits_per_raw = stream.get("bits_per_raw_sample") or stream.get("bits_per_sample")
            if bits_per_raw:
                print(f"  Bit Depth:      {bits_per_raw}-bit")

            # Color information
            pix_fmt = stream.get("pix_fmt")
            if pix_fmt:
                print(f"  Pixel Format:   {pix_fmt}")

            color_space = stream.get("color_space")
            if color_space:
                print(f"  Color Space:    {color_space}")

            color_range = stream.get("color_range")
            if color_range:
                print(f"  Color Range:    {color_range}")

            # Bitrate
            bitrate = stream.get("bit_rate")
            if bitrate:
                print(f"  Bitrate:        {format_bitrate(bitrate)}")

            # Encoding
            is_hdr = stream.get("color_transfer") in ["smpte2084", "arib-std-b67"]
            if is_hdr:
                print(f"  HDR:            Yes ({stream.get('color_transfer', 'Unknown')})")

        elif codec_type == "audio":
            print(
                f"  Codec:          {stream.get('codec_long_name', stream.get('codec_name', 'Unknown'))}"
            )
            print(f"  Codec (short):  {stream.get('codec_name', 'Unknown')}")
            print(f"  Profile:        {stream.get('profile', 'Unknown')}")

            # Sample rate
            sample_rate = stream.get("sample_rate")
            if sample_rate:
                print(f"  Sample Rate:    {sample_rate} Hz")

            # Channels
            channels = stream.get("channels")
            channel_layout = stream.get("channel_layout")
            if channels:
                ch_str = f"{channels} channels"
                if channel_layout:
                    ch_str += f" ({channel_layout})"
                print(f"  Channels:       {ch_str}")

            # Bit depth
            bits_per_sample = stream.get("bits_per_sample") or stream.get("bits_per_raw_sample")
            if bits_per_sample and int(bits_per_sample) > 0:
                print(f"  Bit Depth:      {bits_per_sample}-bit")

            # Bitrate
            bitrate = stream.get("bit_rate")
            if bitrate:
                print(f"  Bitrate:        {format_bitrate(bitrate)}")

            # Language
            language = stream.get("tags", {}).get("language")
            if language:
                print(f"  Language:       {language}")

        # Stream tags/metadata
        stream_tags = stream.get("tags", {})
        if stream_tags and codec_type not in ["video", "audio"]:
            for key, value in stream_tags.items():
                print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Analysis completed.")
    print("=" * 60)


def compress_video(  # noqa: PLR0912, PLR0913, PLR0915
    input_path,
    output_path=None,
    crf=None,
    preset=None,
    audio_bitrate=None,
    audio_enabled=True,
    max_fps=None,
    resolution=None,
    volume_gain=None,
    denoise=None,
    analyze_only=False,
    ffmpeg_path="ffmpeg",
    ffprobe_path="ffprobe",
):
    """Compress video using FFmpeg with AV1 codec.

    Args:
        input_path (str): Input video file path
        output_path (str): Output video file path (optional)
        crf (int): AV1 CRF value (default: DEFAULT_CRF)
        preset (int): Encoding preset (default: VIDEO_PRESET)
        audio_bitrate (str): Audio bitrate (default: DEFAULT_AUDIO_BITRATE)
        audio_enabled (bool): Whether to include audio (default: True)
        max_fps (int): Maximum FPS (default: None = keep original)
        resolution (str): Custom resolution in WxH format (default: None)
        volume_gain (str): Volume gain (e.g., "2.0", "10dB", "auto", None)
        denoise (float): Denoise level 0.0-1.0 (None = disabled)
        analyze_only (bool): Only analyze volume, don't compress
        ffmpeg_path (str): Path to ffmpeg executable
        ffprobe_path (str): Path to ffprobe executable
    """
    # Set default values
    if crf is None:
        crf = DEFAULT_CRF
    if preset is None:
        preset = VIDEO_PRESET
    if audio_bitrate is None:
        audio_bitrate = DEFAULT_AUDIO_BITRATE
    input_path = Path(input_path)

    # Validate input file
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    # Set default output path
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"
    else:
        output_path = Path(output_path)

    # Get video information
    video_info = get_video_info(input_path, ffprobe_path)

    if not video_info:
        print("Error: Could not retrieve video information.")
        sys.exit(1)

    original_width = video_info["width"]
    original_height = video_info["height"]
    original_fps = video_info["fps"]
    total_duration = video_info["duration"] or 0

    # Print analysis section
    duration_str = format_time(total_duration) if total_duration else "Unknown"
    fps_display = f"{original_fps:.2f}" if original_fps else "Unknown"
    print_header(
        "Analysis",
        [
            ("Source:     ", str(input_path)),
            ("Resolution: ", f"{original_width}x{original_height}"),
            ("FPS:        ", fps_display),
            ("Duration:   ", duration_str),
        ],
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

    # Parse custom resolution if provided
    custom_max_width = None
    custom_max_height = None
    if resolution:
        try:
            res_parts = resolution.lower().split("x")
            if len(res_parts) == 2:
                custom_max_width = int(res_parts[0])
                custom_max_height = int(res_parts[1])
        except ValueError:
            print(
                f"  {YELLOW}Warning: Invalid resolution format '{resolution}', using defaults{RESET}"
            )

    # Calculate scaled resolution if needed
    scaled_res = calculate_scaled_resolution(
        original_width, original_height, custom_max_width, custom_max_height
    )

    # Build settings rows for display
    settings_rows = []

    # Resolution info
    if scaled_res:
        scaled_width, scaled_height = scaled_res
        settings_rows.append(
            (
                "Resolution: ",
                f"{scaled_width}x{scaled_height} (from {original_width}x{original_height})",
            )
        )
    else:
        settings_rows.append(("Resolution: ", f"{original_width}x{original_height} (no change)"))

    # Add FPS info
    fps_label = ""
    if max_fps is not None and original_fps and original_fps > max_fps:
        fps_label = f"{max_fps} fps (from {original_fps:.2f})"
    elif max_fps is not None and not original_fps:
        fps_label = f"{max_fps} fps (limit applied, original unknown)"
    elif max_fps is not None:
        fps_label = f"{max_fps} fps (original: {original_fps:.2f}, no change)"
    elif original_fps:
        fps_label = f"{original_fps:.2f} (original)"
    else:
        fps_label = "Unknown"
    settings_rows.append(("FPS:        ", fps_label))

    settings_rows.append(("Video:      ", f"{VIDEO_CODEC.upper()} | CRF {crf} | Preset {preset}"))

    # Audio info
    if audio_enabled:
        settings_rows.append(("Audio:      ", f"{AUDIO_CODEC.upper()} @ {audio_bitrate}"))
    else:
        settings_rows.append(("Audio:      ", "Disabled"))

    # Print settings section
    print_header(
        "Compression Settings",
        settings_rows,
    )

    # Print progress header
    print(f"\n  {BOLD}Starting compression...{RESET}")
    print(f"  {CYAN}{'─' * 48}{RESET}")

    # Execute via service layer
    reporter = CLIProgressReporter(total_duration)

    def on_output(line):
        line_stripped = line.strip()
        if line_stripped and (
            "error" in line_stripped.lower() or "warning" in line_stripped.lower()
        ):
            print(f"\n  {line_stripped}")

    try:
        result = compress_video_service(
            input_path=input_path,
            output_path=output_path,
            crf=crf,
            preset=preset,
            audio_bitrate=audio_bitrate,
            audio_enabled=audio_enabled,
            max_fps=max_fps,
            resolution=resolution,
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
            ]

            # Display average statistics
            stats = result.metadata
            if stats and stats.get("avg_fps"):
                result_rows.append(
                    (
                        "Avg speed:  ",
                        f"{stats['avg_fps']:.1f} fps · {stats['avg_speed']:.2f}x · {stats['total_frames']} frames",
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


def compress_video_service(  # noqa: PLR0911, PLR0912, PLR0913, PLR0915
    input_path: str | Path,
    output_path: str | Path | None = None,
    crf: int | None = None,
    preset: int | None = None,
    audio_bitrate: str | None = None,
    audio_enabled: bool = True,
    max_fps: int | None = None,
    resolution: str | None = None,
    volume_gain_db: float | None = None,
    denoise_level: float | None = None,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    on_progress: ProgressCallback | None = None,
    on_output: OutputCallback | None = None,
    cancellation_source: CancellationSource | None = None,
) -> VideoCompressionResult:
    """Compress video using FFmpeg with AV1 codec (service layer).

    This function is designed for API/GUI use and returns structured results
    without side effects (no print/exit). Progress is reported via callback.

    Args:
        input_path: Input video file path
        output_path: Output video file path (optional)
        crf: AV1 CRF value (default: DEFAULT_CRF)
        preset: Encoding preset (default: VIDEO_PRESET)
        audio_bitrate: Audio bitrate (default: DEFAULT_AUDIO_BITRATE)
        audio_enabled: Whether to include audio (default: True)
        max_fps: Maximum FPS (default: None = keep original)
        resolution: Custom resolution in WxH format (default: None)
        volume_gain_db: Volume gain in dB (default: None)
        denoise_level: Denoise level 0.0-1.0 (default: None)
        ffmpeg_path: Path to ffmpeg executable
        ffprobe_path: Path to ffprobe executable
        on_progress: Callback for progress updates
        on_output: Callback for raw output lines
        cancellation_source: Source for cancellation requests

    Returns:
        VideoCompressionResult with status and metadata
    """
    if crf is None:
        crf = DEFAULT_CRF
    if preset is None:
        preset = VIDEO_PRESET
    if audio_bitrate is None:
        audio_bitrate = DEFAULT_AUDIO_BITRATE

    input_path = Path(input_path)

    if not input_path.exists():
        return VideoCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message=f"Input file '{input_path}' does not exist",
        )

    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"
    else:
        output_path = Path(output_path)

    video_info = get_video_info_safe(input_path, ffprobe_path)

    if not video_info:
        return VideoCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message="Could not retrieve video information",
        )

    original_width = video_info["width"]
    original_height = video_info["height"]
    original_fps = video_info["fps"]
    total_duration = video_info["duration"] or 0
    output_fps = max_fps if max_fps is not None else original_fps

    custom_max_width = None
    custom_max_height = None
    if resolution:
        try:
            res_parts = resolution.lower().split("x")
            if len(res_parts) == 2:
                custom_max_width = int(res_parts[0])
                custom_max_height = int(res_parts[1])
        except ValueError:
            pass

    scaled_res = calculate_scaled_resolution(
        original_width, original_height, custom_max_width, custom_max_height
    )

    cmd = [ffmpeg_path, "-i", str(input_path), "-y"]

    video_filters = []
    if scaled_res:
        scaled_width, scaled_height = scaled_res
        video_filters.append(f"scale={scaled_width}:{scaled_height}")

    if max_fps is not None:
        video_filters.append(f"fps={max_fps}")

    if video_filters:
        cmd.extend(["-vf", ",".join(video_filters)])

    cmd.extend(
        [
            "-c:v",
            VIDEO_CODEC,
            "-crf",
            str(crf),
            "-b:v",
            "0",
            "-preset",
            str(preset),
        ]
    )

    if audio_enabled:
        bitrate_kbps = parse_bitrate(audio_bitrate)
        if bitrate_kbps > MAX_AUDIO_BITRATE:
            audio_bitrate = f"{MAX_AUDIO_BITRATE}k"

        audio_filter = build_audio_filter(volume_gain_db, denoise_level)
        if audio_filter:
            cmd.extend(["-af", audio_filter])

        cmd.extend(
            [
                "-c:a",
                AUDIO_CODEC,
                "-b:a",
                audio_bitrate,
            ]
        )
    else:
        cmd.extend(["-an"])

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
                    return VideoCompressionResult(
                        status=CompressionStatus.CANCELLED,
                        input_path=str(input_path),
                        output_path=str(output_path),
                        input_size=input_size,
                        duration=total_duration,
                        width=scaled_res[0] if scaled_res else original_width,
                        height=scaled_res[1] if scaled_res else original_height,
                        fps=output_fps,
                        video_codec=VIDEO_CODEC,
                        audio_codec=AUDIO_CODEC if audio_enabled else "",
                        crf=crf,
                        preset=preset,
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

            return VideoCompressionResult(
                status=CompressionStatus.SUCCESS,
                input_path=str(input_path),
                output_path=str(output_path),
                input_size=input_size,
                output_size=output_size,
                compression_ratio=compression_ratio,
                duration=total_duration,
                width=scaled_res[0] if scaled_res else original_width,
                height=scaled_res[1] if scaled_res else original_height,
                fps=output_fps,
                video_codec=VIDEO_CODEC,
                audio_codec=AUDIO_CODEC if audio_enabled else "",
                crf=crf,
                preset=preset,
                metadata={
                    "avg_fps": sum(stats["fps_list"]) / len(stats["fps_list"])
                    if stats["fps_list"]
                    else 0,
                    "avg_speed": sum(stats["speed_list"]) / len(stats["speed_list"])
                    if stats["speed_list"]
                    else 0,
                    "total_frames": stats["frame_list"][-1] if stats["frame_list"] else 0,
                },
            )
        else:
            return VideoCompressionResult(
                status=CompressionStatus.FAILED,
                input_path=str(input_path),
                input_size=input_size,
                duration=total_duration,
                error_message=f"FFmpeg exited with code {process.returncode}",
                width=original_width,
                height=original_height,
                fps=original_fps,
                video_codec=VIDEO_CODEC,
                audio_codec=AUDIO_CODEC if audio_enabled else "",
                crf=crf,
                preset=preset,
            )

    except FileNotFoundError:
        return VideoCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            input_size=input_size,
            error_message="FFmpeg not found",
        )
    except Exception as e:
        return VideoCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            input_size=input_size,
            error_message=str(e),
        )
    finally:
        if process and process.poll() is None:
            process.terminate()
            process.wait()


def analyze_volume_service(
    input_path: str | Path,
    ffmpeg_path: str = "ffmpeg",
) -> VolumeAnalysisResult:
    """Analyze volume level of media file (service layer).

    Args:
        input_path: Input media file path
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
