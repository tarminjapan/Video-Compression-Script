import tempfile
from pathlib import Path
from unittest.mock import patch

from video_compressor.gui.utils import SettingsManager


class TestSettingsManager:
    def test_get_nonexistent(self, settings_manager):
        assert settings_manager.get("nonexistent") is None

    def test_get_with_default(self, settings_manager):
        assert settings_manager.get("nonexistent", "default") == "default"

    def test_set_and_get(self, settings_manager):
        settings_manager.set("test_key", "test_value")
        assert settings_manager.get("test_key") == "test_value"

    def test_set_overwrite(self, settings_manager):
        settings_manager.set("key", "value1")
        settings_manager.set("key", "value2")
        assert settings_manager.get("key") == "value2"

    def test_set_various_types(self, settings_manager):
        settings_manager.set("string", "hello")
        settings_manager.set("int", 42)
        settings_manager.set("float", 3.14)
        settings_manager.set("bool", True)
        settings_manager.set("list", [1, 2, 3])
        assert settings_manager.get("string") == "hello"
        assert settings_manager.get("int") == 42
        assert settings_manager.get("float") == 3.14
        assert settings_manager.get("bool") is True
        assert settings_manager.get("list") == [1, 2, 3]

    def test_singleton(self, settings_manager):
        mgr2 = SettingsManager.get_instance()
        assert mgr2 is settings_manager

    def test_reset_instance(self, settings_manager):
        SettingsManager.reset_instance()

        with (
            tempfile.TemporaryDirectory() as td,
            patch("video_compressor.gui.utils.get_config_dir", return_value=Path(td)),
        ):
            new_mgr = SettingsManager.get_instance()
            assert new_mgr is not settings_manager
