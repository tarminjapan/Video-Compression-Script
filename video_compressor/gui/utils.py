"""
Shared utility functions for the AmeCompression GUI.
"""

import json
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


_SETTINGS_FILENAME = "settings.json"


class SettingsManager:
    """Centralized manager for application settings persisted to a JSON file.

    Provides atomic read/write access to a shared ``settings.json`` so that
    independent components (theme, i18n, etc.) can manage their own keys
    without risk of overwriting each other's changes.
    """

    _instance = None

    def __init__(self):
        self._config_dir = get_config_dir()
        self._settings_path = self._config_dir / _SETTINGS_FILENAME
        self._cache: dict | None = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def _load(self) -> dict:
        if self._settings_path.is_file():
            try:
                with open(self._settings_path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save(self, settings: dict):
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            with open(self._settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self._cache = settings
        except OSError:
            pass

    def get(self, key: str, default=None):
        settings = self._load()
        return settings.get(key, default)

    def set(self, key: str, value):
        settings = self._load()
        settings[key] = value
        self._save(settings)

    def update_all(self, data: dict):
        """Update multiple settings at once in a single I/O operation.

        Args:
            data (dict): Dictionary of key-value pairs to update.
        """
        settings = self._load()
        settings.update(data)
        self._save(settings)
