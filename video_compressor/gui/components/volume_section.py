"""
Volume adjustment settings section for AmeCompression GUI.

Provides mode selection (disabled/auto/multiplier/dB), sliders,
volume analysis button, and visual level meter.
"""

import math
import threading

import customtkinter as ctk

from ..i18n import t
from ..theme.fonts import DEFAULT_FONT_FAMILY

_VOLUME_MODE_KEYS = ["disabled", "auto", "multiplier", "db"]

_MULTIPLIER_MIN = 0.1
_MULTIPLIER_MAX = 5.0
_DB_MIN = -20.0
_DB_MAX = 20.0


class VolumeSection(ctk.CTkFrame):
    """Volume adjustment settings with mode selection, sliders, and analysis."""

    def __init__(self, master, get_current_file=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._get_current_file = get_current_file
        self._analysis_result: dict | None = None
        self.grid_columnconfigure(0, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        row = 0

        ctk.CTkLabel(
            self,
            text=t("volume.title"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=14, weight="bold"),
        ).grid(row=row, column=0, padx=10, pady=(10, 5), sticky="w")
        row += 1

        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
        mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            mode_frame,
            text=t("volume.mode"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._mode_labels = [t(f"volume.modes.{k}") for k in _VOLUME_MODE_KEYS]
        self._mode_var = ctk.StringVar(value=self._mode_labels[0])
        self._mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            variable=self._mode_var,
            values=self._mode_labels,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            command=self._on_mode_change,
        )
        self._mode_menu.grid(row=0, column=1, sticky="w", padx=(8, 0))
        row += 1

        self._slider_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._slider_frame.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
        self._slider_frame.grid_columnconfigure(1, weight=1)
        self._create_multiplier_slider()
        self._create_db_slider()
        row += 1

        self._analyze_btn = ctk.CTkButton(
            self,
            text=t("volume.analyze"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            width=140,
            height=28,
            command=self._analyze_volume,
        )
        self._analyze_btn.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        row += 1

        self._result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._result_frame.grid(row=row, column=0, padx=10, pady=(0, 5), sticky="ew")
        self._result_frame.grid_columnconfigure(0, weight=1)
        self._create_result_display()
        row += 1

        self._on_mode_change(self._mode_labels[0])

    def _create_multiplier_slider(self):
        ctk.CTkLabel(
            self._slider_frame,
            text=t("volume.multiplier_label"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._mult_value_label = ctk.CTkLabel(
            self._slider_frame,
            text="1.0x",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12, weight="bold"),
            width=50,
        )
        self._mult_value_label.grid(row=0, column=2, padx=(5, 0))

        self._mult_slider = ctk.CTkSlider(
            self._slider_frame,
            from_=_MULTIPLIER_MIN,
            to=_MULTIPLIER_MAX,
            number_of_steps=49,
            command=self._on_mult_change,
        )
        self._mult_slider.set(1.0)
        self._mult_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))

    def _create_db_slider(self):
        ctk.CTkLabel(
            self._slider_frame,
            text=t("volume.db_label"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=2, column=0, sticky="w")

        self._db_value_label = ctk.CTkLabel(
            self._slider_frame,
            text="0.0 dB",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12, weight="bold"),
            width=60,
        )
        self._db_value_label.grid(row=2, column=2, padx=(5, 0))

        self._db_slider = ctk.CTkSlider(
            self._slider_frame,
            from_=_DB_MIN,
            to=_DB_MAX,
            number_of_steps=80,
            command=self._on_db_change,
        )
        self._db_slider.set(0.0)
        self._db_slider.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(2, 0))

    def _create_result_display(self):
        self._mean_vol_label = ctk.CTkLabel(
            self._result_frame,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            text_color=("gray40", "gray60"),
        )
        self._mean_vol_label.grid(row=0, column=0, sticky="w")

        self._max_vol_label = ctk.CTkLabel(
            self._result_frame,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            text_color=("gray40", "gray60"),
        )
        self._max_vol_label.grid(row=1, column=0, sticky="w")

        self._gain_label = ctk.CTkLabel(
            self._result_frame,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11, weight="bold"),
        )
        self._gain_label.grid(row=2, column=0, sticky="w")

        self._meter_frame = ctk.CTkFrame(self._result_frame, height=16, fg_color="transparent")
        self._meter_frame.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        self._meter_frame.grid_columnconfigure(0, weight=1)

        self._meter_bg = ctk.CTkFrame(
            self._meter_frame,
            height=12,
            fg_color=("gray80", "gray25"),
            corner_radius=4,
        )
        self._meter_bg.grid(row=0, column=0, sticky="ew")
        self._meter_bg.grid_columnconfigure(0, weight=1)

        self._meter_bar = ctk.CTkFrame(
            self._meter_bg,
            width=0,
            height=12,
            fg_color=("green", "#90EE90"),
            corner_radius=4,
        )
        self._meter_bar.place(x=0, y=0, relheight=1.0, relwidth=0)

    def _on_mode_change(self, _selected):
        mode = self._get_mode_key()

        if mode == "multiplier":
            self._mult_slider.grid()
            self._mult_value_label.grid()
            self._db_slider.grid_remove()
            self._db_value_label.grid_remove()
        elif mode == "db":
            self._mult_slider.grid_remove()
            self._mult_value_label.grid_remove()
            self._db_slider.grid()
            self._db_value_label.grid()
        else:
            self._mult_slider.grid_remove()
            self._mult_value_label.grid_remove()
            self._db_slider.grid_remove()
            self._db_value_label.grid_remove()

    def _on_mult_change(self, value):
        self._mult_value_label.configure(text=f"{value:.1f}x")

    def _on_db_change(self, value):
        sign = "+" if value >= 0 else ""
        self._db_value_label.configure(text=f"{sign}{value:.1f} dB")

    def _get_mode_key(self) -> str:
        for i, key in enumerate(_VOLUME_MODE_KEYS):
            if i < len(self._mode_labels) and self._mode_var.get() == self._mode_labels[i]:
                return key
        return "disabled"

    def _analyze_volume(self):
        file_path = self._get_current_file() if self._get_current_file else None
        if not file_path:
            self._mean_vol_label.configure(text=t("volume.no_file"))
            return

        self._analyze_btn.configure(state="disabled", text=t("volume.analyzing"))

        def run_analysis():
            try:
                from ...ffmpeg import get_ffmpeg_executables
                from ...volume import analyze_volume_level

                ffmpeg_path, _ = get_ffmpeg_executables()
                result = analyze_volume_level(file_path, ffmpeg_path)
                self._analysis_result = result
                self.after(0, lambda: self._update_analysis_display(result))
            except Exception:
                self.after(0, lambda: self._on_analysis_error("Analysis failed"))

        threading.Thread(target=run_analysis, daemon=True).start()

    def _update_analysis_display(self, result: dict):
        self._analyze_btn.configure(state="normal", text=t("volume.analyze"))

        mean_vol = result.get("mean_volume")
        max_vol = result.get("max_volume")
        rec_gain = result.get("recommended_gain")

        if mean_vol is not None:
            self._mean_vol_label.configure(text=f"{t('volume.mean_volume')}: {mean_vol:.1f} dB")
        else:
            self._mean_vol_label.configure(text=f"{t('volume.mean_volume')}: ---")

        if max_vol is not None:
            self._max_vol_label.configure(text=f"{t('volume.max_volume')}: {max_vol:.1f} dB")
        else:
            self._max_vol_label.configure(text=f"{t('volume.max_volume')}: ---")

        if rec_gain is not None:
            sign = "+" if rec_gain >= 0 else ""
            self._gain_label.configure(
                text=f"{t('volume.recommended_gain')}: {sign}{rec_gain:.1f} dB"
            )
        else:
            self._gain_label.configure(text="")

        if mean_vol is not None:
            normalized = max(0.0, min(1.0, (mean_vol + 60) / 60))
            self._update_meter(normalized)

    def _on_analysis_error(self, error_msg: str):
        self._analyze_btn.configure(state="normal", text=t("volume.analyze"))
        self._mean_vol_label.configure(text=f"{t('common.error')}: {error_msg}")

    def _update_meter(self, level: float):
        level = max(0.0, min(1.0, level))
        if level > 0.8:
            color = ("red", "#FF6B6B")
        elif level > 0.6:
            color = ("orange", "orange")
        else:
            color = ("green", "#90EE90")

        self._meter_bar.place(x=0, y=0, relheight=1.0, relwidth=level)
        self._meter_bar.configure(fg_color=color)

    def get_volume_gain_db(self) -> float | None:
        mode = self._get_mode_key()
        if mode == "disabled":
            return None
        if mode == "multiplier":
            mult = self._mult_slider.get()
            if mult <= 0:
                return None
            return round(20 * math.log10(mult), 1)
        if mode == "db":
            return round(self._db_slider.get(), 1)
        return None

    def get_mode(self) -> str:
        return self._get_mode_key()

    def get_analysis_result(self) -> dict | None:
        return self._analysis_result

    def refresh_texts(self):
        self._mode_labels = [t(f"volume.modes.{k}") for k in _VOLUME_MODE_KEYS]
        current_idx = _VOLUME_MODE_KEYS.index(self._get_mode_key())
        self._mode_var.set(self._mode_labels[current_idx])
        self._mode_menu.configure(values=self._mode_labels)
        self._analyze_btn.configure(text=t("volume.analyze"))
