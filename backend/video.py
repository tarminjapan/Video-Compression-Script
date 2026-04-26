"""Video compression functionality.

This module provides both CLI-oriented functions and service-layer functions
for video compression. The service layer functions return structured results
without side effects (print/exit), making them suitable for API and GUI use.
"""

import contextlib
import subprocess
import time
from pathlib import Path
from typing import Any

from .config import (
    AUDIO_CODEC,
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_CRF,
    MAX_AUDIO_BITRATE,
    VIDEO_CODEC,
    VIDEO_PRESET,
)
from .ffmpeg import get_video_info_safe
from .models import (
    CompressionStatus,
    VideoCompressionParams,
    VideoCompressionResult,
    VolumeAnalysisResult,
)
from .progress_handler import (
    ProgressParser,
)
from .utils import (
    calculate_scaled_resolution,
    parse_bitrate,
)
from .volume import (
    analyze_volume_level,
    build_audio_filter,
)


def format_bitrate(bitrate: int | float | str | None) -> str:
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


def format_duration(seconds: float | str | None) -> str:
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


def format_file_size(size_bytes: float | str | None) -> str:
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


def _prepare_video_command(
    params: VideoCompressionParams,
    video_info: dict[str, Any],
) -> tuple[list[str], tuple[int, int] | None]:
    """Prepare FFmpeg command for video compression."""
    input_path = Path(params.input_path)
    output_path = Path(params.output_path) if params.output_path else None
    crf = params.crf if params.crf is not None else DEFAULT_CRF
    preset = params.preset if params.preset is not None else VIDEO_PRESET
    audio_bitrate = (
        params.audio_bitrate if params.audio_bitrate is not None else DEFAULT_AUDIO_BITRATE
    )

    w_val = video_info.get("width")
    h_val = video_info.get("height")
    original_width = int(w_val) if w_val is not None else None
    original_height = int(h_val) if h_val is not None else None

    custom_max_width = None
    custom_max_height = None
    if params.resolution:
        with contextlib.suppress(ValueError):
            res_parts = params.resolution.lower().split("x")
            if len(res_parts) == 2:
                custom_max_width = int(res_parts[0])
                custom_max_height = int(res_parts[1])

    scaled_res = None
    if original_width is not None and original_height is not None:
        scaled_res = calculate_scaled_resolution(
            original_width, original_height, custom_max_width, custom_max_height
        )

    cmd = [params.ffmpeg_path, "-i", str(input_path), "-y"]

    video_filters = []
    if scaled_res:
        video_filters.append(f"scale={scaled_res[0]}:{scaled_res[1]}")
    if params.max_fps is not None:
        video_filters.append(f"fps={params.max_fps}")
    if video_filters:
        cmd.extend(["-vf", ",".join(video_filters)])

    cmd.extend(["-c:v", VIDEO_CODEC, "-crf", str(crf), "-b:v", "0", "-preset", str(preset)])

    if params.audio_enabled:
        bitrate_kbps = parse_bitrate(audio_bitrate)
        if bitrate_kbps > MAX_AUDIO_BITRATE:
            audio_bitrate = f"{MAX_AUDIO_BITRATE}k"
        audio_filter = build_audio_filter(params.volume_gain_db, params.denoise_level)
        if audio_filter:
            cmd.extend(["-af", audio_filter])
        cmd.extend(["-c:a", AUDIO_CODEC, "-b:a", audio_bitrate])
    else:
        cmd.extend(["-an"])

    cmd.append(str(output_path))
    return cmd, scaled_res


def _handle_video_progress(
    line: str,
    params: VideoCompressionParams,
    parser: ProgressParser,
    stats: dict[str, list[float]],
) -> None:
    """Handle a single line of output from FFmpeg."""
    event = parser.parse_line(line)
    if event:
        if event.fps > 0:
            stats["fps_list"].append(event.fps)
            stats["speed_list"].append(event.speed)
            stats["frame_list"].append(float(event.frame))
        if params.on_progress:
            params.on_progress(event)
    elif params.on_output:
        params.on_output(line)


def compress_video_service(**kwargs: Any) -> VideoCompressionResult:
    """Compress video using FFmpeg with AV1 codec (service layer)."""
    params = VideoCompressionParams(**kwargs)
    input_path = Path(params.input_path)

    if not input_path.exists():
        return VideoCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message=f"Input file '{input_path}' does not exist",
        )

    if not params.output_path:
        params.output_path = input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"

    video_info = get_video_info_safe(input_path, params.ffprobe_path)
    if not video_info:
        return VideoCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message="Could not retrieve video information",
        )

    total_duration = video_info["duration"] or 0
    cmd, scaled_res = _prepare_video_command(params, video_info)

    input_size = input_path.stat().st_size
    stats: dict[str, list[float]] = {"fps_list": [], "speed_list": [], "frame_list": []}
    process = None

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
                if params.cancellation_source and params.cancellation_source.is_cancelled:
                    process.terminate()
                    return VideoCompressionResult(
                        status=CompressionStatus.CANCELLED,
                        input_path=str(input_path),
                        output_path=str(params.output_path),
                        input_size=input_size,
                        duration=total_duration,
                    )
                _handle_video_progress(line, params, parser, stats)

        process.wait()

        if process.returncode == 0:
            output_size = Path(params.output_path).stat().st_size
            return VideoCompressionResult(
                status=CompressionStatus.SUCCESS,
                input_path=str(input_path),
                output_path=str(params.output_path),
                input_size=input_size,
                output_size=output_size,
                compression_ratio=(1 - output_size / input_size) * 100,
                duration=total_duration,
                width=scaled_res[0] if scaled_res else video_info.get("width"),
                height=scaled_res[1] if scaled_res else video_info.get("height"),
                fps=params.max_fps or video_info.get("fps"),
                video_codec=VIDEO_CODEC,
                audio_codec=AUDIO_CODEC if params.audio_enabled else "",
                metadata={
                    "avg_fps": sum(stats["fps_list"]) / len(stats["fps_list"])
                    if stats["fps_list"]
                    else 0,
                    "avg_speed": sum(stats["speed_list"]) / len(stats["speed_list"])
                    if stats["speed_list"]
                    else 0,
                },
            )
        return VideoCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message=f"FFmpeg exited with code {process.returncode}",
        )
    except Exception as e:
        return VideoCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
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
            target_level=-23.0,
        )

    volume_info = analyze_volume_level(input_path, ffmpeg_path)

    return VolumeAnalysisResult(
        mean_volume=volume_info["mean_volume"],
        max_volume=volume_info["max_volume"],
        recommended_gain=volume_info["recommended_gain"],
        target_level=-23.0,
    )
