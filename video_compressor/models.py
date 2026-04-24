"""
Data models for compression results and progress events.

These models provide a clean interface for returning compression results
and progress information, independent of CLI/GUI/API boundaries.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CompressionStatus(Enum):
    """Status of a compression operation."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressEvent:
    """Progress event emitted during compression.

    Attributes:
        percent: Progress percentage (0.0 - 100.0)
        current_time: Current playback time in seconds
        total_duration: Total media duration in seconds
        fps: Current frames per second
        speed: Encoding speed multiplier
        frame: Current frame number
        eta: Estimated time remaining in seconds
        status: Current status message
    """
    percent: float = 0.0
    current_time: float = 0.0
    total_duration: float = 0.0
    fps: float = 0.0
    speed: float = 0.0
    frame: int = 0
    eta: float = 0.0
    status: str = ""


@dataclass
class CompressionResult:
    """Result of a compression operation.

    Attributes:
        status: Final status of the operation
        input_path: Input file path
        output_path: Output file path (if successful)
        input_size: Input file size in bytes
        output_size: Output file size in bytes (if successful)
        compression_ratio: Compression ratio percentage (if successful)
        duration: Media duration in seconds
        error_message: Error message (if failed)
        metadata: Additional metadata
    """
    status: CompressionStatus
    input_path: str
    output_path: str | None = None
    input_size: int = 0
    output_size: int = 0
    compression_ratio: float = 0.0
    duration: float = 0.0
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if compression was successful."""
        return self.status == CompressionStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """Check if compression failed."""
        return self.status == CompressionStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        """Check if compression was cancelled."""
        return self.status == CompressionStatus.CANCELLED


@dataclass
class VideoCompressionResult(CompressionResult):
    """Result of a video compression operation.

    Attributes:
        width: Output video width
        height: Output video height
        fps: Output video FPS
        video_codec: Video codec used
        audio_codec: Audio codec used
        crf: CRF value used
        preset: Encoding preset used
    """
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    video_codec: str = ""
    audio_codec: str = ""
    crf: int = 0
    preset: int = 0


@dataclass
class AudioCompressionResult(CompressionResult):
    """Result of an audio compression operation.

    Attributes:
        sample_rate: Output sample rate
        channels: Number of channels
        audio_codec: Audio codec used
        bitrate: Audio bitrate
    """
    sample_rate: int | None = None
    channels: int | None = None
    audio_codec: str = ""
    bitrate: str = ""


@dataclass
class VolumeAnalysisResult:
    """Result of volume analysis.

    Attributes:
        mean_volume: Mean volume level in dB
        max_volume: Max volume level in dB
        recommended_gain: Recommended gain adjustment in dB
        target_level: Target volume level in dB
    """
    mean_volume: float | None = None
    max_volume: float | None = None
    recommended_gain: float | None = None
    target_level: float = -23.0

    @property
    def has_data(self) -> bool:
        """Check if analysis has valid data."""
        return self.mean_volume is not None


@dataclass
class MediaInfo:
    """Media information structure.

    Attributes:
        width: Video width (video only)
        height: Video height (video only)
        fps: Video FPS (video only)
        duration: Duration in seconds
        bitrate: Bitrate in bps
        sample_rate: Sample rate in Hz (audio only)
        channels: Number of channels (audio only)
        codec_name: Codec name
        codec_long_name: Full codec name
        format_name: Format name
        metadata: Additional metadata
    """
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    duration: float | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    codec_name: str = ""
    codec_long_name: str = ""
    format_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
