"""FFmpeg executable detection and path management."""

import contextlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any


def get_ffmpeg_executables():
    """Detect OS and return appropriate FFmpeg executable paths.
    Checks for local FFmpeg executables in the bin directory first.

    Returns:
        tuple: (ffmpeg_path, ffprobe_path)
    """
    script_dir = Path(__file__).parent.parent.resolve()

    # Determine executable names based on OS
    is_windows = platform.system() == "Windows"
    ffmpeg_name = "ffmpeg.exe" if is_windows else "ffmpeg"
    ffprobe_name = "ffprobe.exe" if is_windows else "ffprobe"

    # Check for local FFmpeg executables in bin directory
    local_ffmpeg = script_dir / "bin" / ffmpeg_name
    local_ffprobe = script_dir / "bin" / ffprobe_name

    if local_ffmpeg.exists() and local_ffprobe.exists():
        print(f"Using local FFmpeg: {local_ffmpeg}")
        return str(local_ffmpeg), str(local_ffprobe)

    # Fall back to system FFmpeg
    return "ffmpeg", "ffprobe"


def get_video_info(video_path: str | Path, ffprobe_path: str = "ffprobe") -> dict[str, Any] | None:
    """Get video information using ffprobe.

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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
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
                        with contextlib.suppress(ValueError):
                            fps = float(fps_str)

                if len(remaining) > 2:
                    with contextlib.suppress(ValueError):
                        duration = float(remaining[2])
    except subprocess.CalledProcessError as e:
        print(f"Error getting video info: {e.stderr}")
        return None

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
                format_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            format_output = format_result.stdout.strip()
            if format_output:
                with contextlib.suppress(ValueError):
                    duration = float(format_output)
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


def get_detailed_media_info(
    media_path: str | Path, ffprobe_path: str = "ffprobe"
) -> dict[str, Any] | None:
    """Get detailed media information using ffprobe.

    Args:
        media_path (str): Path to media file (video or audio)
        ffprobe_path (str): Path to ffprobe executable

    Returns:
        dict: Detailed media information including codecs, bitrate, etc.
    """
    cmd = [
        ffprobe_path,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(media_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        data = json.loads(result.stdout)
        return data
    except subprocess.CalledProcessError:
        return None
    except json.JSONDecodeError:
        return None


def get_audio_info(audio_path: str | Path, ffprobe_path: str = "ffprobe") -> dict[str, Any]:  # noqa: PLR0912
    """Get audio information using ffprobe.

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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
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
                    with contextlib.suppress(ValueError):
                        duration = float(parts[0])
    except subprocess.CalledProcessError as e:
        print(f"Error getting audio info: {e.stderr}")

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
                format_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            format_output = format_result.stdout.strip()
            if format_output:
                with contextlib.suppress(ValueError):
                    duration = float(format_output)
        except subprocess.CalledProcessError:
            pass

    return {
        "duration": duration,
        "bitrate": bitrate,
        "sample_rate": sample_rate,
        "channels": channels,
    }


def get_video_info_safe(  # noqa: PLR0912
    video_path: str | Path, ffprobe_path: str = "ffprobe"
) -> dict[str, Any] | None:
    """Get video information using ffprobe (service layer safe version).

    Unlike get_video_info, this function does not call sys.exit on failure,
    making it safe for API/GUI use.

    Args:
        video_path (str): Path to video file
        ffprobe_path (str): Path to ffprobe executable

    Returns:
        dict: Video width, height, duration, fps, or None on error
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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        output = result.stdout.strip()
        if output:
            parts = output.split("x")
            if len(parts) >= 2:
                width = int(parts[0])
                remaining = parts[1].split(",")
                height = int(remaining[0])

                if len(remaining) > 1:
                    fps_str = remaining[1]
                    if "/" in fps_str:
                        num, den = fps_str.split("/")
                        if float(den) != 0:
                            fps = float(num) / float(den)
                    else:
                        with contextlib.suppress(ValueError):
                            fps = float(fps_str)

                if len(remaining) > 2:
                    with contextlib.suppress(ValueError):
                        duration = float(remaining[2])
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        return None

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
                format_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            format_output = format_result.stdout.strip()
            if format_output:
                with contextlib.suppress(ValueError):
                    duration = float(format_output)
        except subprocess.CalledProcessError:
            pass

    if width is not None and height is not None:
        return {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
        }

    return None


def get_audio_info_safe(  # noqa: PLR0912
    audio_path: str | Path, ffprobe_path: str = "ffprobe"
) -> dict[str, Any] | None:
    """Get audio information using ffprobe (service layer safe version).

    Unlike get_audio_info, this function does not call sys.exit on failure,
    making it safe for API/GUI use.

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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        output = result.stdout.strip()
        if output:
            lines = output.split("\n")
            for line in lines:
                parts = line.split(",")
                if len(parts) >= 4:
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
                    with contextlib.suppress(ValueError):
                        duration = float(parts[0])
    except subprocess.CalledProcessError:
        pass
    except FileNotFoundError:
        pass

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
                format_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            format_output = format_result.stdout.strip()
            if format_output:
                with contextlib.suppress(ValueError):
                    duration = float(format_output)
        except subprocess.CalledProcessError:
            pass

    return {
        "duration": duration,
        "bitrate": bitrate,
        "sample_rate": sample_rate,
        "channels": channels,
    }
