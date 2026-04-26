"""Audio compression functionality.

This module provides both CLI-oriented functions and service-layer functions
for audio compression. The service layer functions return structured results
without side effects (print/exit), making them suitable for API and GUI use.
"""

import subprocess
import time
from pathlib import Path

from .config import (
    DEFAULT_MP3_BITRATE,
    MP3_BITRATE_MAX,
    MP3_BITRATE_MIN,
    MP3_CODEC,
    TARGET_VOLUME_LEVEL,
)
from .ffmpeg import get_audio_info_safe
from .models import (
    AudioCompressionResult,
    CompressionStatus,
    VolumeAnalysisResult,
)
from .progress_handler import (
    CancellationSource,
    OutputCallback,
    ProgressCallback,
    ProgressParser,
)
from .utils import (
    parse_bitrate,
)
from .volume import (
    analyze_volume_level,
    build_audio_filter,
)


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
