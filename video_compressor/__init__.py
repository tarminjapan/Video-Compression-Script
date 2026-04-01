"""
Video/Audio compression script package initialization.
"""

__version__ = "1.0.6"

__all__ = ["compress_audio", "compress_video", "main"]

from .audio import compress_audio
from .cli import main
from .video import compress_video
