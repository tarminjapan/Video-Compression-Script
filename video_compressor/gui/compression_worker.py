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

from ..config import AUDIO_CODEC, MP3_CODEC, VIDEO_CODEC
from ..ffmpeg import get_audio_info, get_ffmpeg_executables, get_video_info
from ..progress_handler import CancellationSource, ProgressParser
from ..volume import build_audio_filter
from .i18n import t
from .utils import SettingsManager


class CompressionWorker:
    """Runs FFmpeg compression in a background thread with progress callbacks."""

    def __init__(self):
        self._process: subprocess.Popen | None = None
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

                video_info = get_video_info(input_path, ffprobe_path)
                total_duration = video_info.get("duration", 0) if video_info else 0

                cmd = [ffmpeg_path, "-i", str(input_path), "-y"]

                video_filters: list[str] = []
                if resolution:
                    video_filters.append(f"scale={resolution}")
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
                    audio_filter = build_audio_filter(
                        volume_gain_db=volume_gain_db,
                        denoise_level=denoise_level,
                    )
                    cmd.extend(["-c:a", AUDIO_CODEC, "-b:a", audio_bitrate])
                    if audio_filter:
                        cmd.extend(["-af", audio_filter])
                else:
                    cmd.append("-an")

                cmd.append(str(output_path))

                self._run_ffmpeg(cmd, total_duration, on_progress, on_complete, on_error)
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

                audio_info = get_audio_info(input_path, ffprobe_path)
                total_duration = audio_info.get("duration", 0) or 0

                cmd = [ffmpeg_path, "-i", str(input_path), "-y"]

                audio_filter = build_audio_filter(
                    volume_gain_db=volume_gain_db,
                    denoise_level=denoise_level,
                )
                if audio_filter:
                    cmd.extend(["-af", audio_filter])

                cmd.extend(["-c:a", MP3_CODEC, "-b:a", bitrate])
                if keep_metadata:
                    cmd.extend(["-map_metadata", "0"])
                cmd.append(str(output_path))

                self._run_ffmpeg(cmd, total_duration, on_progress, on_complete, on_error)
            except Exception as e:
                if on_error:
                    on_error(str(e))

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def cancel(self):
        """Request cancellation of the current compression operation."""
        self._cancellation_source.cancel()
        if self._process and self._process.poll() is None:
            self._process.terminate()

    def _run_ffmpeg(self, cmd, total_duration, on_progress, on_complete, on_error):
        start_time = time.time()
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                encoding="utf-8",
                errors="replace",
            )

            parser = ProgressParser(total_duration)
            parser.set_start_time(start_time)

            if self._process.stdout:
                for line in self._process.stdout:
                    if self._cancellation_source.is_cancelled:
                        break

                    event = parser.parse_line(line)
                    if event and on_progress:
                        on_progress({
                            "percent": event.percent,
                            "current_time": event.current_time,
                            "total_duration": event.total_duration,
                            "fps": event.fps,
                            "speed": event.speed,
                            "frame": event.frame,
                            "eta": event.eta,
                        })

            if self._process:
                self._process.wait()

            if self._cancellation_source.is_cancelled:
                if on_complete:
                    on_complete({"status": "cancelled"})
            elif self._process and self._process.returncode == 0:
                if on_complete:
                    on_complete({"status": "success"})
            else:
                if on_error:
                    code = self._process.returncode if self._process else -1
                    on_error(t("errors.ffmpeg_exit", code=code))
        except FileNotFoundError:
            if on_error:
                on_error(t("errors.ffmpeg_not_found"))
        except Exception as e:
            if on_error:
                on_error(str(e))
        finally:
            self._process = None
