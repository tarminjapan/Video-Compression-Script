"""
Video compression functionality.
"""

import subprocess
import sys
from pathlib import Path

from .config import (
    AUDIO_CODEC,
    CRF_MAX,
    CRF_MIN,
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_CRF,
    MAX_AUDIO_BITRATE,
    MAX_FPS,
    VIDEO_CODEC,
    VIDEO_PRESET,
)
from .ffmpeg import get_detailed_media_info, get_video_info
from .progress import show_final_progress, update_progress
from .utils import calculate_scaled_resolution, format_time, parse_bitrate
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


def analyze_media(
    input_path,
    ffmpeg_path="ffmpeg",
    ffprobe_path="ffprobe",
):
    """
    Analyze media file and display detailed information.

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
            bits_per_raw = stream.get("bits_per_raw_sample") or stream.get(
                "bits_per_sample"
            )
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
                print(
                    f"  HDR:            Yes ({stream.get('color_transfer', 'Unknown')})"
                )

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
            bits_per_sample = stream.get("bits_per_sample") or stream.get(
                "bits_per_raw_sample"
            )
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


def compress_video(
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
    """
    Compress video using FFmpeg with AV1 codec.

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
    from .config import TARGET_VOLUME_LEVEL

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
        output_path = (
            input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"
        )
    else:
        output_path = Path(output_path)

    # Get video information
    print(f"Analyzing video: {input_path}")
    video_info = get_video_info(input_path, ffprobe_path)

    if not video_info:
        print("Error: Could not retrieve video information.")
        sys.exit(1)

    original_width = video_info["width"]
    original_height = video_info["height"]
    original_fps = video_info["fps"]
    total_duration = video_info["duration"] or 0

    print(f"Original resolution: {original_width}x{original_height}")
    if original_fps:
        print(f"Original FPS: {original_fps:.2f}")
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

    # Parse custom resolution if provided
    custom_max_width = None
    custom_max_height = None
    if resolution:
        try:
            res_parts = resolution.lower().split("x")
            if len(res_parts) == 2:
                custom_max_width = int(res_parts[0])
                custom_max_height = int(res_parts[1])
                print(
                    f"Custom resolution limit: {custom_max_width}x{custom_max_height}"
                )
        except ValueError:
            print(f"Warning: Invalid resolution format '{resolution}', using defaults")

    # Calculate scaled resolution if needed
    scaled_res = calculate_scaled_resolution(
        original_width, original_height, custom_max_width, custom_max_height
    )

    # Build ffmpeg command
    cmd = [ffmpeg_path, "-i", str(input_path), "-y"]  # -y to overwrite output

    # Build video filter chain
    video_filters = []

    # Add scaling filter if needed
    if scaled_res:
        scaled_width, scaled_height = scaled_res
        print(
            f"Scaling to {scaled_width}x{scaled_height} while maintaining aspect ratio"
        )
        video_filters.append(f"scale={scaled_width}:{scaled_height}")
    else:
        print("No scaling needed (resolution within limits)")

    # Add FPS filter if needed
    fps_filter = None
    if max_fps is not None and original_fps and original_fps > max_fps:
        print(f"Limiting FPS from {original_fps:.2f} to {max_fps}")
        fps_filter = f"fps={max_fps}"
        video_filters.append(fps_filter)
    elif max_fps is not None and not original_fps:
        print(f"Warning: FPS unknown, applying FPS limit of {max_fps} as a precaution")
        fps_filter = f"fps={max_fps}"
        video_filters.append(fps_filter)
    elif max_fps is not None:
        print(
            f"FPS limit: {max_fps} (original: {f'{original_fps:.2f}' if original_fps else 'unknown'})"
        )

    # Apply video filters if any
    if video_filters:
        cmd.extend(["-vf", ",".join(video_filters)])

    # Video codec settings
    cmd.extend(
        [
            "-c:v",
            VIDEO_CODEC,
            "-crf",
            str(crf),
            "-b:v",
            "0",  # Disable bitrate-based encoding (CRF mode)
            "-preset",
            str(preset),
        ]
    )

    # Audio codec settings
    if audio_enabled:
        # Validate and cap audio bitrate
        bitrate_kbps = parse_bitrate(audio_bitrate)
        if bitrate_kbps > MAX_AUDIO_BITRATE:
            print(
                f"Warning: Audio bitrate capped to {MAX_AUDIO_BITRATE}k (requested: {audio_bitrate})"
            )
            audio_bitrate = f"{MAX_AUDIO_BITRATE}k"

        # Build audio filter for volume and denoise
        audio_filter = build_audio_filter(volume_gain_db, denoise)
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
        print(f"Audio: {AUDIO_CODEC} @ {audio_bitrate}")
    else:
        cmd.extend(["-an"])  # No audio
        print("Audio: Disabled")

    # Output file
    cmd.append(str(output_path))

    # Display command for reference
    print(f"\nFFmpeg command: {' '.join(cmd)}\n")
    print("Starting compression...")
    print("-" * 60)

    # Execute ffmpeg command
    process = None
    stats = {"fps_list": [], "speed_list": [], "frame_list": [], "rolling_data": []}

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,  # Close stdin to prevent blocking
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
            print("✓ Compression completed successfully!")
            print(f"  Output: {output_path}")

            # Get output file size
            output_size = output_path.stat().st_size / (1024 * 1024)  # MB
            input_size = input_path.stat().st_size / (1024 * 1024)  # MB
            compression_ratio = (1 - output_size / input_size) * 100

            print(f"  Input size: {input_size:.2f} MB")
            print(f"  Output size: {output_size:.2f} MB")
            print(f"  Compression: {compression_ratio:.1f}% reduction")

            # Display average statistics
            if stats["fps_list"]:
                avg_fps = sum(stats["fps_list"]) / len(stats["fps_list"])
                avg_speed = sum(stats["speed_list"]) / len(stats["speed_list"])
                total_frames = stats["frame_list"][-1] if stats["frame_list"] else 0
                print(
                    f"  Avg encoding speed: {avg_fps:.1f} fps, {avg_speed:.2f}x | Total frames: {total_frames}"
                )
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
