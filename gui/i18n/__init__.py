"""
Internationalization (i18n) module for AmeCompression GUI.

Provides translation loading, language switching, and the t() helper function.

Usage:
    from gui.i18n import t, TranslationManager

    # Get a translated string
    title = t("app.title")

    # Switch language dynamically
    TranslationManager.get_instance().set_language("ja")
"""

from .translations import TranslationManager, t

__all__ = ["TranslationManager", "t"]
