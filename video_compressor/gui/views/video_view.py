"""
Video compression view with settings panel, file selection, and progress display.

Implements Issue #8 (Video Compression Settings Panel), Issue #6 (File Selection UI),
and Issue #7 (Compression Execution & Progress Display) for video files.
"""

import os
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ..components.denoise_section import DenoiseSection
from ..components.file_drop_frame import FileDropFrame
from ..components.file_list import FileListFrame
from ..components.progress_panel import ProgressPanel
from ..components.volume_section import VolumeSection
from ..compression_worker import CompressionWorker
from ..i18n import t
from ..theme.fonts import DEFAULT_FONT_FAMILY

_RESOLUTION_KEYS = ["original", "4k", "2k", "1080p", "720p", "480p", "custom"]
_RESOLUTION_VALUES = {
    "original": None,
    "4k": "3840:2160",
    "2k": "2560:1440",
    "1080p": "1920:1080",
    "720p": "1280:720",
    "480p": "854:480",
    "custom": None,
}

_FPS_KEYS = ["unlimited", "24", "25", "30", "48", "50", "60", "90", "120", "144", "240"]
_FPS_VALUES = {
    "unlimited": None,
    "24": 24,
    "25": 25,
    "30": 30,
    "48": 48,
    "50": 50,
    "60": 60,
    "90": 90,
    "120": 120,
    "144": 144,
    "240": 240,
}

_AUDIO_BITRATE_OPTIONS = ["32k", "64k", "96k", "128k", "192k", "256k", "320k"]


