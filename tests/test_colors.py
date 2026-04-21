from video_compressor.gui.theme.colors import (
    BG_DROP_BORDER,
    BG_DROP_ZONE,
    BG_METER,
    BG_NAV_ACTIVE,
    BG_NAV_INACTIVE,
    BTN_NAV_HOVER,
    BTN_SECONDARY_FG,
    BTN_SECONDARY_HOVER,
    COLOR_ERROR,
    COLOR_PROGRESS,
    COLOR_SUCCESS,
    COLOR_WARNING,
    DIVIDER_COLOR,
    METER_HIGH,
    METER_LOW,
    METER_MED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_STATUS,
    TEXT_TERTIARY,
)


class TestColorTuples:
    def _assert_tuple(self, value):
        if isinstance(value, tuple):
            assert len(value) == 2, f"Expected 2-element tuple, got {value}"

    def test_text_colors_are_tuples(self):
        for color in [TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_STATUS]:
            self._assert_tuple(color)

    def test_bg_colors_are_tuples(self):
        for color in [BG_NAV_ACTIVE, BG_DROP_ZONE, BG_DROP_BORDER, BG_METER]:
            self._assert_tuple(color)

    def test_button_colors_are_tuples(self):
        for color in [BTN_SECONDARY_FG, BTN_SECONDARY_HOVER, BTN_NAV_HOVER]:
            self._assert_tuple(color)

    def test_status_colors_are_tuples(self):
        for color in [COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_PROGRESS]:
            self._assert_tuple(color)

    def test_meter_colors_are_tuples(self):
        for color in [METER_HIGH, METER_MED, METER_LOW]:
            self._assert_tuple(color)

    def test_divider_color_is_tuple(self):
        self._assert_tuple(DIVIDER_COLOR)

    def test_nav_inactive_is_transparent(self):
        assert BG_NAV_INACTIVE == "transparent"

    def test_all_colors_are_light_dark_pairs(self):
        all_colors = [
            TEXT_PRIMARY,
            TEXT_SECONDARY,
            TEXT_TERTIARY,
            TEXT_STATUS,
            BG_NAV_ACTIVE,
            BG_DROP_ZONE,
            BG_DROP_BORDER,
            BG_METER,
            BTN_SECONDARY_FG,
            BTN_SECONDARY_HOVER,
            BTN_NAV_HOVER,
            COLOR_SUCCESS,
            COLOR_ERROR,
            COLOR_WARNING,
            COLOR_PROGRESS,
            METER_HIGH,
            METER_MED,
            METER_LOW,
            DIVIDER_COLOR,
        ]
        for color in all_colors:
            assert isinstance(color, tuple), f"{color} is not a tuple"
            assert len(color) == 2, f"{color} does not have exactly 2 elements"
