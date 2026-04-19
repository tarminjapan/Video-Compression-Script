"""
Font configuration for AmeCompression GUI.

Provides platform-specific default font families:
  - Windows / Linux: Noto Sans JP
  - macOS: Hiragino Sans
"""

import sys

if sys.platform == "darwin":
    DEFAULT_FONT_FAMILY = "Hiragino Sans"
else:
    DEFAULT_FONT_FAMILY = "Noto Sans JP"
