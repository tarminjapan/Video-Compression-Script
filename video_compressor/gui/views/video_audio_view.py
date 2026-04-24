"""
Unified Video/Audio compression view.

Merges the previous VideoView and AudioView into a single screen with
video settings, audio settings, file selection, and progress display.

Implements Issue #36 (Video / Audio screen integration) and
Issue #37 (UI improvements).
"""

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...config import AUDIO_EXTENSIONS, MP3_BITRATE_MAX, MP3_BITRATE_MIN, VIDEO_EXTENSIONS
from ...ffmpeg import get_audio_info, get_video_info
from ..components.denoise_section import DenoiseSection
from ..components.file_drop_frame import FileDropFrame
from ..components.file_list import FileListFrame
from ..components.progress_panel import ProgressPanel
from ..components.volume_section import VolumeSection
from ..compression_worker import CompressionWorker
from ..i18n import t
from ..theme.fonts import DEFAULT_FONT_FAMILY
from ..utils import SettingsManager

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

_VIDEO_AUDIO_BITRATE_OPTIONS = ["32k", "64k", "96k", "128k", "192k", "256k", "320k"]


class VideoAudioView(ctk.CTkFrame):
    """Unified video/audio compression view with file selection, settings, and progress."""

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
        self._info_request_id = 0

        self._settings = SettingsManager.get_instance()
        _raw_crf = self._settings.get("default_crf", 25)
        self._default_crf: int = int(_raw_crf) if _raw_crf is not None else 25
        _raw_preset = self._settings.get("default_preset", 6)
        self._default_preset: int = int(_raw_preset) if _raw_preset is not None else 6
        _raw_bitrate = self._settings.get("default_audio_bitrate", "192k")
        self._default_audio_bitrate: str = str(_raw_bitrate) if _raw_bitrate is not None else "192k"
        _raw_mp3_bitrate = self._settings.get("default_mp3_bitrate") or self._settings.get(
            "default_audio_bitrate", "192k"
        )
        if isinstance(_raw_mp3_bitrate, str) and _raw_mp3_bitrate.endswith("k"):
            self._default_mp3_bitrate: int = int(_raw_mp3_bitrate[:-1])
        else:
            self._default_mp3_bitrate = (
                int(_raw_mp3_bitrate) if _raw_mp3_bitrate is not None else 192
            )
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
            file_type="all",
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
        self._create_video_audio_column(row)
        row += 1

        self._audio_settings_title = ctk.CTkLabel(
            self._settings_frame,
            text=t("audio_settings.title"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=15, weight="bold"),
        )
        self._audio_settings_title.grid(
            row=row, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w"
        )
        row += 1

        row = self._create_mp3_bitrate_slider(row)

        self._keep_metadata_var = ctk.BooleanVar(value=True)
        self._keep_metadata_check = ctk.CTkCheckBox(
            self._settings_frame,
            text=t("audio_settings.keep_metadata"),
            variable=self._keep_metadata_var,
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._keep_metadata_check.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        row += 1

        row = self._create_volume_section(row)
        row = self._create_denoise_section(row)
        row = self._create_input_info(row)
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
            text=str(self._default_crf),
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
        self._crf_slider.set(self._default_crf)
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
            text=str(self._default_preset),
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
        self._preset_slider.set(self._default_preset)
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

    def _create_video_audio_column(self, row: int) -> int:
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

        self._audio_bitrate_var = ctk.StringVar(value=self._default_audio_bitrate)
        self._audio_bitrate_combo = ctk.CTkComboBox(
            bitrate_frame,
            variable=self._audio_bitrate_var,
            values=_VIDEO_AUDIO_BITRATE_OPTIONS,
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

    def _create_mp3_bitrate_slider(self, row: int) -> int:
        bitrate_frame = ctk.CTkFrame(self._settings_frame, fg_color="transparent")
        bitrate_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=2, sticky="ew")
        bitrate_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            bitrate_frame,
            text=t("audio_settings.bitrate"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        ).grid(row=0, column=0, sticky="w")

        self._mp3_bitrate_value_label = ctk.CTkLabel(
            bitrate_frame,
            text=f"{self._default_mp3_bitrate} kbps",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12, weight="bold"),
            width=80,
        )
        self._mp3_bitrate_value_label.grid(row=0, column=2, padx=(5, 0))

        self._mp3_bitrate_slider = ctk.CTkSlider(
            bitrate_frame,
            from_=MP3_BITRATE_MIN,
            to=MP3_BITRATE_MAX,
            number_of_steps=(MP3_BITRATE_MAX - MP3_BITRATE_MIN) // 8,
            command=self._on_mp3_bitrate_change,
        )
        self._mp3_bitrate_slider.set(self._default_mp3_bitrate)
        self._mp3_bitrate_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))

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

    def _create_output_preview(self, row: int) -> int:
        preview_frame = ctk.CTkFrame(self._settings_frame, fg_color="transparent")
        preview_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
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
        self._volume_section.grid(row=row, column=0, columnspan=2, sticky="ew")
        return row + 1

    def _create_denoise_section(self, row: int) -> int:
        self._denoise_section = DenoiseSection(self._settings_frame)
        self._denoise_section.grid(row=row, column=0, columnspan=2, sticky="ew")
        return row + 1

    def _get_first_file(self) -> str | None:
        files = self._file_list.get_file_paths()
        return files[0] if files else None

    def _create_input_info(self, row: int) -> int:
        self._info_frame = ctk.CTkFrame(self._settings_frame, fg_color="transparent")
        self._info_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
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

    def _create_validation(self, row: int) -> int:
        self._error_label = ctk.CTkLabel(
            self._settings_frame,
            text="",
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            text_color="red",
        )
        self._error_label.grid(row=row, column=0, columnspan=2, padx=10, sticky="w")

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

    def _on_mp3_bitrate_change(self, value):
        kbps = self._get_rounded_mp3_bitrate(value)
        self._mp3_bitrate_value_label.configure(text=f"{kbps} kbps")
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

    def _get_file_type(self, path: str) -> str:
        ext = Path(path).suffix.lower()
        if ext in VIDEO_EXTENSIONS:
            return "video"
        if ext in AUDIO_EXTENSIONS:
            return "audio"
        return "video"

    def _get_rounded_mp3_bitrate(self, value: float) -> int:
        kbps = int(value)
        return max(MP3_BITRATE_MIN, min(MP3_BITRATE_MAX, round(kbps / 8) * 8))

    def _get_output_path(self, input_path: str) -> str:
        input_p = Path(input_path)
        output_folder = self._output_folder_entry.get() or str(input_p.parent)
        file_type = self._get_file_type(input_path)
        if file_type == "audio":
            output_name = f"{input_p.stem}_compressed.mp3"
        else:
            output_name = f"{input_p.stem}_compressed{input_p.suffix}"
        return str(Path(output_folder) / output_name)

    def _update_preview(self):
        files = self._file_list.get_file_paths()
        if not files:
            self._preview_label.configure(text="\u2014")
            return

        preview = self._get_output_path(files[0])
        if len(preview) > 55:
            preview = "..." + preview[-52:]
        self._preview_label.configure(text=preview)

    def _update_input_info(self):
        files = self._file_list.get_file_paths()
        if not files:
            self._info_label.configure(text="\u2014")
            return

        first_file = files[0]
        self._info_request_id += 1
        request_id = self._info_request_id

        def fetch_info():
            if request_id != self._info_request_id:
                return
            try:
                _, ffprobe_path = CompressionWorker._resolve_ffmpeg_paths()
                file_type = self._get_file_type(first_file)
                parts: list[str] = []
                ext = Path(first_file).suffix.upper().lstrip(".")
                parts.append(ext)

                if file_type == "audio":
                    info = get_audio_info(first_file, ffprobe_path)
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
                else:
                    info = get_video_info(first_file, ffprobe_path)
                    if info:
                        if info.get("width") and info.get("height"):
                            parts.append(f"{info['width']}x{info['height']}")
                        if info.get("fps"):
                            parts.append(f"{info['fps']:.2f} FPS")
                    if info and info.get("duration"):
                        dur = info["duration"]
                        m, s = int(dur // 60), dur % 60
                        parts.append(f"{m:02d}:{s:04.1f}")

                text = " | ".join(parts) if parts else "\u2014"
                if request_id == self._info_request_id and self.winfo_exists():
                    self.after(0, lambda: self._info_label.configure(text=text))
            except Exception:
                if request_id == self._info_request_id and self.winfo_exists():
                    self.after(0, lambda: self._info_label.configure(text="\u2014"))

        threading.Thread(target=fetch_info, daemon=True).start()

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

    @staticmethod
    def _parse_custom_resolution(raw: str) -> tuple[str, str] | None:
        if "x" not in raw.lower():
            return None
        parts = raw.lower().split("x")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return parts[0], parts[1]
        return None

    def _get_resolution_value(self) -> str | None:
        key = self._get_resolution_key()
        if key == "custom":
            raw = self._custom_res_entry.get().strip()
            parsed = self._parse_custom_resolution(raw)
            if parsed:
                return f"{parsed[0]}:{parsed[1]}"
            return None
        return _RESOLUTION_VALUES.get(key)

    def _has_video_files(self) -> bool:
        return any(self._get_file_type(f) == "video" for f in self._file_list.get_file_paths())

    def _validate(self) -> str | None:
        files = self._file_list.get_file_paths()
        if not files:
            return t("errors.no_input")

        if self._has_video_files():
            res_key = self._get_resolution_key()
            if res_key == "custom":
                raw = self._custom_res_entry.get().strip()
                if not raw:
                    return t("errors.custom_resolution_required")
                if not self._parse_custom_resolution(raw):
                    return t("errors.invalid_resolution_format")

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

        file_type = self._get_file_type(input_path)
        output_path = self._get_output_path(input_path)

        if file_type == "audio":
            self._start_audio_file(input_path, output_path)
        else:
            self._start_video_file(input_path, output_path)

    def _start_video_file(self, input_path: str, output_path: str):
        if self._worker.is_running:
            return

        resolution = self._get_resolution_value()
        max_fps = self._get_max_fps_value()
        audio_bitrate = self._get_audio_bitrate_value()
        audio_enabled = not self._disable_audio_var.get()

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

    def _start_audio_file(self, input_path: str, output_path: str):
        if self._worker.is_running:
            return

        kbps = self._get_rounded_mp3_bitrate(self._mp3_bitrate_slider.get())
        bitrate = f"{kbps}k"
        keep_metadata = self._keep_metadata_var.get()

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
        self._audio_settings_title.configure(text=t("audio_settings.title"))
        self._keep_metadata_check.configure(text=t("audio_settings.keep_metadata"))

        self._resolution_labels = [t(f"video_settings.resolution.{k}") for k in _RESOLUTION_KEYS]
        current_res_idx = _RESOLUTION_KEYS.index(self._get_resolution_key())
        self._resolution_var.set(self._resolution_labels[current_res_idx])
        self._resolution_menu.configure(values=self._resolution_labels)

        self._fps_labels = [t(f"video_settings.fps_options.{k}") for k in _FPS_KEYS]
        current_fps_idx = _FPS_KEYS.index(self._get_fps_key())
        self._fps_var.set(self._fps_labels[current_fps_idx])
        self._fps_combo.configure(values=self._fps_labels)

        self._update_preview()
