#!/usr/bin/env python3
"""
Video/Audio Compression Script using FFmpeg
- Video: Maximum resolution 4K (3840x2160), SVT-AV1 codec (CRF 25), max 120 FPS
- Audio: AAC for video (max 320kbps), MP3 for audio files (max 320kbps)
"""

import argparse
import platform
import re
import subprocess
import sys
from pathlib import Path

# ============================================
# Settings & Constants (Customize here)
# ============================================

# Resolution settings (4K = 3840x2160)
MAX_WIDTH = 3840  # Maximum width
MAX_HEIGHT = 2160  # Maximum height

# Video codec settings
VIDEO_CODEC = "libsvtav1"  # Video codec (SVT-AV1)
DEFAULT_CRF = 25  # CRF value (0-63, lower = higher quality/larger, higher = lower quality/smaller)
VIDEO_PRESET = 6  # Encoding speed preset (0-13, higher = faster)
DEFAULT_FPS = None  # Default FPS (None = keep original)
MAX_FPS = 120  # Maximum FPS

# Audio codec settings (for video)
AUDIO_CODEC = "aac"  # Audio codec (AAC)
DEFAULT_AUDIO_BITRATE = "192k"  # Default audio bitrate
MAX_AUDIO_BITRATE = 320  # Maximum audio bitrate in kbps
DEFAULT_AUDIO_ENABLED = True  # Audio enabled by default

# MP3 codec settings (for audio-only files)
MP3_CODEC = "libmp3lame"  # MP3 encoder
DEFAULT_MP3_BITRATE = "192k"  # Default MP3 bitrate
MP3_BITRATE_MIN = 32  # Minimum MP3 bitrate in kbps
MP3_BITRATE_MAX = 320  # Maximum MP3 bitrate in kbps

# Volume adjustment settings
DEFAULT_VOLUME_GAIN = (
    None  # Default: disabled (None, or value like "2.0", "10dB", "auto")
)
TARGET_VOLUME_LEVEL = -16  # Target loudness in dB (standard for speech/dialogue)
MAX_VOLUME_LEVEL = -1  # Maximum volume level to prevent clipping (dB)

# Denoise settings
DEFAULT_DENOISE = None  # Default: disabled (None or 0.0-1.0)
DENOISE_MIN = 0.0  # Minimum denoise level
DENOISE_MAX = 1.0  # Maximum denoise level
DEFAULT_DENOISE_LEVEL = (
    0.15  # Default denoise level when --denoise is used without value
)

# Supported file extensions
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".ts",
    ".mts",
    ".m2ts",
}
AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".m4a",
    ".ogg",
    ".wma",
    ".ape",
    ".alac",
}

# CRF value range
CRF_MIN = 0
CRF_MAX = 63

# Progress bar settings
PROGRESS_BAR_LENGTH = 30

# ============================================


def get_ffmpeg_executables():
    """
    Detect OS and return appropriate FFmpeg executable paths.
    Checks for local FFmpeg executables in the script root directory first.

    Returns:
        tuple: (ffmpeg_path, ffprobe_path)
    """
    script_dir = Path(__file__).parent.resolve()

    # Determine executable names based on OS
    is_windows = platform.system() == "Windows"
    ffmpeg_name = "ffmpeg.exe" if is_windows else "ffmpeg"
    ffprobe_name = "ffprobe.exe" if is_windows else "ffprobe"

    # Check for local FFmpeg executables
    local_ffmpeg = script_dir / ffmpeg_name
    local_ffprobe = script_dir / ffprobe_name

    if local_ffmpeg.exists() and local_ffprobe.exists():
        print(f"Using local FFmpeg: {local_ffmpeg}")
        return str(local_ffmpeg), str(local_ffprobe)

    # Fall back to system FFmpeg
    return "ffmpeg", "ffprobe"


def format_time(seconds):
    """
    Format seconds to MM:SS.s format.

    Args:
        seconds (float): Time in seconds

    Returns:
        str: Formatted time string
    """
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"


