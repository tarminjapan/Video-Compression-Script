"""Audio compression functionality.

This module provides both CLI-oriented functions and service-layer functions
for audio compression. The service layer functions return structured results
without side effects (print/exit), making them suitable for API and GUI use.
"""

import subprocess
import time
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_MP3_BITRATE,
    MP3_BITRATE_MAX,
    MP3_BITRATE_MIN,
    MP3_CODEC,
    TARGET_VOLUME_LEVEL,
)
from .ffmpeg import get_audio_info_safe
from .models import (
    AudioCompressionParams,
    AudioCompressionResult,
    CompressionStatus,
    VolumeAnalysisResult,
)
from .progress_handler import (
    ProgressParser,
)
from .utils import (
    parse_bitrate,
)
from .volume import (
    analyze_volume_level,
    build_audio_filter,
)


def _prepare_audio_command(params: AudioCompressionParams) -> list[str]:
    """Prepare FFmpeg command for audio compression."""
    input_path = Path(params.input_path)
    output_path = Path(params.output_path) if params.output_path else None
    bitrate = params.bitrate if params.bitrate is not None else DEFAULT_MP3_BITRATE

    bitrate_kbps = parse_bitrate(bitrate)
    if bitrate_kbps < MP3_BITRATE_MIN:
        bitrate = f"{MP3_BITRATE_MIN}k"
    elif bitrate_kbps > MP3_BITRATE_MAX:
        bitrate = f"{MP3_BITRATE_MAX}k"

    cmd = [params.ffmpeg_path, "-i", str(input_path), "-y"]

    audio_filter = build_audio_filter(params.volume_gain_db, params.denoise_level)
    if audio_filter:
        cmd.extend(["-af", audio_filter])

    cmd.extend(["-c:a", MP3_CODEC, "-b:a", bitrate])

    if params.keep_metadata:
        cmd.extend(["-map_metadata", "0"])

    cmd.append(str(output_path))
    return cmd


def _handle_audio_progress(
    line: str,
    params: AudioCompressionParams,
    parser: ProgressParser,
    stats: dict[str, list[float]],
) -> None:
    """Handle a single line of output from FFmpeg."""
    event = parser.parse_line(line)
    if event:
        if event.speed > 0:
            stats["speed_list"].append(event.speed)
        if params.on_progress:
            params.on_progress(event)
    elif params.on_output:
        params.on_output(line)


def compress_audio_service(**kwargs: Any) -> AudioCompressionResult:
    """Compress audio file to MP3 using FFmpeg (service layer)."""
    params = AudioCompressionParams(**kwargs)
    input_path = Path(params.input_path)

    if not input_path.exists():
        return AudioCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message=f"Input file '{input_path}' does not exist",
        )

    if not params.output_path:
        params.output_path = input_path.parent / f"{input_path.stem}_compressed.mp3"
    elif Path(params.output_path).suffix.lower() != ".mp3":
        params.output_path = Path(params.output_path).with_suffix(".mp3")

    audio_info = get_audio_info_safe(input_path, params.ffprobe_path)
    if not audio_info:
        return AudioCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message="Could not retrieve audio information",
        )

    total_duration = audio_info["duration"] or 0
    cmd = _prepare_audio_command(params)
    input_size = input_path.stat().st_size
    stats: dict[str, list[float]] = {"speed_list": []}
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
                    return AudioCompressionResult(
                        status=CompressionStatus.CANCELLED,
                        input_path=str(input_path),
                        output_path=str(params.output_path),
                        input_size=input_size,
                        duration=total_duration,
                    )
                _handle_audio_progress(line, params, parser, stats)

        process.wait()

        if process.returncode == 0:
            output_size = Path(params.output_path).stat().st_size
            return AudioCompressionResult(
                status=CompressionStatus.SUCCESS,
                input_path=str(input_path),
                output_path=str(params.output_path),
                input_size=input_size,
                output_size=output_size,
                compression_ratio=(1 - output_size / input_size) * 100,
                duration=total_duration,
                sample_rate=audio_info.get("sample_rate"),
                channels=audio_info.get("channels"),
                audio_codec=MP3_CODEC,
                bitrate=params.bitrate or DEFAULT_MP3_BITRATE,
            )
        return AudioCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
            error_message=f"FFmpeg exited with code {process.returncode}",
        )
    except Exception as e:
        return AudioCompressionResult(
            status=CompressionStatus.FAILED,
            input_path=str(input_path),
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