class VideoView(ctk.CTkFrame):
    """Full video compression view with file selection, settings, and progress."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._worker = CompressionWorker()
        self._resolution_labels: list[str] = []
        self._fps_labels: list[str] = []

        self._file_queue: list[str] = []
        self._current_index = 0
        self._batch_successes = 0
        self._batch_failures = 0
        self._is_paused = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_file_section()
        self._create_settings_section()
        self._create_progress_section()

    def _create_file_section(self):
        self._file_section = ctk.CTkFrame(self, fg_color="transparent")
        self._file_section.grid(row=0, column=0, sticky="ew")
        self._file_section.grid_columnconfigure(0, weight=1)

        self._file_drop = FileDropFrame(
            self._file_section,
            file_type="video",
            multiple=True,
            on_files_added=self._on_files_added,
        )
        self._file_drop.grid(row=0, column=0, sticky="ew")

        self._file_list = FileListFrame(
            self._file_section,
            on_change=self._update_preview,
        )
        self._file_list.grid(row=1, column=0, sticky="ew")

        output_frame = ctk.CTkFrame(self._file_section, fg_color="transparent")
        output_frame.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")
        output_frame.grid_columnconfigure(1, weight=1)

        self._output_folder_label = ctk.CTkLabel(
            output_frame,
            text=t("file.output_folder"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._output_folder_label.grid(row=0, column=0, padx=(0, 8))

        self._output_folder_entry = ctk.CTkEntry(
            output_frame,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            placeholder_text=t("file.output_folder"),
        )
        self._output_folder_entry.grid(row=0, column=1, sticky="ew")

        self._output_browse_btn = ctk.CTkButton(
            output_frame,
            text=t("file.browse"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            width=70,
            command=self._browse_output_folder,
        )
        self._output_browse_btn.grid(row=0, column=2, padx=(8, 0))

    def _create_settings_section(self):
        self._settings_frame = ctk.CTkScrollableFrame(self)
        self._settings_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._settings_frame.grid_columnconfigure((0, 1), weight=1)

        row = 0

        ctk.CTkLabel(
            self._settings_frame,
            text=t("video_settings.title"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=15, weight="bold"),
        ).grid(row=row, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        row += 1

        self._create_video_column(row)
        self._create_audio_column(row)
        row += 1
        row = self._create_volume_section(row)
        row = self._create_denoise_section(row)
        row = self._create_output_preview(row)
        row = self._create_validation(row)

    def _create_video_column(self, row: int) -> int:
        video_frame = ctk.CTkFrame(self._settings_frame, fg_color="transparent")
        video_frame.grid(row=row, column=0, padx=10, pady=5, sticky="nsew")
        video_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            video_frame,
            text=t("video_settings.video_section"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        crf_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
        crf_frame.grid(row=1, column=0, sticky="ew")
        crf_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            crf_frame,
            text=t("video_settings.crf"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._crf_value_label = ctk.CTkLabel(
            crf_frame,
            text="25",
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
        self._crf_slider.set(25)
        self._crf_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))

        ctk.CTkLabel(
            crf_frame,
            text=t("video_settings.crf_range"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=10),
            text_color=("gray50", "gray60"),
        ).grid(row=2, column=0, columnspan=3, sticky="w")

        preset_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
        preset_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        preset_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            preset_frame,
            text=t("video_settings.preset"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._preset_value_label = ctk.CTkLabel(
            preset_frame,
            text="6",
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
        self._preset_slider.set(6)
        self._preset_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))

        ctk.CTkLabel(
            preset_frame,
            text=t("video_settings.preset_range"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=10),
            text_color=("gray50", "gray60"),
        ).grid(row=2, column=0, columnspan=3, sticky="w")

        res_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
        res_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        res_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            res_frame,
            text=t("video_settings.max_resolution"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._resolution_labels = [t(f"video_settings.resolution.{k}") for k in _RESOLUTION_KEYS]
        self._resolution_var = ctk.StringVar(value=self._resolution_labels[0])
        self._resolution_menu = ctk.CTkOptionMenu(
            res_frame,
            variable=self._resolution_var,
            values=self._resolution_labels,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            command=self._on_resolution_change,
        )
        self._resolution_menu.grid(row=0, column=1, sticky="w")

        self._custom_res_frame = ctk.CTkFrame(res_frame, fg_color="transparent")
        self._custom_res_entry = ctk.CTkEntry(
            self._custom_res_frame,
            width=120,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            placeholder_text="1920x1080",
        )
        self._custom_res_entry.grid(row=0, column=0, padx=(0, 4))

        ctk.CTkLabel(
            self._custom_res_frame,
            text="WxH",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=10),
            text_color=("gray50", "gray60"),
        ).grid(row=0, column=1)

        fps_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
        fps_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        fps_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fps_frame,
            text=t("video_settings.max_fps"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._fps_labels = [t(f"video_settings.fps_options.{k}") for k in _FPS_KEYS]
        self._fps_var = ctk.StringVar(value=self._fps_labels[0])
        self._fps_combo = ctk.CTkComboBox(
            fps_frame,
            variable=self._fps_var,
            values=self._fps_labels,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            command=self._on_fps_change,
        )
        self._fps_combo.grid(row=0, column=1, sticky="w")

        return row + 1

    def _create_audio_column(self, row: int) -> int:
        audio_frame = ctk.CTkFrame(self._settings_frame, fg_color="transparent")
        audio_frame.grid(row=row, column=1, padx=10, pady=5, sticky="nsew")
        audio_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            audio_frame,
            text=t("video_settings.audio_section"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        bitrate_frame = ctk.CTkFrame(audio_frame, fg_color="transparent")
        bitrate_frame.grid(row=1, column=0, sticky="ew")
        bitrate_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            bitrate_frame,
            text=t("video_settings.audio_bitrate"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._audio_bitrate_var = ctk.StringVar(value="192k")
        self._audio_bitrate_combo = ctk.CTkComboBox(
            bitrate_frame,
            variable=self._audio_bitrate_var,
            values=_AUDIO_BITRATE_OPTIONS,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._audio_bitrate_combo.grid(row=0, column=1, sticky="w")

        self._disable_audio_var = ctk.BooleanVar(value=False)
        self._disable_audio_check = ctk.CTkCheckBox(
            audio_frame,
            text=t("video_settings.disable_audio"),
            variable=self._disable_audio_var,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            command=self._on_audio_toggle,
        )
        self._disable_audio_check.grid(row=2, column=0, sticky="w", pady=(10, 3))

        return row + 1

    def _create_output_preview(self, row: int) -> int:
        preview_frame = ctk.CTkFrame(self._settings_frame, fg_color="transparent")
        preview_frame.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        preview_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            preview_frame,
            text=t("audio_settings.output_preview"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._preview_label = ctk.CTkLabel(
            preview_frame,
            text="\u2014",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            text_color=("gray40", "gray60"),
        )
        self._preview_label.grid(row=0, column=1, sticky="w", padx=(10, 0))

        return row + 1

    def _create_volume_section(self, row: int) -> int:
        self._volume_section = VolumeSection(
            self._settings_frame,
            get_current_file=self._get_first_file,
        )
        self._volume_section.grid(row=row, column=0, sticky="ew")
        return row + 1

    def _create_denoise_section(self, row: int) -> int:
        self._denoise_section = DenoiseSection(self._settings_frame)
        self._denoise_section.grid(row=row, column=0, sticky="ew")
        return row + 1

    def _get_first_file(self) -> str | None:
        files = self._file_list.get_file_paths()
        return files[0] if files else None

    def _create_validation(self, row: int) -> int:
        self._error_label = ctk.CTkLabel(
            self._settings_frame,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            text_color="red",
        )
        self._error_label.grid(row=row, column=0, padx=10, sticky="w")

        return row + 1

    def _create_progress_section(self):
        self._progress_panel = ProgressPanel(
            self,
            on_start=self._start_compression,
            on_cancel=self._cancel_compression,
            on_pause=self._on_pause,
        )
        self._progress_panel.grid(row=2, column=0, sticky="ew")

    def _on_crf_change(self, value):
        self._crf_value_label.configure(text=str(int(value)))
        self._update_preview()

    def _on_preset_change(self, value):
        self._preset_value_label.configure(text=str(int(value)))
        self._update_preview()

    def _on_audio_toggle(self):
        if self._disable_audio_var.get():
            self._audio_bitrate_combo.configure(state="disabled")
        else:
            self._audio_bitrate_combo.configure(state="normal")
        self._update_preview()

    def _on_resolution_change(self, _selected):
        is_custom = self._get_resolution_key() == "custom"
        if is_custom:
            self._custom_res_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=3)
        else:
            self._custom_res_frame.grid_forget()
        self._update_preview()

    def _on_fps_change(self, _selected):
        self._update_preview()

    def _on_files_added(self, paths: list[str]):
        self._file_list.add_files(paths)
        self._update_preview()

    def _browse_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self._output_folder_entry.delete(0, "end")
            self._output_folder_entry.insert(0, folder)
            self._update_preview()

    def _update_preview(self):
        files = self._file_list.get_file_paths()
        if not files:
            self._preview_label.configure(text="\u2014")
            return

        input_path = Path(files[0])
        output_name = f"{input_path.stem}_compressed{input_path.suffix}"

        output_folder = self._output_folder_entry.get() or str(input_path.parent)
        preview = os.path.join(output_folder, output_name)
        if len(preview) > 55:
            preview = "..." + preview[-52:]
        self._preview_label.configure(text=preview)

    def _get_resolution_key(self) -> str:
        for i, key in enumerate(_RESOLUTION_KEYS):
            if (
                i < len(self._resolution_labels)
                and self._resolution_var.get() == self._resolution_labels[i]
            ):
                return key
        return "original"

    def _get_fps_key(self) -> str:
        for i, key in enumerate(_FPS_KEYS):
            if i < len(self._fps_labels) and self._fps_var.get() == self._fps_labels[i]:
                return key
        return "unlimited"

    def _get_audio_bitrate_value(self) -> str:
        value = self._audio_bitrate_var.get().strip()
        if not value:
            return "192k"
        if value.lower().endswith("k"):
            return value
        if value.isdigit():
            return f"{value}k"
        return value

    def _get_max_fps_value(self) -> int | None:
        value = self._fps_var.get().strip()
        for i, key in enumerate(_FPS_KEYS):
            if i < len(self._fps_labels) and value == self._fps_labels[i]:
                return _FPS_VALUES.get(key)
        try:
            clean_value = value.upper().replace("FPS", "").strip()
            return int(float(clean_value))
        except ValueError:
            pass
        return None

    def _get_resolution_value(self) -> str | None:
        key = self._get_resolution_key()
        if key == "custom":
            raw = self._custom_res_entry.get().strip()
            if "x" in raw.lower():
                parts = raw.lower().split("x")
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    return f"{parts[0]}:{parts[1]}"
            return None
        return _RESOLUTION_VALUES.get(key)

    def _validate(self) -> str | None:
        files = self._file_list.get_file_paths()
        if not files:
            return t("errors.no_input")

        res_key = self._get_resolution_key()
        if res_key == "custom":
            raw = self._custom_res_entry.get().strip()
            if not raw:
                return "Custom resolution is required (e.g. 1920x1080)"
            if "x" not in raw.lower():
                return "Invalid resolution format. Use WxH (e.g. 1920x1080)"
            parts = raw.lower().split("x")
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                return "Invalid resolution format. Use WxH (e.g. 1920x1080)"

        return None

    def _start_compression(self):
        error = self._validate()
        if error:
            self._error_label.configure(text=error)
            return
        self._error_label.configure(text="")

        self._file_queue = self._file_list.get_file_paths()
        self._current_index = 0
        self._batch_successes = 0
        self._batch_failures = 0
        self._is_paused = False

        self._progress_panel.reset()
        self._progress_panel.set_compressing(True)
        self._progress_panel.update_overall_progress(0, len(self._file_queue))
        self._process_next_file()

    def _process_next_file(self):
        if self._current_index >= len(self._file_queue):
            self._on_batch_complete()
            return

        input_path = self._file_queue[self._current_index]
        input_p = Path(input_path)
        total = len(self._file_queue)
        current = self._current_index + 1

        batch_info = t(
            "batch.processing_file",
            current=current,
            total=total,
            filename=input_p.name,
        )
        self._progress_panel.set_status_text(batch_info)
        self._progress_panel.update_overall_progress(current - 1, total)

        if self._is_paused:
            return

        output_folder = self._output_folder_entry.get() or ""
        if output_folder:
            output_path = str(Path(output_folder) / f"{input_p.stem}_compressed{input_p.suffix}")
        else:
            output_path = str(input_p.parent / f"{input_p.stem}_compressed{input_p.suffix}")

        resolution = self._get_resolution_value()
        max_fps = self._get_max_fps_value()
        audio_bitrate = self._get_audio_bitrate_value()
        audio_enabled = not self._disable_audio_var.get()

        if self._worker.is_running:
            return

        self._worker.start_video_compression(
            input_path=input_path,
            output_path=output_path,
            crf=int(self._crf_slider.get()),
            preset=int(self._preset_slider.get()),
            audio_bitrate=audio_bitrate,
            audio_enabled=audio_enabled,
            max_fps=max_fps,
            resolution=resolution,
            volume_gain_db=self._volume_section.get_volume_gain_db(),
            denoise_level=self._denoise_section.get_level(),
            on_progress=self._on_progress,
            on_complete=self._on_file_complete,
            on_error=self._on_file_error,
        )

    def _on_file_complete(self, result: dict):
        self.after(0, lambda: self._handle_file_complete(result))

    def _handle_file_complete(self, result: dict):
        if result.get("status") == "cancelled":
            self._progress_panel.set_complete(result)
            return

        if result.get("status") == "success":
            self._batch_successes += 1
        else:
            self._batch_failures += 1

        self._current_index += 1
        self._progress_panel.update_overall_progress(self._current_index, len(self._file_queue))

        if self._current_index < len(self._file_queue):
            self._progress_panel.reset_progress_bar()
            self._process_next_file()
        else:
            self._on_batch_complete()

    def _on_file_error(self, error_msg: str):
        self.after(0, lambda: self._handle_file_error(error_msg))

    def _handle_file_error(self, error_msg: str):
        self._batch_failures += 1
        self._progress_panel.add_error_log(
            f"{Path(self._file_queue[self._current_index]).name}: {error_msg}"
        )
        self._current_index += 1
        self._progress_panel.update_overall_progress(self._current_index, len(self._file_queue))

        if self._current_index < len(self._file_queue):
            self._progress_panel.reset_progress_bar()
            self._process_next_file()
        else:
            self._on_batch_complete()

    def _on_batch_complete(self):
        self._progress_panel.set_compressing(False)
        self._progress_panel.set_progress_bar_done()
        self._progress_panel.update_overall_progress(len(self._file_queue), len(self._file_queue))

        total = len(self._file_queue)
        if self._batch_failures == 0:
            msg = t("batch.all_success", count=total)
            self._progress_panel.set_success_status(msg)
        else:
            msg = t(
                "batch.summary",
                success=self._batch_successes,
                failed=self._batch_failures,
            )
            self._progress_panel.set_summary_status(msg)

    def _cancel_compression(self):
        self._worker.cancel()

    def _on_pause(self, is_paused: bool):
        self._is_paused = is_paused
        if (
            not is_paused
            and not self._worker.is_running
            and self._current_index < len(self._file_queue)
        ):
            self._process_next_file()

    def _on_progress(self, progress: dict):
        self.after(0, lambda: self._progress_panel.update_progress(progress))

    def refresh_texts(self):
        self._file_drop.refresh_texts()
        self._file_list.refresh_texts()
        self._output_folder_label.configure(text=t("file.output_folder"))
        self._output_browse_btn.configure(text=t("file.browse"))
        self._progress_panel.refresh_texts()
        self._volume_section.refresh_texts()
        self._denoise_section.refresh_texts()

        self._resolution_labels = [t(f"video_settings.resolution.{k}") for k in _RESOLUTION_KEYS]
        current_res_idx = _RESOLUTION_KEYS.index(self._get_resolution_key())
        self._resolution_var.set(self._resolution_labels[current_res_idx])
        self._resolution_menu.configure(values=self._resolution_labels)

        self._fps_labels = [t(f"video_settings.fps_options.{k}") for k in _FPS_KEYS]
        current_fps_idx = _FPS_KEYS.index(self._get_fps_key())
        self._fps_var.set(self._fps_labels[current_fps_idx])
        self._fps_combo.configure(values=self._fps_labels)

        self._update_preview()
