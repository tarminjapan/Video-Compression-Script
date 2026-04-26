"""Progress event abstraction and cancellation control.

Provides common interfaces for progress reporting and cancellation
that can be used by CLI, GUI, and API layers.
"""

from __future__ import annotations

import re
import time
from typing import Protocol

from .models import ProgressEvent


class ProgressCallback(Protocol):
    """Protocol for progress callback functions."""

    def __call__(self, event: ProgressEvent) -> None:
        """Called with progress updates."""
        ...


class OutputCallback(Protocol):
    """Protocol for raw output callback functions."""

    def __call__(self, line: str) -> None:
        """Called with raw output lines."""
        ...


class CancellationSource:
    """Manages cancellation requests for compression operations.

    This class provides a thread-safe way to signal cancellation
    to running compression operations.
    """

    def __init__(self):
        self._cancelled = False

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True

    def reset(self) -> None:
        """Reset cancellation state."""
        self._cancelled = False


class ProgressParser:
    """Parses FFmpeg output into progress events.

    This class is responsible for parsing FFmpeg's stderr/stdout output
    and extracting progress information into ProgressEvent objects.
    """

    def __init__(self, total_duration: float):
        """Initialize parser with total media duration.

        Args:
            total_duration: Total media duration in seconds
        """
        self.total_duration = total_duration
        self.start_time: float = 0.0

    def set_start_time(self, start_time: float) -> None:
        """Set the compression start time for ETA calculation.

        Args:
            start_time: Unix timestamp when compression started
        """
        self.start_time = start_time

    def parse_line(self, line: str) -> ProgressEvent | None:
        """Parse a single FFmpeg output line into a progress event.

        Args:
            line: FFmpeg output line

        Returns:
            ProgressEvent if progress was parsed, None otherwise
        """
        if self.total_duration <= 0:
            return None

        time_match = re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", line)
        if not time_match:
            return None

        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = float(time_match.group(3))
        media_time = hours * 3600 + minutes * 60 + seconds

        percent = min(100.0, (media_time / self.total_duration) * 100)

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
        if 0 < percent < 100 and self.start_time > 0:
            elapsed_wall = time.time() - self.start_time
            if elapsed_wall > 0:
                eta = elapsed_wall * (100 - percent) / percent

        status = "running"
        if percent >= 100:
            status = "complete"

        return ProgressEvent(
            percent=percent,
            current_time=media_time,
            total_duration=self.total_duration,
            fps=fps,
            speed=speed,
            frame=frame,
            eta=eta,
            status=status,
        )
