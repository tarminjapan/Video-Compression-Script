from video_compressor import __version__
from video_compressor.config import (
    AUDIO_CODEC,
    AUDIO_EXTENSIONS,
    CRF_MAX,
    CRF_MIN,
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_AUDIO_ENABLED,
    DEFAULT_CRF,
    DEFAULT_DENOISE,
    DEFAULT_DENOISE_LEVEL,
    DEFAULT_FPS,
    DEFAULT_MP3_BITRATE,
    DEFAULT_VOLUME_GAIN,
    DENOISE_MAX,
    DENOISE_MIN,
    MAX_AUDIO_BITRATE,
    MAX_FPS,
    MAX_HEIGHT,
    MAX_VOLUME_LEVEL,
    MAX_WIDTH,
    MP3_BITRATE_MAX,
    MP3_BITRATE_MIN,
    MP3_CODEC,
    PROGRESS_BAR_LENGTH,
    TARGET_VOLUME_LEVEL,
    VIDEO_CODEC,
    VIDEO_EXTENSIONS,
    VIDEO_PRESET,
)


class TestVersion:
    def test_version_is_string(self):
        assert isinstance(__version__, str)

    def test_version_format(self):
        parts = __version__.split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()


class TestResolution:
    def test_max_resolution(self):
        assert MAX_WIDTH == 3840
        assert MAX_HEIGHT == 2160


class TestVideoCodec:
    def test_video_codec(self):
        assert VIDEO_CODEC == "libsvtav1"

    def test_crf_range(self):
        assert CRF_MIN == 0
        assert CRF_MAX == 63
        assert CRF_MIN <= DEFAULT_CRF <= CRF_MAX

    def test_preset_range(self):
        assert 0 <= VIDEO_PRESET <= 13

    def test_default_fps(self):
        assert DEFAULT_FPS is None

    def test_max_fps(self):
        assert MAX_FPS == 120


class TestAudioCodec:
    def test_audio_codec(self):
        assert AUDIO_CODEC == "aac"

    def test_default_audio_bitrate(self):
        assert DEFAULT_AUDIO_BITRATE == "192k"

    def test_max_audio_bitrate(self):
        assert MAX_AUDIO_BITRATE == 320

    def test_default_audio_enabled(self):
        assert DEFAULT_AUDIO_ENABLED is True


class TestMP3Codec:
    def test_mp3_codec(self):
        assert MP3_CODEC == "libmp3lame"

    def test_default_mp3_bitrate(self):
        assert DEFAULT_MP3_BITRATE == "192k"

    def test_mp3_bitrate_range(self):
        assert MP3_BITRATE_MIN == 32
        assert MP3_BITRATE_MAX == 320
        assert MP3_BITRATE_MIN < MP3_BITRATE_MAX


class TestVolume:
    def test_default_volume_gain(self):
        assert DEFAULT_VOLUME_GAIN is None

    def test_target_volume_level(self):
        assert TARGET_VOLUME_LEVEL == -16

    def test_max_volume_level(self):
        assert MAX_VOLUME_LEVEL == -1


class TestDenoise:
    def test_default_denoise(self):
        assert DEFAULT_DENOISE is None

    def test_denoise_range(self):
        assert DENOISE_MIN == 0.0
        assert DENOISE_MAX == 1.0
        assert DENOISE_MIN <= DEFAULT_DENOISE_LEVEL <= DENOISE_MAX


class TestFileExtensions:
    def test_video_extensions(self):
        assert ".mp4" in VIDEO_EXTENSIONS
        assert ".mkv" in VIDEO_EXTENSIONS
        assert ".avi" in VIDEO_EXTENSIONS
        assert ".mov" in VIDEO_EXTENSIONS
        assert ".webm" in VIDEO_EXTENSIONS

    def test_audio_extensions(self):
        assert ".mp3" in AUDIO_EXTENSIONS
        assert ".wav" in AUDIO_EXTENSIONS
        assert ".flac" in AUDIO_EXTENSIONS
        assert ".aac" in AUDIO_EXTENSIONS

    def test_no_overlap(self):
        assert VIDEO_EXTENSIONS.isdisjoint(AUDIO_EXTENSIONS)

    def test_progress_bar_length(self):
        assert PROGRESS_BAR_LENGTH > 0
