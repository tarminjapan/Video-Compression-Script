"""
Threaded FFmpeg compression worker for GUI use.

Provides CompressionWorker that runs FFmpeg in a background thread
and reports progress via callbacks, keeping the GUI responsive.
"""

import platform
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path

from ..audio import compress_audio_service
from ..config import AUDIO_CODEC, MP3_CODEC, VIDEO_CODEC
from ..ffmpeg import get_ffmpeg_executables
from ..models import ProgressEvent
from ..progress_handler import CancellationSource
from ..video import compress_video_service
from .i18n import t
from .utils import SettingsManager


class CompressionWorker:
    """Runs FFmpeg compression in a background thread with progress callbacks."""

    def __init__(self):
        self._cancellation_source = CancellationSource()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def cancellation_source(self) -> CancellationSource:
        """Get the cancellation source for external cancellation requests."""
        return self._cancellation_source

    @staticmethod
    def _resolve_ffmpeg_paths():
        settings = SettingsManager.get_instance()
        mode = settings.get("ffmpeg_path_mode", "auto")
        custom_path = settings.get("ffmpeg_path", "")
        if mode == "manual" and custom_path:
            ffmpeg_p = Path(custom_path)
            if ffmpeg_p.exists():
                ffprobe_name = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"
                ffprobe_p = ffmpeg_p.parent / ffprobe_name
                return str(ffmpeg_p), str(ffprobe_p) if ffprobe_p.exists() else "ffprobe"
        return get_ffmpeg_executables()

    @staticmethod
    def _event_to_dict(e: ProgressEvent) -> dict:
        """Convert a ProgressEvent to a dictionary for GUI use."""
        return {
            "percent": e.percent,
            "current_time": e.current_time,
            "total_duration": e.total_duration,
            "fps": e.fps,
            "speed": e.speed,
            "frame": e.frame,
            "eta": e.eta,
        }

    def start_video_compression(
        self,
        input_path: str,
        output_path: str,
        crf: int = 25,
        preset: int = 6,
        audio_bitrate: str = "192k",
        audio_enabled: bool = True,
        max_fps: int | None = None,
        resolution: str | None = None,
        volume_gain_db: float | None = None,
        denoise_level: float | None = None,
        on_progress: Callable[[dict], None] | None = None,
        on_complete: Callable[[dict], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        if self.is_running:
            return

        self._cancellation_source.reset()

        def target():
            try:
                ffmpeg_path, ffprobe_path = self._resolve_ffmpeg_paths()

                result = compress_video_service(
                    input_path=input_path,
                    output_path=output_path,
                    crf=crf,
                    preset=preset,
                    audio_bitrate=audio_bitrate,
                    audio_enabled=audio_enabled,
                    max_fps=max_fps,
                    resolution=resolution,
                    volume_gain_db=volume_gain_db,
                    denoise_level=denoise_level,
                    ffmpeg_path=ffmpeg_path,
                    ffprobe_path=ffprobe_path,
                    on_progress=lambda e: on_progress(self._event_to_dict(e)) if on_progress else None,
                    cancellation_source=self._cancellation_source,
                )

                if result.is_success:
                    if on_complete:
                        on_complete({"status": "success"})
                elif result.is_cancelled:
                    if on_complete:
                        on_complete({"status": "cancelled"})
                else:
                    if on_error:
                        on_error(result.error_message)
            except Exception as e:
                if on_error:
                    on_error(str(e))

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def start_audio_compression(
        self,
        input_path: str,
        output_path: str,
        bitrate: str = "192k",
        keep_metadata: bool = True,
        volume_gain_db: float | None = None,
        denoise_level: float | None = None,
        on_progress: Callable[[dict], None] | None = None,
        on_complete: Callable[[dict], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        if self.is_running:
            return

        self._cancellation_source.reset()

        def target():
            try:
                ffmpeg_path, ffprobe_path = self._resolve_ffmpeg_paths()

                result = compress_audio_service(
                    input_path=input_path,
                    output_path=output_path,
                    bitrate=bitrate,
                    volume_gain_db=volume_gain_db,
                    denoise_level=denoise_level,
                    keep_metadata=keep_metadata,
                    ffmpeg_path=ffmpeg_path,
                    ffprobe_path=ffprobe_path,
                    on_progress=lambda e: on_progress(self._event_to_dict(e)) if on_progress else None,
                    cancellation_source=self._cancellation_source,
                )

                if result.is_success:
                    if on_complete:
                        on_complete({"status": "success"})
                elif result.is_cancelled:
                    if on_complete:
                        on_complete({"status": "cancelled"})
                else:
                    if on_error:
                        on_error(result.error_message)
            except Exception as e:
                if on_error:
                    on_error(str(e))

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def cancel(self):
        """Request cancellation of the current compression operation."""
        self._cancellation_source.cancel()
