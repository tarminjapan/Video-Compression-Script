"""Utility functions for video compression."""

import re
from pathlib import Path

from . import __version__
from .config import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS

# ============================================
# ASCII Art Banner
# ============================================
# ANSI color codes
_CYAN = "\033[96m"
_BLUE = "\033[94m"
_MAGENTA = "\033[95m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"

_ASCII_BANNER = r"""
   __  __          __
  /\ \/\ \  __    /\ \
  \ \ \ \ \/\_\   \_\ \     __    ___
   \ \ \ \ \/\ \  /'_` \  /'__`\ / __`\
    \ \ \_/ \ \ \/\ \L\ \/\  __//\ \L\ \
     \ `\___/\ \_\ \___,_\ \____\ \____/
      `\/__/  \/_/\/__,_ /\/____/\/___/
  ____
 /\  _`\
 \ \ \/\_\    ___     ___ ___   _____   _ __    __    ____    ____    ___   _ __
  \ \ \/_/_  / __`\ /' __` __`\/\ '__`\/\`'__\/'__`\ /',__\  /',__\  / __`\/\`'__\
   \ \ \L\ \/\ \L\ \/\ \/\ \/\ \ \ \L\ \ \ \//\  __//\__, `\/\__, `\/\ \L\ \ \ \/
    \ \____/\ \____/\ \_\ \_\ \_\ \ ,__/\ \_\\ \____\/\____/\/\____/\ \____/\_\ \
     \/___/  \/___/  \/_/\/_/\/_/\ \ \/  \/_/ \/____/\/___/  \/___/  \/___/  \/_/
                                  \ \_\
                                   \/_/"""


def print_banner():
    """Print a styled ASCII art banner for Video Compressor."""
    line = "─" * 62
    print(f"{_DIM}{line}{_RESET}")
    print(f"{_CYAN}{_BOLD}{_ASCII_BANNER}{_RESET}")
    print()
    print(f"{_BLUE}{_BOLD}  ▸ Video Compressor v{__version__}{_RESET}")
    print(f"{_DIM}  ▸ Video / Audio Compression Tool{_RESET}")
    print(f"{_DIM}{line}{_RESET}")
    print()


def print_header(title, rows, color=_CYAN):
    """Print a styled section with a colored header line and indented rows.

    Args:
        title (str): Section title
        rows (list[tuple]): List of (label, value) pairs. Value can be a string
                           or a tuple (value, value_color) for colored values.
        color (str): ANSI color code for the header
    """
    print(f"\n  {color}{_BOLD}── {title} {'─' * (44 - len(title))}{_RESET}")
    for row in rows:
        label = row[0]
        value_data = row[1] if len(row) > 1 else ""
        if isinstance(value_data, tuple):
            value_str, val_color = value_data
            print(f"  {_DIM}{label}{_RESET}{val_color}{value_str}{_RESET}")
        else:
            print(f"  {_DIM}{label}{_RESET}{value_data}")


def format_time(seconds):
    """Format seconds to MM:SS.s format.

    Args:
        seconds (float): Time in seconds

    Returns:
        str: Formatted time string
    """
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"


def get_file_type(file_path):
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


def parse_bitrate(bitrate_str):
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


def calculate_scaled_resolution(width, height, max_width=None, max_height=None):
    """Calculate scaled resolution while maintaining aspect ratio.

    Args:
        width (int): Original width
        height (int): Original height
        max_width (int): Maximum allowed width (default: MAX_WIDTH)
        max_height (int): Maximum allowed height (default: MAX_HEIGHT)

    Returns:
        tuple: (scaled_width, scaled_height) or None if scaling not needed
    """
    from .config import MAX_HEIGHT, MAX_WIDTH

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


def parse_input_paths(raw_inputs):
    """Parse raw input string(s) into a list of individual file paths.

    Supports the following delimiters:
    - Newline (\\n)
    - Comma (,)
    - Whitespace (spaces, tabs)

    Handles double-quoted paths containing spaces.

    Args:
        raw_inputs (str or list[str]): Raw input string(s) containing one or more file paths

    Returns:
        list[str]: List of individual file paths
    """
    if not raw_inputs:
        return []

    # If a single string is provided, put it in a list
    if isinstance(raw_inputs, str):
        raw_inputs = [raw_inputs]

    # Join all inputs with a space, normalizing newlines and commas to spaces
    combined = "\n".join(raw_inputs)

    # Replace commas with newlines for uniform parsing
    combined = combined.replace(",", "\n")

    # Parse using regex: extract double-quoted strings OR non-whitespace sequences
    paths = []
    for match in re.finditer(r'"([^"]*)"|\S+', combined):
        # If quoted, use group(1) (content inside quotes); otherwise group(0) (full match)
        path = match.group(1) if match.group(1) is not None else match.group(0)
        path = path.strip()
        if path:
            paths.append(path)

    return paths
