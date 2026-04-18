"""
Configuration settings and constants for video compression.
"""

# ============================================
# Resolution Settings (4K = 3840x2160)
# ============================================
MAX_WIDTH = 3840  # Maximum width
MAX_HEIGHT = 2160  # Maximum height

# ============================================
# Video Codec Settings
# ============================================
VIDEO_CODEC = "libsvtav1"  # Video codec (SVT-AV1)
DEFAULT_CRF = 25  # CRF value (0-63, lower = higher quality/larger, higher = lower quality/smaller)
VIDEO_PRESET = 6  # Encoding speed preset (0-13, higher = faster)
DEFAULT_FPS = None  # Default FPS (None = keep original)
MAX_FPS = 120  # Maximum FPS

# ============================================
# Audio Codec Settings (for video)
# ============================================
AUDIO_CODEC = "aac"  # Audio codec (AAC)
DEFAULT_AUDIO_BITRATE = "192k"  # Default audio bitrate
MAX_AUDIO_BITRATE = 320  # Maximum audio bitrate in kbps
DEFAULT_AUDIO_ENABLED = True  # Audio enabled by default

# ============================================
# MP3 Codec Settings (for audio-only files)
# ============================================
MP3_CODEC = "libmp3lame"  # MP3 encoder
DEFAULT_MP3_BITRATE = "192k"  # Default MP3 bitrate
MP3_BITRATE_MIN = 32  # Minimum MP3 bitrate in kbps
MP3_BITRATE_MAX = 320  # Maximum MP3 bitrate in kbps

# ============================================
# Volume Adjustment Settings
# ============================================
DEFAULT_VOLUME_GAIN = None  # Default: disabled (None, or value like "2.0", "10dB", "auto")
TARGET_VOLUME_LEVEL = -16  # Target loudness in dB (standard for speech/dialogue)
MAX_VOLUME_LEVEL = -1  # Maximum volume level to prevent clipping (dB)

# ============================================
# Denoise Settings
# ============================================
DEFAULT_DENOISE = None  # Default: disabled (None or 0.0-1.0)
DENOISE_MIN = 0.0  # Minimum denoise level
DENOISE_MAX = 1.0  # Maximum denoise level
DEFAULT_DENOISE_LEVEL = 0.15  # Default denoise level when --denoise is used without value

# ============================================
# Supported File Extensions
# ============================================
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".ts",
    ".mts",
    ".m2ts",
}
AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".m4a",
    ".ogg",
    ".wma",
    ".ape",
    ".alac",
}

# ============================================
# CRF Value Range
# ============================================
CRF_MIN = 0
CRF_MAX = 63

# ============================================
# Progress Bar Settings
# ============================================
PROGRESS_BAR_LENGTH = 30
