"""
Translation loader and manager for AmeCompression GUI i18n.

Provides the TranslationManager singleton class for loading, switching,
and persisting language preferences, and the t() helper function for
retrieving translated strings.

Usage:
    from gui.i18n import t, TranslationManager

    title = t("app.title")

    mgr = TranslationManager.get_instance()
    mgr.set_language("ja")
    title_ja = t("app.title")
"""

import json
import os
import sys
from pathlib import Path

_DEFAULT_LANGUAGE = "en"
_SUPPORTED_LANGUAGES = ("en", "ja")
_SETTINGS_FILENAME = "settings.json"


def _get_config_dir():
    """Return the platform-specific configuration directory.

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


def _get_translations_dir():
    """Return the directory containing translation JSON files.

    Returns:
        Path: Directory where en.json and ja.json are located.
    """
    return Path(__file__).parent


class TranslationManager:
    """Singleton manager for loading and switching UI translations.

    Loads translation data from JSON files (en.json, ja.json) located in
    the gui/i18n/ directory. Persists the selected language to a
    platform-specific settings file so that the preference survives
    application restarts.

    Supports dot-notation keys to reference nested values, e.g.
    ``t("app.title")`` looks up ``translations["app"]["title"]``.
    """

    _instance = None

    def __init__(self):
        self._translations = {}
        self._current_lang = _DEFAULT_LANGUAGE
        self._translations_dir = _get_translations_dir()
        self._config_dir = _get_config_dir()
        self._load_all_translations()
        self._load_language_preference()

    @classmethod
    def get_instance(cls):
        """Return the singleton TranslationManager instance.

        Creates the instance on first access.

        Returns:
            TranslationManager: The shared manager instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance.

        Primarily useful for testing.
        """
        cls._instance = None

    def _load_all_translations(self):
        """Load translation data for all supported languages from disk."""
        for lang in _SUPPORTED_LANGUAGES:
            filepath = self._translations_dir / f"{lang}.json"
            if filepath.is_file():
                try:
                    with open(filepath, encoding="utf-8") as f:
                        self._translations[lang] = json.load(f)
                except (json.JSONDecodeError, OSError):
                    self._translations[lang] = {}
            else:
                self._translations[lang] = {}

    def _load_language_preference(self):
        """Load saved language preference from the settings file.

        Checks the environment variable ``AME_LANGUAGE`` first (for
        debugging or temporary overrides), then falls back to the
        persisted settings file, and finally to the default language.
        """
        env_lang = os.environ.get("AME_LANGUAGE")
        if env_lang and env_lang in _SUPPORTED_LANGUAGES:
            self._current_lang = env_lang
            return

        settings_path = self._config_dir / _SETTINGS_FILENAME
        if settings_path.is_file():
            try:
                with open(settings_path, encoding="utf-8") as f:
                    settings = json.load(f)
                saved_lang = settings.get("language")
                if saved_lang and saved_lang in _SUPPORTED_LANGUAGES:
                    self._current_lang = saved_lang
                    return
            except (json.JSONDecodeError, OSError):
                pass

    def _save_language_preference(self):
        """Persist the current language selection to the settings file."""
        settings_path = self._config_dir / _SETTINGS_FILENAME
        settings = {}
        if settings_path.is_file():
            try:
                with open(settings_path, encoding="utf-8") as f:
                    settings = json.load(f)
            except (json.JSONDecodeError, OSError):
                settings = {}

        settings["language"] = self._current_lang
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def _resolve_key(self, data, key):
        """Resolve a dot-notation key against a nested dictionary.

        Args:
            data (dict): The translation dictionary for the current language.
            key (str): Dot-separated key, e.g. ``"app.title"``.

        Returns:
            str or None: The resolved translation string, or None if not found.
        """
        parts = key.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current if isinstance(current, str) else None

    def get_language(self):
        """Return the currently active language code.

        Returns:
            str: Language code such as ``"en"`` or ``"ja"``.
        """
        return self._current_lang

    def get_supported_languages(self):
        """Return a tuple of supported language codes.

        Returns:
            tuple: Supported language codes.
        """
        return _SUPPORTED_LANGUAGES

    def set_language(self, lang):
        """Switch the active language and persist the choice.

        Args:
            lang (str): Language code to switch to (e.g. ``"en"`` or ``"ja"``).

        Raises:
            ValueError: If the language code is not supported.
        """
        if lang not in _SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {lang}. Supported: {', '.join(_SUPPORTED_LANGUAGES)}"
            )
        self._current_lang = lang
        self._save_language_preference()

    def translate(self, key, **kwargs):
        """Return the translated string for the given key.

        Looks up the key in the current language's translation dictionary
        using dot-notation (e.g. ``"app.title"``). If the key is not found
        in the current language, falls back to the default language. If
        still not found, returns the key itself.

        Optional keyword arguments are used for string interpolation via
        ``str.format()``.

        Args:
            key (str): Dot-notation translation key.
            **kwargs: Format parameters for the translation string.

        Returns:
            str: The translated and formatted string.
        """
        text = self._resolve_key(self._translations.get(self._current_lang, {}), key)
        if text is None:
            text = self._resolve_key(self._translations.get(_DEFAULT_LANGUAGE, {}), key)
        if text is None:
            return key

        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text


def t(key, **kwargs):
    """Translate a key using the current language setting.

    This is the primary helper function for retrieving translated strings.
    It delegates to the singleton TranslationManager instance.

    Args:
        key (str): Dot-notation translation key (e.g. ``"app.title"``).
        **kwargs: Optional format parameters for interpolation.

    Returns:
        str: The translated and formatted string.
    """
    return TranslationManager.get_instance().translate(key, **kwargs)