def get_file_type(file_path):
    """
    Determine file type based on extension.

    Args:
        file_path (str or Path): Path to file

    Returns:
        str: "video", "audio", or "unknown"
    """
    ext = Path(file_path).suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    elif ext in AUDIO_EXTENSIONS:
        return "audio"
    return "unknown"


def get_video_info(video_path, ffprobe_path="ffprobe"):
    """
    Get video information using ffprobe.

    Args:
        video_path (str): Path to video file
        ffprobe_path (str): Path to ffprobe executable

    Returns:
        dict: Video width, height, duration, fps
    """
    cmd = [
        ffprobe_path,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,duration",
        "-of",
        "csv=s=x:p=0",
        str(video_path),
    ]

    width = None
    height = None
    fps = None
    duration = None

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output:
            parts = output.split("x")
            if len(parts) >= 2:
                width = int(parts[0])
                remaining = parts[1].split(",")
                height = int(remaining[0])

                # Parse FPS (format: 30/1 or 29.97)
                if len(remaining) > 1:
                    fps_str = remaining[1]
                    if "/" in fps_str:
                        num, den = fps_str.split("/")
                        if float(den) != 0:
                            fps = float(num) / float(den)
                    else:
                        try:
                            fps = float(fps_str)
                        except ValueError:
                            pass

                if len(remaining) > 2:
                    try:
                        duration = float(remaining[2])
                    except ValueError:
                        pass
    except subprocess.CalledProcessError as e:
        print(f"Error getting video info: {e.stderr}")
        sys.exit(1)

    # If duration not found in stream, try format-level duration
    if duration is None:
        format_cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(video_path),
        ]
        try:
            format_result = subprocess.run(
                format_cmd, capture_output=True, text=True, check=True
            )
            format_output = format_result.stdout.strip()
            if format_output:
                try:
                    duration = float(format_output)
                except ValueError:
                    pass
        except subprocess.CalledProcessError:
            pass  # Ignore errors, duration will remain None

    if width is not None and height is not None:
        return {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
        }

    return None


