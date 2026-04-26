import json
import os
import sys
from pathlib import Path
from typing import Any


def get_config_dir() -> Path:
    """Get the platform-specific configuration directory."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
    elif sys.platform == "darwin":
        base = str(Path("~/Library/Application Support").expanduser())
    else:  # Linux/Other
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path("~/.config").expanduser())

    if not base:
        base = str(Path("~").expanduser())

    path = Path(base) / "AmeCompression"
    path.mkdir(parents=True, exist_ok=True)
    return path


class SettingsManager:
    """Manages application settings and persistence."""

    _instance: "SettingsManager | None" = None

    def __init__(self) -> None:
        """Initialize SettingsManager."""
        self.config_dir = get_config_dir()
        self.settings_file = self.config_dir / "settings.json"
        self.settings = self._load_settings()

    @classmethod
    def get_instance(cls) -> "SettingsManager":
        """Get the singleton instance of SettingsManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance."""
        cls._instance = None

    def _load_settings(self) -> dict[str, Any]:
        """Load settings from the JSON file."""
        if self.settings_file.exists():
            try:
                with self.settings_file.open(encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
        return {}

    def _save_settings(self) -> None:
        """Save settings to the JSON file."""
        try:
            with self.settings_file.open("w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self.settings[key] = value
        self._save_settings()

    def update_all(self, data: dict[str, Any]) -> None:
        """Update multiple settings at once."""
        self.settings.update(data)
        self._save_settings()
