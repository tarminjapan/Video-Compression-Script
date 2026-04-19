"""
Threaded FFmpeg compression worker for GUI use.

Provides CompressionWorker that runs FFmpeg in a background thread
and reports progress via callbacks, keeping the GUI responsive.
"""

import re
import subprocess
import threading
import time
from collections.abc import Callable

from ..config import AUDIO_CODEC, MP3_CODEC, VIDEO_CODEC
from ..ffmpeg import get_audio_info, get_ffmpeg_executables, get_video_info
from ..volume import build_audio_filter
from .i18n import t


class CompressionWorker:
    """Runs FFmpeg compression in a background thread with progress callbacks."""

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._cancelled = False
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

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

        self._cancelled = False

        def target():
            try:
                ffmpeg_path, ffprobe_path = get_ffmpeg_executables()

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

        self._cancelled = False

        def target():
            try:
                ffmpeg_path, ffprobe_path = get_ffmpeg_executables()

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
        self._cancelled = True
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

            if self._process.stdout:
                for line in self._process.stdout:
                    if self._cancelled:
                        break

                    progress = self._parse_progress(line, total_duration, start_time)
                    if progress and on_progress:
                        on_progress(progress)

            if self._process:
                self._process.wait()

            if self._cancelled:
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

    @staticmethod
    def _parse_progress(line: str, total_duration: float, start_time: float) -> dict | None:
        time_match = re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", line)
        if not time_match or total_duration <= 0:
            return None

        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = float(time_match.group(3))
        current_time = hours * 3600 + minutes * 60 + seconds
        percent = min(100.0, (current_time / total_duration) * 100)

        fps = 0.0
        fps_match = re.search(r"fps=\s*([\d.]+)", line)
        if fps_match:
            fps = float(fps_match.group(1))

        speed = 0.0
        speed_match = re.search(r"speed=\s*([\d.]+)x", line)
        if speed_match:
            speed = float(speed_match.group(1))

        frame = 0
        frame_match = re.search(r"frame=\s*(\d+)", line)
        if frame_match:
            frame = int(frame_match.group(1))

        eta = 0.0
        elapsed_wall = time.time() - start_time
        if 0 < percent < 100 and elapsed_wall > 0:
            eta = elapsed_wall * (100 - percent) / percent

        return {
            "percent": percent,
            "current_time": current_time,
            "total_duration": total_duration,
            "fps": fps,
            "speed": speed,
            "frame": frame,
            "eta": eta,
        }
