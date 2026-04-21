"""
Audio compression view with settings panel, file selection, and progress display.

Implements Issue #5 (Audio Compression Settings Panel), Issue #6 (File Selection UI),
and Issue #7 (Compression Execution & Progress Display) for audio files.
"""

import os
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...config import MP3_BITRATE_MAX, MP3_BITRATE_MIN
from ..components.denoise_section import DenoiseSection
from ..components.file_drop_frame import FileDropFrame
from ..components.file_list import FileListFrame
from ..components.progress_panel import ProgressPanel
from ..components.volume_section import VolumeSection
from ..compression_worker import CompressionWorker
from ..i18n import t
from ..theme.fonts import DEFAULT_FONT_FAMILY
from ..utils import SettingsManager


class AudioView(ctk.CTkFrame):
    """Full audio compression view with file selection, settings, and progress."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._worker = CompressionWorker()
        self._file_queue: list[str] = []
        self._current_index = 0
        self._batch_successes = 0
        self._batch_failures = 0
        self._is_paused = False

        self._settings = SettingsManager.get_instance()
        _raw_bitrate = self._settings.get("default_audio_bitrate", "192k")
        if isinstance(_raw_bitrate, str) and _raw_bitrate.endswith("k"):
            self._default_bitrate: int = int(_raw_bitrate[:-1])
        else:
            self._default_bitrate = int(_raw_bitrate) if _raw_bitrate is not None else 192
        _raw_output = self._settings.get("default_output_folder", "")
        self._default_output_folder: str = str(_raw_output) if _raw_output is not None else ""

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
            file_type="audio",
            multiple=True,
            on_files_added=self._on_files_added,
        )
        self._file_drop.grid(row=0, column=0, sticky="ew")

        self._file_list = FileListFrame(
            self._file_section,
            on_change=self._on_file_change,
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
        if self._default_output_folder:
            self._output_folder_entry.insert(0, self._default_output_folder)

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
        self._settings_frame.grid(row=1, column=0, sticky="nsew")
        self._settings_frame.grid_columnconfigure(0, weight=1)

        row = 0

        ctk.CTkLabel(
            self._settings_frame,
            text=t("audio_settings.title"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=15, weight="bold"),
        ).grid(row=row, column=0, padx=10, pady=(10, 5), sticky="w")
        row += 1

        row = self._create_bitrate_slider(row)

        self._keep_metadata_var = ctk.BooleanVar(value=True)
        self._keep_metadata_check = ctk.CTkCheckBox(
            self._settings_frame,
            text=t("audio_settings.keep_metadata"),
            variable=self._keep_metadata_var,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._keep_metadata_check.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        row += 1

        row = self._create_volume_section(row)
        row = self._create_denoise_section(row)
        row = self._create_input_info(row)
        row = self._create_output_preview(row)

    def _create_bitrate_slider(self, row: int) -> int:
        bitrate_frame = ctk.CTkFrame(self._settings_frame, fg_color="transparent")
        bitrate_frame.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
        bitrate_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            bitrate_frame,
            text=t("audio_settings.bitrate"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._bitrate_value_label = ctk.CTkLabel(
            bitrate_frame,
            text=f"{self._default_bitrate} kbps",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12, weight="bold"),
            width=80,
        )
        self._bitrate_value_label.grid(row=0, column=2, padx=(5, 0))

        self._bitrate_slider = ctk.CTkSlider(
            bitrate_frame,
            from_=MP3_BITRATE_MIN,
            to=MP3_BITRATE_MAX,
            number_of_steps=(MP3_BITRATE_MAX - MP3_BITRATE_MIN) // 8,
            command=self._on_bitrate_change,
        )
        self._bitrate_slider.set(self._default_bitrate)
        self._bitrate_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))

        range_frame = ctk.CTkFrame(bitrate_frame, fg_color="transparent")
        range_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        range_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            range_frame,
            text=f"{MP3_BITRATE_MIN}k",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=10),
            text_color=("gray50", "gray60"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            range_frame,
            text=f"{MP3_BITRATE_MAX}k",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=10),
            text_color=("gray50", "gray60"),
        ).grid(row=0, column=2, sticky="e")

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

    def _create_input_info(self, row: int) -> int:
        self._info_frame = ctk.CTkFrame(self._settings_frame, fg_color="transparent")
        self._info_frame.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        self._info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._info_frame,
            text=t("audio_settings.input_info"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        self._info_label = ctk.CTkLabel(
            self._info_frame,
            text="\u2014",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            text_color=("gray40", "gray60"),
            wraplength=600,
            justify="left",
        )
        self._info_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

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

    def _create_progress_section(self):
        self._progress_panel = ProgressPanel(
            self,
            on_start=self._start_compression,
            on_cancel=self._cancel_compression,
            on_pause=self._on_pause,
        )
        self._progress_panel.grid(row=2, column=0, sticky="ew")

    def _on_bitrate_change(self, value):
        kbps = int(value)
        kbps = max(MP3_BITRATE_MIN, min(MP3_BITRATE_MAX, round(kbps / 8) * 8))
        self._bitrate_value_label.configure(text=f"{kbps} kbps")
        self._update_preview()

    def _on_files_added(self, paths: list[str]):
        self._file_list.add_files(paths)
        self._on_file_change()

    def _on_file_change(self):
        self._update_preview()
        self._update_input_info()

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
        output_name = f"{input_path.stem}_compressed.mp3"

        output_folder = self._output_folder_entry.get() or str(input_path.parent)
        preview = os.path.join(output_folder, output_name)
        if len(preview) > 55:
            preview = "..." + preview[-52:]
        self._preview_label.configure(text=preview)

    def _update_input_info(self):
        files = self._file_list.get_file_paths()
        if not files:
            self._info_label.configure(text="\u2014")
            return

        def fetch_info():
            try:
                from ...ffmpeg import get_audio_info, get_ffmpeg_executables

                _, ffprobe_path = get_ffmpeg_executables()
                info = get_audio_info(files[0], ffprobe_path)

                parts: list[str] = []
                ext = Path(files[0]).suffix.upper().lstrip(".")
                parts.append(ext)
                if info.get("bitrate"):
                    parts.append(f"{info['bitrate'] // 1000} kbps")
                if info.get("sample_rate"):
                    parts.append(f"{info['sample_rate']} Hz")
                if info.get("channels"):
                    ch = info["channels"]
                    ch_str = (
                        t("common.mono")
                        if ch == 1
                        else t("common.stereo")
                        if ch == 2
                        else t("common.channels", count=ch)
                    )
                    parts.append(ch_str)
                if info.get("duration"):
                    dur = info["duration"]
                    m, s = int(dur // 60), dur % 60
                    parts.append(f"{m:02d}:{s:04.1f}")

                text = " | ".join(parts) if parts else "\u2014"
                self.after(0, lambda: self._info_label.configure(text=text))
            except Exception:
                self.after(0, lambda: self._info_label.configure(text="\u2014"))

        threading.Thread(target=fetch_info, daemon=True).start()

    def _start_compression(self):
        files = self._file_list.get_file_paths()
        if not files:
            return

        self._file_queue = files
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
            output_path = str(Path(output_folder) / f"{input_p.stem}_compressed.mp3")
        else:
            output_path = str(input_p.parent / f"{input_p.stem}_compressed.mp3")

        kbps = int(self._bitrate_slider.get())
        kbps = max(MP3_BITRATE_MIN, min(MP3_BITRATE_MAX, round(kbps / 8) * 8))
        bitrate = f"{kbps}k"
        keep_metadata = self._keep_metadata_var.get()

        if self._worker.is_running:
            return

        self._worker.start_audio_compression(
            input_path=input_path,
            output_path=output_path,
            bitrate=bitrate,
            keep_metadata=keep_metadata,
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
        self._update_preview()
