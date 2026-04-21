import math

from video_compressor.volume import (
    build_audio_filter,
    calculate_recommended_gain,
    parse_volume_gain,
    validate_denoise_level,
)


class TestCalculateRecommendedGain:
    def test_normal_case(self):
        gain = calculate_recommended_gain(-27.5, -5.2)
        assert isinstance(gain, float)
        assert gain <= 0 - (-5.2)

    def test_target_reached(self):
        gain = calculate_recommended_gain(-16.0, -3.0)
        assert gain == min(0.0, 2.0)
        assert gain == 0.0

    def test_loud_audio(self):
        gain = calculate_recommended_gain(-10.0, -1.0)
        assert gain == min(-16.0 - (-10.0), -1.0 - (-1.0))

    def test_quiet_audio(self):
        gain = calculate_recommended_gain(-40.0, -20.0)
        assert gain == round(min(24.0, 19.0), 1)

    def test_rounded_to_one_decimal(self):
        gain = calculate_recommended_gain(-27.5, -5.2)
        assert gain == round(gain, 1)

    def test_zero_mean(self):
        gain = calculate_recommended_gain(0.0, 0.0)
        assert gain == min(-16.0, -1.0)


class TestParseVolumeGain:
    def test_none(self):
        gain_db, is_auto = parse_volume_gain(None)
        assert gain_db is None
        assert is_auto is False

    def test_auto(self):
        gain_db, is_auto = parse_volume_gain("auto")
        assert gain_db is None
        assert is_auto is True

    def test_auto_uppercase(self):
        gain_db, is_auto = parse_volume_gain("AUTO")
        assert gain_db is None
        assert is_auto is True

    def test_db_suffix(self):
        gain_db, is_auto = parse_volume_gain("10dB")
        assert gain_db == 10.0
        assert is_auto is False

    def test_db_negative(self):
        gain_db, is_auto = parse_volume_gain("-5dB")
        assert gain_db == -5.0
        assert is_auto is False

    def test_db_case_insensitive(self):
        gain_db, is_auto = parse_volume_gain("10DB")
        assert gain_db == 10.0
        assert is_auto is False

    def test_multiplier(self):
        gain_db, is_auto = parse_volume_gain("2.0")
        expected = round(20 * math.log10(2.0), 1)
        assert gain_db == expected
        assert is_auto is False

    def test_multiplier_one(self):
        gain_db, is_auto = parse_volume_gain("1.0")
        assert gain_db == 0.0
        assert is_auto is False

    def test_whitespace(self):
        gain_db, is_auto = parse_volume_gain("  auto  ")
        assert gain_db is None
        assert is_auto is True


class TestBuildAudioFilter:
    def test_no_filters(self):
        assert build_audio_filter() is None

    def test_no_filters_none(self):
        assert build_audio_filter(volume_gain_db=None, denoise_level=None) is None

    def test_volume_only(self):
        result = build_audio_filter(volume_gain_db=5.0)
        assert result == "volume=5.0dB"

    def test_denoise_only(self):
        result = build_audio_filter(denoise_level=0.5)
        assert result is not None
        assert "afftdn=nr=" in result
        assert "volume" not in result

    def test_both_filters(self):
        result = build_audio_filter(volume_gain_db=5.0, denoise_level=0.3)
        assert result is not None
        assert "afftdn=nr=" in result
        assert "volume=5.0dB" in result
        assert result.index("afftdn") < result.index("volume")

    def test_denoise_zero(self):
        assert build_audio_filter(denoise_level=0.0) is None

    def test_denoise_max(self):
        result = build_audio_filter(denoise_level=1.0)
        assert result is not None
        assert "afftdn=nr=97" in result


class TestValidateDenoiseLevel:
    def test_none(self):
        assert validate_denoise_level(None) is None

    def test_valid_range(self):
        assert validate_denoise_level(0.5) == 0.5

    def test_minimum(self):
        assert validate_denoise_level(0.0) == 0.0

    def test_maximum(self):
        assert validate_denoise_level(1.0) == 1.0

    def test_too_low(self):
        assert validate_denoise_level(-0.5) == 0.0

    def test_too_high(self):
        assert validate_denoise_level(1.5) == 1.0
