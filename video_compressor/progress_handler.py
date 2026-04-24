"""
Progress event abstraction and cancellation control.

Provides common interfaces for progress reporting and cancellation
that can be used by CLI, GUI, and API layers.
"""

import re
import time
from abc import ABC, abstractmethod
from typing import Protocol

from .models import ProgressEvent


class ProgressCallback(Protocol):
    """Protocol for progress callback functions."""

    def __call__(self, event: ProgressEvent) -> None:
        """Called with progress updates."""
        ...


class CancellationSource:
    """Manages cancellation requests for compression operations.

    This class provides a thread-safe way to signal cancellation
    to running compression operations.

    Example:
        cancel_source = CancellationSource()

        # In compression operation
        if cancel_source.is_cancelled:
            return

        # From external (e.g., GUI button)
        cancel_source.cancel()
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


class ProgressReporter(ABC):
    """Abstract base class for progress reporters.

    Concrete implementations handle progress reporting for different
    interfaces (CLI, GUI, API).
    """

    @abstractmethod
    def report(self, event: ProgressEvent) -> None:
        """Report a progress event.

        Args:
            event: Progress event to report
        """
        pass

    @abstractmethod
    def report_complete(self) -> None:
        """Report completion."""
        pass

    @abstractmethod
    def report_error(self, message: str) -> None:
        """Report an error.

        Args:
            message: Error message
        """
        pass


class CLIProgressReporter(ProgressReporter):
    """CLI implementation of progress reporter.

    Displays progress in the terminal with a progress bar.
    """

    def __init__(self, total_duration: float):
        """Initialize CLI progress reporter.

        Args:
            total_duration: Total media duration in seconds
        """
        self.total_duration = total_duration
        self.parser = ProgressParser(total_duration)
        self._stats = {"fps_list": [], "speed_list": [], "frame_list": []}

    @property
    def stats(self) -> dict:
        """Get collected statistics."""
        return self._stats

    def report(self, event: ProgressEvent) -> None:
        """Report progress to CLI."""
        import sys

        from .config import PROGRESS_BAR_LENGTH
        from .utils import (
            _BOLD,
            _CYAN,
            _DIM,
            _GREEN,
            _RESET,
            _YELLOW,
            format_time,
        )

        if event.percent <= 0:
            return

        if event.fps > 0 and event.speed > 0:
            self._stats["fps_list"].append(event.fps)
            self._stats["speed_list"].append(event.speed)
            self._stats["frame_list"].append(event.frame)

        eta_str = f"{_YELLOW}--:--{_RESET}"
        if event.eta > 0:
            eta_str = f"{_YELLOW}{format_time(event.eta)}{_RESET}"
        elif event.percent >= 100:
            eta_str = f"{_GREEN}✓ Done{_RESET}"

        filled = int(PROGRESS_BAR_LENGTH * event.percent / 100)
        bar = "█" * filled + "░" * (PROGRESS_BAR_LENGTH - filled)

        current_str = format_time(event.current_time)
        total_str = format_time(self.total_duration)

        bar_color = _GREEN if event.percent >= 100 else _CYAN

        output = (
            f"\r  {bar_color}[{bar}]{_RESET} {_BOLD}{event.percent:5.1f}%{_RESET}"
            f"  {_DIM}│{_RESET} {current_str}{_DIM}/{_RESET}{total_str}"
            f"  {_DIM}│{_RESET} ETA {eta_str}"
            f"  {_DIM}│{_RESET} {_DIM}{event.fps:>4.0f}{_RESET} fps"
            f" {_DIM}·{_RESET} {_DIM}{event.speed:.1f}x{_RESET}"
            f" {_DIM}·{_RESET} {_DIM}F{_RESET}{event.frame}"
        )
        sys.stdout.write(output)
        sys.stdout.flush()

    def report_complete(self) -> None:
        """Report completion to CLI."""
        import sys

        from .config import PROGRESS_BAR_LENGTH
        from .utils import _BOLD, _DIM, _GREEN, _RESET, format_time

        bar = "█" * PROGRESS_BAR_LENGTH
        total_str = format_time(self.total_duration)

        output = (
            f"\r  {_GREEN}[{bar}]{_RESET} {_BOLD}100.0%{_RESET}"
            f"  {_DIM}│{_RESET} {total_str}{_DIM}/{_RESET}{total_str}"
            f"  {_DIM}│{_RESET} ETA {_GREEN}✓ Done{_RESET}"
            f"  {_DIM}│{_RESET} {_DIM}  --{_RESET} fps"
            f" {_DIM}·{_RESET} {_DIM}--x{_RESET}"
            f" {_DIM}·{_RESET} {_DIM}F{_RESET}--"
        )
        sys.stdout.write(output)
        sys.stdout.flush()

    def report_error(self, message: str) -> None:
        """Report error to CLI."""
        print(f"\n  Error: {message}")
