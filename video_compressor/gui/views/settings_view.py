"""
Settings view for AmeCompression GUI.

Provides language, theme, FFmpeg path, output folder, and default compression
settings with save/reset functionality.
"""

import platform
import shutil
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ..i18n import TranslationManager, t
from ..theme import get_theme_options, save_theme_preference
from ..theme.fonts import DEFAULT_FONT_FAMILY
from ..utils import SettingsManager

_FFMPEG_MODE_KEYS = ["auto", "manual"]
_AUDIO_BITRATE_OPTIONS = ["32k", "64k", "96k", "128k", "192k", "256k", "320k"]


class SettingsView(ctk.CTkFrame):
    """Full settings view with appearance, FFmpeg, output, and compression sections."""

    def __init__(
        self,
        master,
        on_language_change: Callable[[], None] | None = None,
        on_theme_change: Callable[[str], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._settings = SettingsManager.get_instance()
        self._on_language_change = on_language_change
        self._on_theme_change = on_theme_change

        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        row = 0

        self._title_label = ctk.CTkLabel(
            scroll,
            text=t("settings.title"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=18, weight="bold"),
        )
        self._title_label.grid(row=row, column=0, padx=16, pady=(16, 10), sticky="w")
        row += 1

        row = self._create_appearance_section(scroll, row)
        row = self._create_ffmpeg_section(scroll, row)
        row = self._create_output_section(scroll, row)
        row = self._create_compression_section(scroll, row)
        row = self._create_actions(scroll, row)

    def _section_header(self, parent, row, key):
        label = ctk.CTkLabel(
            parent,
            text=t(key),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=14, weight="bold"),
        )
        label.grid(row=row, column=0, padx=16, pady=(16, 6), sticky="w")

        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray80", "gray20"))
        sep.grid(row=row + 1, column=0, padx=16, sticky="ew")
        return row + 2

    def _create_appearance_section(self, parent, row):
        row = self._section_header(parent, row, "settings.section_appearance")

        lang_frame = ctk.CTkFrame(parent, fg_color="transparent")
        lang_frame.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
        lang_frame.grid_columnconfigure(1, weight=1)

        self._lang_label = ctk.CTkLabel(
            lang_frame,
            text=t("settings.language"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._lang_label.grid(row=0, column=0, sticky="w")

        mgr = TranslationManager.get_instance()
        current_lang = mgr.get_language()
        supported = mgr.get_supported_languages()
        self._lang_keys = list(supported)
        self._lang_labels = [t(f"settings.language_names.{k}") for k in supported]
        current_idx = self._lang_keys.index(current_lang) if current_lang in self._lang_keys else 0
        self._lang_var = ctk.StringVar(value=self._lang_labels[current_idx])
        self._lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            variable=self._lang_var,
            values=self._lang_labels,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            command=self._on_language_change_internal,
        )
        self._lang_menu.grid(row=0, column=1, sticky="w", padx=(8, 0))
        row += 1

        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
        theme_frame.grid_columnconfigure(1, weight=1)

        self._theme_label = ctk.CTkLabel(
            theme_frame,
            text=t("settings.theme"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._theme_label.grid(row=0, column=0, sticky="w")

        current_theme = self._settings.get("theme", "dark") or "dark"
        theme_list = list(get_theme_options())
        self._theme_labels = [t(f"settings.themes.{k}") for k in theme_list]
        current_theme_idx = theme_list.index(current_theme) if current_theme in theme_list else 0
        self._theme_var = ctk.StringVar(value=self._theme_labels[current_theme_idx])
        self._theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            variable=self._theme_var,
            values=self._theme_labels,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            command=self._on_theme_change_internal,
        )
        self._theme_menu.grid(row=0, column=1, sticky="w", padx=(8, 0))
        row += 1

        return row

    def _create_ffmpeg_section(self, parent, row):
        row = self._section_header(parent, row, "settings.section_ffmpeg")

        mode_frame = ctk.CTkFrame(parent, fg_color="transparent")
        mode_frame.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
        mode_frame.grid_columnconfigure(1, weight=1)

        self._ffmpeg_mode_label = ctk.CTkLabel(
            mode_frame,
            text=t("settings.ffmpeg_mode"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._ffmpeg_mode_label.grid(row=0, column=0, sticky="w")

        self._ffmpeg_mode_labels = [
            t("settings.ffmpeg_auto"),
            t("settings.ffmpeg_manual"),
        ]
        current_mode = self._settings.get("ffmpeg_path_mode", "auto") or "auto"
        mode_idx = _FFMPEG_MODE_KEYS.index(current_mode) if current_mode in _FFMPEG_MODE_KEYS else 0
        self._ffmpeg_mode_var = ctk.StringVar(value=self._ffmpeg_mode_labels[mode_idx])
        self._ffmpeg_mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            variable=self._ffmpeg_mode_var,
            values=self._ffmpeg_mode_labels,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            command=self._on_ffmpeg_mode_change,
        )
        self._ffmpeg_mode_menu.grid(row=0, column=1, sticky="w", padx=(8, 0))
        row += 1

        self._ffmpeg_path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._ffmpeg_path_frame.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
        self._ffmpeg_path_frame.grid_columnconfigure(1, weight=1)

        self._ffmpeg_path_label = ctk.CTkLabel(
            self._ffmpeg_path_frame,
            text=t("settings.ffmpeg_path"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._ffmpeg_path_label.grid(row=0, column=0, sticky="w")

        saved_path = self._settings.get("ffmpeg_path", "") or ""
        self._ffmpeg_path_entry = ctk.CTkEntry(
            self._ffmpeg_path_frame,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            placeholder_text="ffmpeg",
        )
        self._ffmpeg_path_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        if saved_path:
            self._ffmpeg_path_entry.insert(0, saved_path)

        self._ffmpeg_browse_btn = ctk.CTkButton(
            self._ffmpeg_path_frame,
            text=t("settings.ffmpeg_browse"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            width=70,
            command=self._browse_ffmpeg_path,
        )
        self._ffmpeg_browse_btn.grid(row=0, column=2)
        row += 1

        self._ffmpeg_status_label = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            text_color=("gray40", "gray60"),
        )
        self._ffmpeg_status_label.grid(row=row, column=0, padx=16, pady=(0, 4), sticky="w")
        row += 1

        self._on_ffmpeg_mode_change(self._ffmpeg_mode_labels[mode_idx])

        return row

    def _create_output_section(self, parent, row):
        row = self._section_header(parent, row, "settings.section_output")

        output_frame = ctk.CTkFrame(parent, fg_color="transparent")
        output_frame.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
        output_frame.grid_columnconfigure(1, weight=1)

        self._output_label = ctk.CTkLabel(
            output_frame,
            text=t("settings.output_default"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._output_label.grid(row=0, column=0, sticky="w")

        saved_output = self._settings.get("default_output_folder", "") or ""
        self._output_entry = ctk.CTkEntry(
            output_frame,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            placeholder_text=t("settings.output_default"),
        )
        self._output_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        if saved_output:
            self._output_entry.insert(0, saved_output)

        self._output_browse_btn = ctk.CTkButton(
            output_frame,
            text=t("settings.output_browse"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            width=70,
            command=self._browse_output_folder,
        )
        self._output_browse_btn.grid(row=0, column=2)
        row += 1

        return row

    def _create_compression_section(self, parent, row):
        row = self._section_header(parent, row, "settings.section_compression")

        default_crf = self._settings.get("default_crf", 25)
        default_preset = self._settings.get("default_preset", 6)
        default_bitrate = self._settings.get("default_audio_bitrate", "192k") or "192k"

        crf_frame = ctk.CTkFrame(parent, fg_color="transparent")
        crf_frame.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
        crf_frame.grid_columnconfigure(1, weight=1)

        self._crf_label = ctk.CTkLabel(
            crf_frame,
            text=t("settings.default_crf"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._crf_label.grid(row=0, column=0, sticky="w")

        self._crf_value_label = ctk.CTkLabel(
            crf_frame,
            text=str(default_crf),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12, weight="bold"),
            width=30,
        )
        self._crf_value_label.grid(row=0, column=2, padx=(5, 0))

        self._crf_slider = ctk.CTkSlider(
            crf_frame,
            from_=0,
            to=63,
            number_of_steps=63,
            command=self._on_crf_change,
        )
        self._crf_slider.set(int(default_crf) if default_crf is not None else 25)
        self._crf_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))
        row += 1

        preset_frame = ctk.CTkFrame(parent, fg_color="transparent")
        preset_frame.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
        preset_frame.grid_columnconfigure(1, weight=1)

        self._preset_label = ctk.CTkLabel(
            preset_frame,
            text=t("settings.default_preset"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._preset_label.grid(row=0, column=0, sticky="w")

        self._preset_value_label = ctk.CTkLabel(
            preset_frame,
            text=str(default_preset),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12, weight="bold"),
            width=30,
        )
        self._preset_value_label.grid(row=0, column=2, padx=(5, 0))

        self._preset_slider = ctk.CTkSlider(
            preset_frame,
            from_=0,
            to=13,
            number_of_steps=13,
            command=self._on_preset_change,
        )
        self._preset_slider.set(int(default_preset) if default_preset is not None else 6)
        self._preset_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))
        row += 1

        bitrate_frame = ctk.CTkFrame(parent, fg_color="transparent")
        bitrate_frame.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
        bitrate_frame.grid_columnconfigure(1, weight=1)

        self._bitrate_label = ctk.CTkLabel(
            bitrate_frame,
            text=t("settings.default_audio_bitrate"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._bitrate_label.grid(row=0, column=0, sticky="w")

        self._bitrate_var = ctk.StringVar(
            value=default_bitrate if default_bitrate in _AUDIO_BITRATE_OPTIONS else "192k"
        )
        self._bitrate_combo = ctk.CTkComboBox(
            bitrate_frame,
            variable=self._bitrate_var,
            values=_AUDIO_BITRATE_OPTIONS,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._bitrate_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        row += 1

        return row

    def _create_actions(self, parent, row):
        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.grid(row=row, column=0, padx=16, pady=(20, 8), sticky="ew")
        action_frame.grid_columnconfigure(1, weight=1)

        self._save_btn = ctk.CTkButton(
            action_frame,
            text=t("settings.save"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=13, weight="bold"),
            width=140,
            height=36,
            command=self._save_settings,
        )
        self._save_btn.grid(row=0, column=0, sticky="w")

        self._reset_btn = ctk.CTkButton(
            action_frame,
            text=t("settings.reset"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=13),
            width=140,
            height=36,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            command=self._reset_settings,
        )
        self._reset_btn.grid(row=0, column=1, sticky="e")
        row += 1

        self._status_label = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            text_color=("green", "#90EE90"),
        )
        self._status_label.grid(row=row, column=0, padx=16, pady=(0, 16), sticky="w")
        row += 1

        return row

    def _on_language_change_internal(self, _selected):
        for i, key in enumerate(self._lang_keys):
            if i < len(self._lang_labels) and self._lang_var.get() == self._lang_labels[i]:
                TranslationManager.get_instance().set_language(key)
                if self._on_language_change:
                    self._on_language_change()
                break

    def _on_theme_change_internal(self, _selected):
        theme_list = list(get_theme_options())
        for i, key in enumerate(theme_list):
            if i < len(self._theme_labels) and self._theme_var.get() == self._theme_labels[i]:
                save_theme_preference(key)
                if self._on_theme_change:
                    self._on_theme_change(key)
                break

    def _on_ffmpeg_mode_change(self, _selected):
        is_manual = self._ffmpeg_mode_var.get() == self._ffmpeg_mode_labels[1]
        if is_manual:
            self._ffmpeg_path_entry.configure(state="normal")
            self._ffmpeg_browse_btn.configure(state="normal")
            self._update_ffmpeg_status()
        else:
            self._ffmpeg_path_entry.configure(state="disabled")
            self._ffmpeg_browse_btn.configure(state="disabled")
            self._ffmpeg_status_label.configure(text="")

    def _browse_ffmpeg_path(self):
        if platform.system() == "Windows":
            filetypes = [("Executable", "*.exe"), ("All files", "*.*")]
        else:
            filetypes = [("All files", "*.*")]
        result = filedialog.askopenfilename(filetypes=filetypes)
        if result:
            self._ffmpeg_path_entry.delete(0, "end")
            self._ffmpeg_path_entry.insert(0, result)
            self._update_ffmpeg_status()

    def _browse_output_folder(self):
        folder = filedialog.askdirectory(title=t("settings.folder_select"))
        if folder:
            self._output_entry.delete(0, "end")
            self._output_entry.insert(0, folder)

    def _on_crf_change(self, value):
        self._crf_value_label.configure(text=str(int(value)))

    def _on_preset_change(self, value):
        self._preset_value_label.configure(text=str(int(value)))

    def _update_ffmpeg_status(self):
        path = self._ffmpeg_path_entry.get().strip()
        if not path:
            self._ffmpeg_status_label.configure(text="")
            return
        if Path(path).exists() and shutil.which(path):
            self._ffmpeg_status_label.configure(
                text=t("settings.ffmpeg_status_found", path=path),
                text_color=("green", "#90EE90"),
            )
        else:
            self._ffmpeg_status_label.configure(
                text=t("settings.ffmpeg_status_not_found"),
                text_color=("red", "#FF6B6B"),
            )

    def _save_settings(self):
        ffmpeg_mode = self._get_ffmpeg_mode_key()
        self._settings.set("ffmpeg_path_mode", ffmpeg_mode)

        if ffmpeg_mode == "manual":
            self._settings.set("ffmpeg_path", self._ffmpeg_path_entry.get().strip())
        else:
            self._settings.set("ffmpeg_path", "")

        output_folder = self._output_entry.get().strip()
        self._settings.set("default_output_folder", output_folder)

        self._settings.set("default_crf", int(self._crf_slider.get()))
        self._settings.set("default_preset", int(self._preset_slider.get()))
        self._settings.set("default_audio_bitrate", self._bitrate_var.get())

        if ffmpeg_mode == "manual":
            self._update_ffmpeg_status()

        self._status_label.configure(text=t("settings.saved"), text_color=("green", "#90EE90"))

    def _reset_settings(self):
        self._settings.set("default_crf", 25)
        self._settings.set("default_preset", 6)
        self._settings.set("default_audio_bitrate", "192k")
        self._settings.set("default_output_folder", "")
        self._settings.set("ffmpeg_path", "")
        self._settings.set("ffmpeg_path_mode", "auto")

        self._crf_slider.set(25)
        self._crf_value_label.configure(text="25")
        self._preset_slider.set(6)
        self._preset_value_label.configure(text="6")
        self._bitrate_var.set("192k")
        self._output_entry.delete(0, "end")
        self._ffmpeg_path_entry.delete(0, "end")
        self._ffmpeg_path_entry.configure(state="disabled")
        self._ffmpeg_browse_btn.configure(state="disabled")
        self._ffmpeg_mode_var.set(self._ffmpeg_mode_labels[0])
        self._ffmpeg_status_label.configure(text="")

        self._status_label.configure(
            text=t("settings.reset_done"),
            text_color=("green", "#90EE90"),
        )

    def _get_ffmpeg_mode_key(self) -> str:
        for i, key in enumerate(_FFMPEG_MODE_KEYS):
            if (
                i < len(self._ffmpeg_mode_labels)
                and self._ffmpeg_mode_var.get() == self._ffmpeg_mode_labels[i]
            ):
                return key
        return "auto"

    def refresh_texts(self):
        mgr = TranslationManager.get_instance()
        supported = mgr.get_supported_languages()
        self._lang_keys = list(supported)
        self._lang_labels = [t(f"settings.language_names.{k}") for k in supported]
        current_lang = mgr.get_language()
        current_idx = self._lang_keys.index(current_lang) if current_lang in self._lang_keys else 0
        self._lang_var.set(self._lang_labels[current_idx])
        self._lang_menu.configure(values=self._lang_labels)
        self._lang_label.configure(text=t("settings.language"))
        self._title_label.configure(text=t("settings.title"))

        self._theme_labels = [t(f"settings.themes.{k}") for k in get_theme_options()]
        current_theme = self._settings.get("theme", "dark") or "dark"
        theme_list = list(get_theme_options())
        current_theme_idx = theme_list.index(current_theme) if current_theme in theme_list else 0
        self._theme_var.set(self._theme_labels[current_theme_idx])
        self._theme_menu.configure(values=self._theme_labels)
        self._theme_label.configure(text=t("settings.theme"))

        self._ffmpeg_mode_label.configure(text=t("settings.ffmpeg_mode"))
        self._ffmpeg_mode_labels = [t("settings.ffmpeg_auto"), t("settings.ffmpeg_manual")]
        mode_idx = _FFMPEG_MODE_KEYS.index(self._get_ffmpeg_mode_key())
        self._ffmpeg_mode_var.set(self._ffmpeg_mode_labels[mode_idx])
        self._ffmpeg_mode_menu.configure(values=self._ffmpeg_mode_labels)
        self._ffmpeg_path_label.configure(text=t("settings.ffmpeg_path"))
        self._ffmpeg_browse_btn.configure(text=t("settings.ffmpeg_browse"))

        self._output_label.configure(text=t("settings.output_default"))
        self._output_browse_btn.configure(text=t("settings.output_browse"))

        self._crf_label.configure(text=t("settings.default_crf"))
        self._preset_label.configure(text=t("settings.default_preset"))
        self._bitrate_label.configure(text=t("settings.default_audio_bitrate"))

        self._save_btn.configure(text=t("settings.save"))
        self._reset_btn.configure(text=t("settings.reset"))
