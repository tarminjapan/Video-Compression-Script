"""
Main GUI application for AmeCompression using CustomTkinter.

Provides the top-level window layout with a header bar, sidebar navigation,
switchable content area, and status bar.
"""

import shutil

import customtkinter as ctk

from .. import __version__
from ..ffmpeg import get_ffmpeg_executables
from .i18n import TranslationManager, t
from .theme import get_theme_options, load_theme_preference, save_theme_preference
from .views.audio_view import AudioView
from .views.settings_view import SettingsView
from .views.video_view import VideoView

_SIDEBAR_WIDTH = 200


class App(ctk.CTk):
    """Main application window for AmeCompression GUI."""

    WINDOW_WIDTH = 1024
    WINDOW_HEIGHT = 768
    MIN_WIDTH = 800
    MIN_HEIGHT = 600

    def __init__(self):
        super().__init__()

        self._current_theme = load_theme_preference()

        self.title(t("app.title"))
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        ctk.set_default_color_theme("blue")

        self._current_view_name: str | None = None
        self._current_view: ctk.CTkFrame | None = None
        self._views: dict[str, ctk.CTkFrame] = {}

        self._create_layout()
        self._create_header()
        self._create_sidebar()
        self._create_status_bar()
        self._switch_view("video")

    def _create_layout(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _create_header(self):
        header = ctk.CTkFrame(self, corner_radius=0, height=48)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        self._title_label = ctk.CTkLabel(
            header,
            text=t("app.title"),
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self._title_label.grid(row=0, column=0, padx=(16, 8), pady=10, sticky="w")

        self._language_btn = ctk.CTkButton(
            header,
            text=self._language_label(),
            width=80,
            command=self._toggle_language,
        )
        self._language_btn.grid(row=0, column=2, padx=(4, 8), pady=10)

        self._theme_btn = ctk.CTkButton(
            header,
            text=self._theme_label(),
            width=80,
            command=self._toggle_theme,
        )
        self._theme_btn.grid(row=0, column=3, padx=(4, 16), pady=10)

    def _create_sidebar(self):
        sidebar = ctk.CTkFrame(self, corner_radius=0, width=_SIDEBAR_WIDTH)
        sidebar.grid(row=1, column=0, sticky="ns")
        sidebar.grid_rowconfigure(3, weight=1)
        sidebar.grid_propagate(False)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("video", "nav.video"),
            ("audio", "nav.audio"),
            ("settings", "nav.settings"),
        ]
        for idx, (key, translation_key) in enumerate(nav_items):
            btn = ctk.CTkButton(
                sidebar,
                text=t(translation_key),
                fg_color="transparent",
                anchor="w",
                command=lambda k=key: self._switch_view(k),
            )
            btn.grid(row=idx, column=0, padx=8, pady=(8, 0), sticky="ew")
            self._nav_buttons[key] = btn

    def _create_status_bar(self):
        status_frame = ctk.CTkFrame(self, corner_radius=0, height=28)
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        status_frame.grid_propagate(False)

        ffmpeg_status = self._detect_ffmpeg()
        self._ffmpeg_label = ctk.CTkLabel(
            status_frame,
            text=ffmpeg_status,
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._ffmpeg_label.grid(row=0, column=0, padx=10, pady=4, sticky="w")

        self._version_label = ctk.CTkLabel(
            status_frame,
            text=t("app.version", version=__version__),
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._version_label.grid(row=0, column=1, padx=10, pady=4, sticky="e")
        status_frame.grid_columnconfigure(0, weight=1)

    def _switch_view(self, view_name: str):
        for name, btn in self._nav_buttons.items():
            if name == view_name:
                btn.configure(fg_color=("gray75", "gray30"))
            else:
                btn.configure(fg_color="transparent")

        if self._current_view is not None:
            self._current_view.grid_forget()

        if view_name not in self._views:
            view_classes = {
                "video": VideoView,
                "audio": AudioView,
                "settings": SettingsView,
            }
            cls = view_classes.get(view_name)
            if cls is None:
                return
            self._views[view_name] = cls(self, corner_radius=0)

        self._views[view_name].grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        self._current_view = self._views[view_name]
        self._current_view_name = view_name

    def _toggle_language(self):
        mgr = TranslationManager.get_instance()
        current = mgr.get_language()
        new_lang = "ja" if current == "en" else "en"
        mgr.set_language(new_lang)
        self._refresh_ui_texts()

    def _toggle_theme(self):
        options = get_theme_options()
        current_idx = options.index(self._current_theme) if self._current_theme in options else 0
        next_idx = (current_idx + 1) % len(options)
        self._current_theme = options[next_idx]
        save_theme_preference(self._current_theme)
        self._theme_btn.configure(text=self._theme_label())

    def _language_label(self) -> str:
        lang = TranslationManager.get_instance().get_language()
        return "日本語" if lang == "ja" else "EN"

    def _theme_label(self) -> str:
        return t(f"settings.themes.{self._current_theme}")

    def _detect_ffmpeg(self) -> str:
        try:
            ffmpeg_path, _ = get_ffmpeg_executables()
            if ffmpeg_path and shutil.which(ffmpeg_path):
                return t("status.ffmpeg_detected")
        except Exception:
            pass
        return t("status.ffmpeg_not_found")

    def _refresh_ui_texts(self):
        self.title(t("app.title"))
        self._title_label.configure(text=t("app.title"))
        self._language_btn.configure(text=self._language_label())
        self._theme_btn.configure(text=self._theme_label())
        self._ffmpeg_label.configure(text=self._detect_ffmpeg())
        self._version_label.configure(text=t("app.version", version=__version__))

        nav_items = [
            ("video", "nav.video"),
            ("audio", "nav.audio"),
            ("settings", "nav.settings"),
        ]
        for key, translation_key in nav_items:
            if key in self._nav_buttons:
                self._nav_buttons[key].configure(text=t(translation_key))


def run_gui():
    """Launch the AmeCompression GUI application."""
    app = App()
    app.mainloop()
