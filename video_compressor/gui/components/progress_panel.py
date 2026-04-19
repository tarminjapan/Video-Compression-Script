"""
Compression progress panel for AmeCompression GUI.

Displays progress bar, statistics, control buttons, and error log.
"""

import customtkinter as ctk

from ..i18n import t
from ..theme.fonts import DEFAULT_FONT_FAMILY


class ProgressPanel(ctk.CTkFrame):
    """Panel showing compression progress with start/cancel/pause controls."""

    def __init__(self, master, on_start=None, on_cancel=None, on_pause=None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_start = on_start
        self._on_cancel = on_cancel
        self._on_pause = on_pause
        self._is_paused = False

        self.grid_columnconfigure(0, weight=1)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)

        self._start_btn = ctk.CTkButton(
            btn_frame,
            text=t("compress.start"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=14, weight="bold"),
            height=38,
            command=self._handle_start,
        )
        self._start_btn.grid(row=0, column=0, sticky="w")

        self._pause_btn = ctk.CTkButton(
            btn_frame,
            text=t("batch.pause"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=13),
            height=38,
            width=100,
            state="disabled",
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            command=self._handle_pause,
        )
        self._pause_btn.grid(row=0, column=1, padx=(10, 0))

        self._cancel_btn = ctk.CTkButton(
            btn_frame,
            text=t("compress.cancel"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=13),
            height=38,
            width=100,
            state="disabled",
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            command=self._handle_cancel,
        )
        self._cancel_btn.grid(row=0, column=2, padx=(10, 0))

        self._overall_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            text_color=("gray40", "gray60"),
        )
        self._overall_label.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")

        self._overall_progress_bar = ctk.CTkProgressBar(self, height=8)
        self._overall_progress_bar.grid(row=2, column=0, padx=10, pady=(2, 2), sticky="ew")
        self._overall_progress_bar.set(0)

        self._progress_bar = ctk.CTkProgressBar(self, height=12)
        self._progress_bar.grid(row=3, column=0, padx=10, pady=(2, 2), sticky="ew")
        self._progress_bar.set(0)

        self._stats_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            text_color=("gray40", "gray60"),
        )
        self._stats_label.grid(row=4, column=0, padx=10, sticky="w")

        self._status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=13, weight="bold"),
        )
        self._status_label.grid(row=5, column=0, padx=10, pady=(5, 0), sticky="w")

        self._error_textbox = ctk.CTkTextbox(
            self,
            height=60,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            state="disabled",
            wrap="word",
        )
        self._error_textbox.grid(row=6, column=0, padx=10, pady=(5, 10), sticky="ew")

    def _handle_start(self):
        if self._on_start:
            self._on_start()

    def _handle_cancel(self):
        if self._on_cancel:
            self._on_cancel()

    def _handle_pause(self):
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._pause_btn.configure(text=t("batch.resume"))
            self._status_label.configure(
                text=t("batch.paused"),
                text_color=("orange", "orange"),
            )
        else:
            self._pause_btn.configure(text=t("batch.pause"))
        if self._on_pause:
            self._on_pause(self._is_paused)

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def set_compressing(self, is_compressing: bool):
        if is_compressing:
            self._start_btn.configure(state="disabled")
            self._cancel_btn.configure(state="normal")
            self._pause_btn.configure(state="normal")
            self._is_paused = False
            self._pause_btn.configure(text=t("batch.pause"))
            self._status_label.configure(
                text=t("compress.compressing"),
                text_color=("blue", "lightblue"),
            )
            self._progress_bar.set(0)
            self._overall_progress_bar.set(0)
            self._stats_label.configure(text="")
            self._overall_label.configure(text="")
            self._clear_errors()
        else:
            self._start_btn.configure(state="normal")
            self._cancel_btn.configure(state="disabled")
            self._pause_btn.configure(state="disabled")
            self._is_paused = False

    def update_progress(self, progress: dict):
        percent = progress.get("percent", 0)
        self._progress_bar.set(percent / 100)

        fps = progress.get("fps", 0)
        speed = progress.get("speed", 0)
        eta = progress.get("eta", 0)

        eta_min = int(eta // 60)
        eta_sec = int(eta % 60)
        eta_str = f"{eta_min:02d}:{eta_sec:02d}" if eta > 0 else "--:--"

        stats_text = (
            f"{percent:.1f}%  |  "
            f"{t('compress.eta')}: {eta_str}  |  "
            f"{t('compress.fps')}: {fps:.0f}  |  "
            f"{t('compress.speed')}: {speed:.1f}x"
        )
        self._stats_label.configure(text=stats_text)

    def set_complete(self, result: dict):
        self.set_compressing(False)
        self._progress_bar.set(1.0)

        if result.get("status") == "cancelled":
            self._status_label.configure(
                text=t("compress.cancelled"),
                text_color=("orange", "orange"),
            )
        elif result.get("status") == "success":
            self._status_label.configure(
                text=t("compress.complete"),
                text_color=("green", "#90EE90"),
            )

    def set_result(self, original_size: float, compressed_size: float):
        reduction = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        result_text = (
            f"{t('compress.original_size')}: {original_size:.2f} MB  \u2192  "
            f"{t('compress.compressed_size')}: {compressed_size:.2f} MB  |  "
            f"{t('compress.reduction')}: {reduction:.1f}%"
        )
        self._status_label.configure(text=result_text)

    def set_error(self, error_msg: str):
        self.set_compressing(False)
        self._status_label.configure(
            text=f"{t('compress.failed')}: {error_msg}",
            text_color=("red", "#FF6B6B"),
        )
        self._error_textbox.configure(state="normal")
        self._error_textbox.insert("end", error_msg + "\n")
        self._error_textbox.configure(state="disabled")

    def add_error_log(self, msg: str):
        self._error_textbox.configure(state="normal")
        self._error_textbox.insert("end", msg + "\n")
        self._error_textbox.configure(state="disabled")

    def _clear_errors(self):
        self._error_textbox.configure(state="normal")
        self._error_textbox.delete("1.0", "end")
        self._error_textbox.configure(state="disabled")

    def reset(self):
        self._progress_bar.set(0)
        self._overall_progress_bar.set(0)
        self._stats_label.configure(text="")
        self._status_label.configure(text="")
        self._overall_label.configure(text="")
        self._clear_errors()
        self.set_compressing(False)

    def reset_progress_bar(self):
        self._progress_bar.set(0)
        self._stats_label.configure(text="")

    def set_progress_bar_done(self):
        self._progress_bar.set(1.0)

    def set_status_text(self, text: str):
        self._status_label.configure(text=text, text_color=("blue", "lightblue"))

    def set_success_status(self, text: str):
        self._status_label.configure(text=text, text_color=("green", "#90EE90"))

    def set_summary_status(self, text: str):
        self._status_label.configure(text=text, text_color=("orange", "orange"))

    def update_overall_progress(self, current: int, total: int):
        if total > 0:
            self._overall_progress_bar.set(current / total)
            self._overall_label.configure(
                text=t("batch.overall_progress", current=current, total=total)
            )

    def refresh_texts(self):
        self._start_btn.configure(text=t("compress.start"))
        self._cancel_btn.configure(text=t("compress.cancel"))
        if self._is_paused:
            self._pause_btn.configure(text=t("batch.resume"))
        else:
            self._pause_btn.configure(text=t("batch.pause"))
