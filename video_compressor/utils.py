"""Utility functions for video compression."""

from pathlib import Path

from .config import AUDIO_EXTENSIONS, MAX_HEIGHT, MAX_WIDTH, VIDEO_EXTENSIONS


def format_time(seconds: float) -> str:
    """Format seconds to MM:SS.s format.

    Args:
        seconds (float): Time in seconds

    Returns:
        str: Formatted time string
    """
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"


def get_file_type(file_path: str | Path) -> str:
    """Determine file type based on extension.

    Args:
        file_path (str or Path): Path to file

    Returns:
        str: "video", "audio", or "unknown"
    """
    ext = Path(file_path).suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    elif ext in AUDIO_EXTENSIONS:
        return "audio"
    return "unknown"


def parse_bitrate(bitrate_str: str) -> int:
    """Parse bitrate string to kbps integer.

    Args:
        bitrate_str (str): Bitrate string (e.g., "192k", "320k")

    Returns:
        int: Bitrate in kbps
    """
    bitrate_str = bitrate_str.lower().strip()
    if bitrate_str.endswith("k"):
        return int(bitrate_str[:-1])
    elif bitrate_str.endswith("m"):
        return int(float(bitrate_str[:-1]) * 1000)
    else:
        return int(bitrate_str)


def calculate_scaled_resolution(
    width: int, height: int, max_width: int | None = None, max_height: int | None = None
) -> tuple[int, int] | None:
    """Calculate scaled resolution while maintaining aspect ratio.

    Args:
        width (int): Original width
        height (int): Original height
        max_width (int): Maximum allowed width (default: MAX_WIDTH)
        max_height (int): Maximum allowed height (default: MAX_HEIGHT)

    Returns:
        tuple: (scaled_width, scaled_height) or None if scaling not needed
    """
    # Set default values
    if max_width is None:
        max_width = MAX_WIDTH
    if max_height is None:
        max_height = MAX_HEIGHT

    # Check if scaling is needed
    if width <= max_width and height <= max_height:
        return None

    # Calculate scaling ratios
    width_ratio = max_width / width
    height_ratio = max_height / height

    # Use smaller ratio to fit within both constraints
    scale_ratio = min(width_ratio, height_ratio)

    # Calculate new dimensions (make even for better encoding quality)
    scaled_width = max(2, int(width * scale_ratio) // 2 * 2)
    scaled_height = max(2, int(height * scale_ratio) // 2 * 2)

    return (scaled_width, scaled_height)
