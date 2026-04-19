"""
Shared utility functions for the AmeCompression GUI.
"""

import os
import sys
from pathlib import Path


def get_config_dir() -> Path:
    """Return the platform-specific configuration directory for AmeCompression.

    Returns:
        Path: Directory for storing application settings.
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "AmeCompression"
