"""
Video/Audio compression script package initialization.
"""

__version__ = "1.0.6"

__all__ = [
    "analyze_audio_volume_service",
    "analyze_volume_service",
    "compress_audio",
    "compress_audio_service",
    "compress_video",
    "compress_video_service",
    "main",
    "models",
    "progress_handler",
]

from . import models, progress_handler
from .audio import analyze_audio_volume_service, compress_audio, compress_audio_service
from .cli import main
from .video import analyze_volume_service, compress_video, compress_video_service