def calculate_scaled_resolution(width, height, max_width=None, max_height=None):
    """
    Calculate scaled resolution while maintaining aspect ratio.

    Args:
        width (int): Original width
        height (int): Original height
        max_width (int): Maximum allowed width (default: MAX_WIDTH)
        max_height (int): Maximum allowed height (default: MAX_HEIGHT)

    Returns:
        tuple: (scaled_width, scaled_height) or None if scaling not needed
    """
    # Set default values
    if max_width is None:
        max_width = MAX_WIDTH
    if max_height is None:
        max_height = MAX_HEIGHT

    # Check if scaling is needed
    if width <= max_width and height <= max_height:
        return None

    # Calculate scaling ratios
    width_ratio = max_width / width
    height_ratio = max_height / height

    # Use smaller ratio to fit within both constraints
    scale_ratio = min(width_ratio, height_ratio)

    # Calculate new dimensions (make even for better encoding quality)
    scaled_width = max(2, int(width * scale_ratio) // 2 * 2)
    scaled_height = max(2, int(height * scale_ratio) // 2 * 2)

    return (scaled_width, scaled_height)


def parse_bitrate(bitrate_str):
    """
    Parse bitrate string to kbps integer.

    Args:
        bitrate_str (str): Bitrate string (e.g., "192k", "320k")

    Returns:
        int: Bitrate in kbps
    """
    bitrate_str = bitrate_str.lower().strip()
    if bitrate_str.endswith("k"):
        return int(bitrate_str[:-1])
    elif bitrate_str.endswith("m"):
        return int(float(bitrate_str[:-1]) * 1000)
    else:
        return int(bitrate_str)


def update_progress(line, total_duration, stats=None):
    """
    Parse progress from FFmpeg log and display progress bar.

    Args:
        line (str): FFmpeg output line
        total_duration (float): Total video duration in seconds
        stats (dict): Dictionary to collect statistics (fps_list, speed_list, frame_list)

    Returns:
        bool: True if progress was displayed, False otherwise
    """
    # Parse time= pattern (e.g., time=00:00:02.33 or time=N/A)
    time_match = re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", line)

    if time_match and total_duration > 0:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = float(time_match.group(3))
        current_time = hours * 3600 + minutes * 60 + seconds

        # Calculate progress percentage (maximum 100%)
        progress = min(100, (current_time / total_duration) * 100)

        # Extract fps
        fps_match = re.search(r"fps=\s*([\d.]+)", line)
        fps = float(fps_match.group(1)) if fps_match else 0.0

        # Extract speed
        speed_match = re.search(r"speed=\s*([\d.]+)x", line)
        speed = float(speed_match.group(1)) if speed_match else 0.0

        # Extract frame count
        frame_match = re.search(r"frame=\s*(\d+)", line)
        frame = int(frame_match.group(1)) if frame_match else 0

        # Collect statistics if stats dictionary is provided
        if stats is not None and fps > 0 and speed > 0:
            stats["fps_list"].append(fps)
            stats["speed_list"].append(speed)
            stats["frame_list"].append(frame)

        # Extract elapsed time and calculate estimated remaining time
        elapsed_match = re.search(r"elapsed=(\d+):(\d+):(\d+\.?\d*)", line)
        eta_str = "--:--"
        if elapsed_match and progress > 0:
            elapsed_hours = int(elapsed_match.group(1))
            elapsed_minutes = int(elapsed_match.group(2))
            elapsed_seconds = float(elapsed_match.group(3))
            elapsed_time = elapsed_hours * 3600 + elapsed_minutes * 60 + elapsed_seconds

            # Estimated remaining time = elapsed time * (remaining progress / current progress)
            if progress < 100:
                remaining_progress = 100 - progress
                eta_seconds = elapsed_time * (remaining_progress / progress)
                eta_str = format_time(eta_seconds)
            else:
                eta_str = "00:00.0"

        # Display progress bar
        filled = int(PROGRESS_BAR_LENGTH * progress / 100)
        bar = "█" * filled + "░" * (PROGRESS_BAR_LENGTH - filled)

        # Format current time
        current_min = int(current_time // 60)
        current_sec = current_time % 60
        total_min = int(total_duration // 60)
        total_sec = total_duration % 60

        # Update the same line (return to beginning of line with \r)
        sys.stdout.write(
            f"\r  [{bar}] {progress:5.1f}% | "
            f"{current_min:02d}:{current_sec:04.1f}/{total_min:02d}:{total_sec:04.1f} | "
            f"ETA {eta_str} | {fps:.0f} fps | {speed:.2f}x | Frame: {frame}"
        )
        sys.stdout.flush()
        return True
    return False


def show_final_progress(total_duration):
    """
    Display 100% progress bar after completion.

    Args:
        total_duration (float): Total video duration in seconds
    """
    bar = "█" * PROGRESS_BAR_LENGTH
    total_min = int(total_duration // 60)
    total_sec = total_duration % 60

    sys.stdout.write(
        f"\r  [{bar}] 100.0% | "
        f"{total_min:02d}:{total_sec:04.1f}/{total_min:02d}:{total_sec:04.1f} | "
        f"ETA 00:00.0 | -- fps | --x | Frame: --"
    )
    sys.stdout.flush()


def get_audio_info(audio_path, ffprobe_path="ffprobe"):
    """
    Get audio information using ffprobe.

    Args:
        audio_path (str): Path to audio file
        ffprobe_path (str): Path to ffprobe executable

    Returns:
        dict: Audio duration, bitrate, sample_rate, channels
    """
    cmd = [
        ffprobe_path,
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=bit_rate,sample_rate,channels,duration",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        str(audio_path),
    ]

    duration = None
    bitrate = None
    sample_rate = None
    channels = None

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output:
            lines = output.split("\n")
            for line in lines:
                parts = line.split(",")
                if len(parts) >= 4:
                    # Stream info: bit_rate, sample_rate, channels, duration
                    try:
                        if parts[0]:
                            bitrate = int(parts[0])
                        if parts[1]:
                            sample_rate = int(parts[1])
                        if parts[2]:
                            channels = int(parts[2])
                        if parts[3]:
                            duration = float(parts[3])
                    except ValueError:
                        pass
                elif len(parts) == 1 and parts[0]:
                    # Format duration (fallback)
                    try:
                        duration = float(parts[0])
                    except ValueError:
                        pass
    except subprocess.CalledProcessError as e:
        print(f"Error getting audio info: {e.stderr}")
        sys.exit(1)

    # If duration not found, try format-level duration
    if duration is None:
        format_cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(audio_path),
        ]
        try:
            format_result = subprocess.run(
                format_cmd, capture_output=True, text=True, check=True
            )
            format_output = format_result.stdout.strip()
            if format_output:
                try:
                    duration = float(format_output)
                except ValueError:
                    pass
        except subprocess.CalledProcessError:
            pass

    return {
        "duration": duration,
        "bitrate": bitrate,
        "sample_rate": sample_rate,
        "channels": channels,
    }


def analyze_volume_level(input_path, ffmpeg_path="ffmpeg"):
    """
    Analyze audio volume level using FFmpeg's volumedetect filter.

    Args:
        input_path (str): Path to input file (video or audio)
        ffmpeg_path (str): Path to ffmpeg executable

    Returns:
        dict: mean_volume (dB), max_volume (dB), recommended_gain (dB)
    """
    cmd = [
        ffmpeg_path,
        "-i",
        str(input_path),
        "-af",
        "volumedetect",
        "-vn",
        "-sn",
        "-dn",
        "-f",
        "null",
        "-",
    ]

    mean_volume = None
    max_volume = None

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",  # Replace undecodable characters to avoid UnicodeDecodeError
            check=False,  # volumedetect outputs to stderr, return code may be 0
        )

        # Parse volumedetect output from stderr (use empty string if None)
        output = result.stderr or ""

        # Parse mean_volume (e.g., [Parsed_volumedetect_0 @ ...] mean_volume: -27.5 dB)
        mean_match = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", output)
        if mean_match:
            mean_volume = float(mean_match.group(1))

        # Parse max_volume (e.g., [Parsed_volumedetect_0 @ ...] max_volume: -5.2 dB)
        max_match = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", output)
        if max_match:
            max_volume = float(max_match.group(1))

    except FileNotFoundError:
        print(
            "Error: FFmpeg not found. Please ensure FFmpeg is installed and added to PATH."
        )
        sys.exit(1)

    # Calculate recommended gain
    recommended_gain = None
    if mean_volume is not None and max_volume is not None:
        recommended_gain = calculate_recommended_gain(mean_volume, max_volume)

    return {
        "mean_volume": mean_volume,
        "max_volume": max_volume,
        "recommended_gain": recommended_gain,
    }


def calculate_recommended_gain(mean_volume, max_volume):
    """
    Calculate recommended volume gain based on current audio levels.

    Args:
        mean_volume (float): Current mean volume in dB
        max_volume (float): Current max volume in dB

    Returns:
        float: Recommended gain in dB
    """
    # Calculate gain needed to reach target level
    gain_for_target = TARGET_VOLUME_LEVEL - mean_volume

    # Calculate maximum safe gain (to prevent clipping)
    # Leave 1dB headroom from 0dB
    max_safe_gain = MAX_VOLUME_LEVEL - max_volume

    # Use the smaller of the two to prevent clipping
    recommended_gain = min(gain_for_target, max_safe_gain)

    # Round to 1 decimal place
    recommended_gain = round(recommended_gain, 1)

    return recommended_gain


def parse_volume_gain(gain_str):
    """
    Parse volume gain string and return gain in dB.

    Args:
        gain_str (str): Gain string (e.g., "2.0", "10dB", "auto")

    Returns:
        tuple: (gain_db, is_auto) where gain_db is the gain in dB,
               and is_auto is True if "auto" was specified
    """
    if gain_str is None:
        return None, False

    gain_str = gain_str.strip()

    # Check for auto mode
    if gain_str.lower() == "auto":
        return None, True

    # Check for dB suffix
    if gain_str.lower().endswith("db"):
        try:
            return float(gain_str[:-2]), False
        except ValueError:
            print(f"Error: Invalid dB value '{gain_str}'")
            sys.exit(1)

    # Treat as multiplier (convert to dB)
    try:
        multiplier = float(gain_str)
        if multiplier <= 0:
            print("Error: Volume multiplier must be positive")
            sys.exit(1)
        # Convert multiplier to dB: dB = 20 * log10(multiplier)
        import math

        gain_db = 20 * math.log10(multiplier)
        return round(gain_db, 1), False
    except ValueError:
        print(f"Error: Invalid volume gain value '{gain_str}'")
        sys.exit(1)


def build_audio_filter(volume_gain_db=None, denoise_level=None):
    """
    Build audio filter string for FFmpeg.

    Args:
        volume_gain_db (float): Volume gain in dB (None = no adjustment)
        denoise_level (float): Denoise level 0.0-1.0 (None = no denoise)

    Returns:
        str: Audio filter string or None if no filters needed
    """
    audio_filters = []

    # Add denoise filter if specified
    if denoise_level is not None and denoise_level > 0:
        # Map 0.0-1.0 to noise reduction amount
        # Higher level = more aggressive noise reduction
        noise_reduction = int(denoise_level * 97)  # 0-97 range for afftdn
        audio_filters.append(f"afftdn=nr={noise_reduction}")

    # Add volume filter if specified
    if volume_gain_db is not None:
        audio_filters.append(f"volume={volume_gain_db}dB")

    if audio_filters:
        return ",".join(audio_filters)

    return None


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
    if denoise is not None:
        if denoise < DENOISE_MIN or denoise > DENOISE_MAX:
            print(
                f"Warning: Denoise level capped to {DENOISE_MIN}-{DENOISE_MAX} (requested: {denoise})"
            )
            denoise = max(DENOISE_MIN, min(DENOISE_MAX, denoise))
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
    if denoise is not None:
        if denoise < DENOISE_MIN or denoise > DENOISE_MAX:
            print(
                f"Warning: Denoise level capped to {DENOISE_MIN}-{DENOISE_MAX} (requested: {denoise})"
            )
            denoise = max(DENOISE_MIN, min(DENOISE_MAX, denoise))
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
    stats = {"fps_list": [], "speed_list": [], "frame_list": []}

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


def main():
    parser = argparse.ArgumentParser(
        description="Compress video/audio using FFmpeg (AV1 for video, MP3 for audio)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Video compression
  %(prog)s input.mp4
  %(prog)s input.mp4 -o output.mp4
  %(prog)s input.mp4 --crf 23 --audio-bitrate 256k
  %(prog)s input.mp4 --resolution 1920x1080 --fps 60
  %(prog)s input.mp4 --no-audio

  # Audio compression (to MP3)
  %(prog)s music.mp3 --audio-bitrate 128k
  %(prog)s audio.wav --audio-bitrate 192k
  %(prog)s song.flac -o compressed.mp3

  # Volume adjustment
  %(prog)s meeting.mp4 --volume-gain auto
  %(prog)s meeting.mp4 --volume-gain 10dB
  %(prog)s meeting.mp4 --volume-gain 2.0
  %(prog)s audio.mp3 --analyze-volume

  # Noise reduction
  %(prog)s meeting.mp4 --denoise
  %(prog)s meeting.mp4 --denoise 0.3
  %(prog)s meeting.mp4 --volume-gain auto --denoise 0.2
        """,
    )

    parser.add_argument("input", nargs="?", help="Input video file path")
    parser.add_argument(
        "-o",
        "--output",
        help="Output video file path (default: input_compressed.ext)",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=DEFAULT_CRF,
        help=f"AV1 CRF value ({CRF_MIN}-{CRF_MAX}, lower = higher quality, higher = smaller size, default: {DEFAULT_CRF})",
    )
    parser.add_argument(
        "--preset",
        type=int,
        default=VIDEO_PRESET,
        help=f"Encoding speed preset (0-13, higher = faster encoding but larger file, default: {VIDEO_PRESET})",
    )
    parser.add_argument(
        "--audio-bitrate",
        default=DEFAULT_AUDIO_BITRATE,
        help=f"Audio bitrate (video: default {DEFAULT_AUDIO_BITRATE}, max {MAX_AUDIO_BITRATE}k | audio/MP3: {MP3_BITRATE_MIN}k-{MP3_BITRATE_MAX}k)",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Disable audio track (audio bitrate option will be ignored)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=None,
        help=f"Maximum FPS (default: keep original, max: {MAX_FPS})",
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default=None,
        help="Maximum resolution in WxH format (e.g., 1920x1080, default: 3840x2160)",
    )
    parser.add_argument(
        "--volume-gain",
        type=str,
        default=None,
        help="Volume gain: multiplier (e.g., '2.0'), dB (e.g., '10dB'), or 'auto' for automatic adjustment",
    )
    parser.add_argument(
        "--analyze-volume",
        action="store_true",
        help="Analyze volume level and show recommended gain (no compression)",
    )
    parser.add_argument(
        "--denoise",
        type=float,
        nargs="?",
        const=DEFAULT_DENOISE_LEVEL,
        default=None,
        help=f"Enable audio noise reduction (level: {DENOISE_MIN}-{DENOISE_MAX}, default: {DEFAULT_DENOISE_LEVEL})",
    )

    args = parser.parse_args()

    # Get FFmpeg executable paths
    ffmpeg_path, ffprobe_path = get_ffmpeg_executables()

    # Get input file path (prompt if not provided)
    input_path = args.input
    if input_path is None:
        input_path = input("Enter the path to the file to compress: ").strip()
        if not input_path:
            print("Error: Input file path not specified.")
            sys.exit(1)

    # Remove surrounding double quotes
    input_path = input_path.strip('"')

    # Determine file type
    file_type = get_file_type(input_path)

    if file_type == "audio":
        # Audio file compression (to MP3)
        compress_audio(
            input_path=input_path,
            output_path=args.output,
            bitrate=args.audio_bitrate,
            volume_gain=args.volume_gain,
            denoise=args.denoise,
            analyze_only=args.analyze_volume,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
    elif file_type == "video":
        # Video file compression
        # Validate CRF value
        if not CRF_MIN <= args.crf <= CRF_MAX:
            print(f"Error: CRF must be between {CRF_MIN} and {CRF_MAX}")
            sys.exit(1)

        # Validate FPS value
        max_fps = args.fps
        if max_fps is not None and max_fps > MAX_FPS:
            print(f"Warning: FPS capped to {MAX_FPS} (requested: {max_fps})")
            max_fps = MAX_FPS

        # Determine audio settings
        audio_enabled = not args.no_audio

        # Run compression
        compress_video(
            input_path=input_path,
            output_path=args.output,
            crf=args.crf,
            preset=args.preset,
            audio_bitrate=args.audio_bitrate,
            audio_enabled=audio_enabled,
            max_fps=max_fps,
            resolution=args.resolution,
            volume_gain=args.volume_gain,
            denoise=args.denoise,
            analyze_only=args.analyze_volume,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
    else:
        print("Error: Unsupported file type. Supported formats:")
        print(f"  Video: {', '.join(sorted(VIDEO_EXTENSIONS))}")
        print(f"  Audio: {', '.join(sorted(AUDIO_EXTENSIONS))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
