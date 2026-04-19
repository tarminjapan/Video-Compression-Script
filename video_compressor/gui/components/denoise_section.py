"""
Noise reduction settings section for AmeCompression GUI.

Provides toggle, level slider, and preset buttons for configuring
audio noise reduction via FFmpeg's afftdn filter.
"""

import customtkinter as ctk

from ...config import DENOISE_MAX, DENOISE_MIN
from ..i18n import t
from ..theme.fonts import DEFAULT_FONT_FAMILY

_DENOISE_PRESETS = {
    "light": 0.15,
    "medium": 0.4,
    "strong": 0.75,
}

_PRESET_KEYS = ["light", "medium", "strong"]


class DenoiseSection(ctk.CTkFrame):
    """Noise reduction settings section with toggle, slider, and presets."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        row = 0

        ctk.CTkLabel(
            self,
            text=t("denoise.title"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=14, weight="bold"),
        ).grid(row=row, column=0, padx=10, pady=(10, 5), sticky="w")
        row += 1

        self._enable_var = ctk.BooleanVar(value=False)
        self._enable_check = ctk.CTkCheckBox(
            self,
            text=t("denoise.enable"),
            variable=self._enable_var,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            command=self._on_toggle,
        )
        self._enable_check.grid(row=row, column=0, padx=10, pady=2, sticky="w")
        row += 1

        self._level_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._level_frame.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
        self._level_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._level_frame,
            text=t("denoise.level"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._level_value_label = ctk.CTkLabel(
            self._level_frame,
            text="0.15",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12, weight="bold"),
            width=40,
        )
        self._level_value_label.grid(row=0, column=2, padx=(5, 0))

        self._level_slider = ctk.CTkSlider(
            self._level_frame,
            from_=DENOISE_MIN,
            to=DENOISE_MAX,
            number_of_steps=100,
            command=self._on_level_change,
        )
        self._level_slider.set(0.15)
        self._level_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))

        ctk.CTkLabel(
            self._level_frame,
            text=t("denoise.level_description"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=10),
            text_color=("gray50", "gray60"),
            wraplength=500,
            justify="left",
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(2, 0))
        row += 1

        self._preset_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._preset_frame.grid(row=row, column=0, padx=10, pady=5, sticky="w")

        self._preset_buttons: list[ctk.CTkButton] = []
        for key in _PRESET_KEYS:
            btn = ctk.CTkButton(
                self._preset_frame,
                text=t(f"denoise.presets.{key}"),
                font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
                width=70,
                height=28,
                command=lambda k=key: self._apply_preset(k),
            )
            btn.pack(side="left", padx=(0, 6))
            self._preset_buttons.append(btn)
        row += 1

        self._on_toggle()

    def _on_toggle(self):
        enabled = self._enable_var.get()
        state = "normal" if enabled else "disabled"
        self._level_slider.configure(state=state)
        for btn in self._preset_buttons:
            btn.configure(state=state)

    def _on_level_change(self, value):
        self._level_value_label.configure(text=f"{value:.2f}")

    def _apply_preset(self, key: str):
        value = _DENOISE_PRESETS.get(key, 0.15)
        self._level_slider.set(value)
        self._on_level_change(value)

    def is_enabled(self) -> bool:
        return self._enable_var.get()

    def get_level(self) -> float | None:
        if not self._enable_var.get():
            return None
        return round(self._level_slider.get(), 2)

    def refresh_texts(self):
        self._enable_check.configure(text=t("denoise.enable"))
        self._preset_frame.winfo_children()
        for i, key in enumerate(_PRESET_KEYS):
            if i < len(self._preset_buttons):
                self._preset_buttons[i].configure(text=t(f"denoise.presets.{key}"))
