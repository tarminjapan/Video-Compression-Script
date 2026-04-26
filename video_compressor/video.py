"""Video compression functionality.

This module provides both CLI-oriented functions and service-layer functions
for video compression. The service layer functions return structured results
without side effects (print/exit), making them suitable for API and GUI use.
"""

import subprocess
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
from .ffmpeg import get_video_info_safe
from .models import (
    CompressionStatus,
    VideoCompressionResult,
    VolumeAnalysisResult,
)
from .progress_handler import (
    CancellationSource,
    OutputCallback,
    ProgressCallback,
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

    w_val = video_info.get("width")
    h_val = video_info.get("height")
    original_width = int(w_val) if w_val is not None else None
    original_height = int(h_val) if h_val is not None else None
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

    if original_width is not None and original_height is not None:
        scaled_res = calculate_scaled_resolution(
            original_width, original_height, custom_max_width, custom_max_height
        )
    else:
        scaled_res = None

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
