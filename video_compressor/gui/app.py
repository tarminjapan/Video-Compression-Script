"""
Main GUI application for AmeCompression using CustomTkinter.

Provides the top-level window layout with a header bar, sidebar navigation,
switchable content area, and status bar.
"""

import shutil

import customtkinter as ctk

from .. import __version__
from ..ffmpeg import get_ffmpeg_executables
from .i18n import t
from .theme import load_theme_preference
from .theme.fonts import DEFAULT_FONT_FAMILY
from .views.settings_view import SettingsView
from .views.video_audio_view import VideoAudioView

_SIDEBAR_WIDTH = 200

_STATUS_TEXT_COLOR = ("gray30", "gray60")


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
        self._ffmpeg_detected: bool | None = None

        self._create_layout()
        self._create_header()
        self._create_sidebar()
        self._create_status_bar()
        self._switch_view("video_audio")

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
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=18, weight="bold"),
        )
        self._title_label.grid(row=0, column=0, padx=(16, 8), pady=10, sticky="w")

    def _create_sidebar(self):
        sidebar = ctk.CTkFrame(self, corner_radius=0, width=_SIDEBAR_WIDTH)
        sidebar.grid(row=1, column=0, sticky="ns")
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_propagate(False)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("video_audio", "nav.video_audio"),
            ("settings", "nav.settings"),
        ]
        for idx, (key, translation_key) in enumerate(nav_items):
            btn = ctk.CTkButton(
                sidebar,
                text=t(translation_key),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                anchor="w",
                font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=14),
                hover_color=("gray75", "gray30"),
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
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            text_color=_STATUS_TEXT_COLOR,
        )
        self._ffmpeg_label.grid(row=0, column=0, padx=10, pady=4, sticky="w")

        self._version_label = ctk.CTkLabel(
            status_frame,
            text=t("app.version", version=__version__),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            text_color=_STATUS_TEXT_COLOR,
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
            if view_name == "video_audio":
                self._views[view_name] = VideoAudioView(self, corner_radius=0)
            elif view_name == "settings":
                self._views[view_name] = SettingsView(
                    self,
                    corner_radius=0,
                    on_language_change=self._refresh_ui_texts,
                )
            else:
                return

        self._views[view_name].grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        self._current_view = self._views[view_name]
        self._current_view_name = view_name

    def _detect_ffmpeg(self) -> str:
        if self._ffmpeg_detected is None:
            try:
                ffmpeg_path, _ = get_ffmpeg_executables()
                self._ffmpeg_detected = bool(ffmpeg_path and shutil.which(ffmpeg_path))
            except Exception:
                self._ffmpeg_detected = False
        if self._ffmpeg_detected:
            return t("status.ffmpeg_detected")
        return t("status.ffmpeg_not_found")

    def _refresh_ui_texts(self):
        self.title(t("app.title"))
        self._title_label.configure(text=t("app.title"))
        self._ffmpeg_label.configure(text=self._detect_ffmpeg())
        self._version_label.configure(text=t("app.version", version=__version__))

        nav_items = [
            ("video_audio", "nav.video_audio"),
            ("settings", "nav.settings"),
        ]
        for key, translation_key in nav_items:
            if key in self._nav_buttons:
                self._nav_buttons[key].configure(text=t(translation_key))

        for view in self._views.values():
            refresh = getattr(view, "refresh_texts", None)
            if callable(refresh):
                refresh()


def run_gui():
    """Launch the AmeCompression GUI application."""
    app = App()
    app.mainloop()
