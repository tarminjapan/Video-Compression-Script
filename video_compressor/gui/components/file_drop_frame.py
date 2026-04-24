"""
File drop area and browse button component for AmeCompression GUI.

Provides a visual drop zone with optional drag-and-drop support
(via windnd on Windows) and a browse button for file selection.
"""

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...config import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS
from ..i18n import t
from ..theme.fonts import DEFAULT_FONT_FAMILY


class FileDropFrame(ctk.CTkFrame):
    """File selection area with visual drop zone and browse button."""

    def __init__(
        self,
        master,
        file_type: str = "all",
        multiple: bool = True,
        on_files_added=None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._file_type = file_type
        self._multiple = multiple
        self._on_files_added = on_files_added

        self.grid_columnconfigure(0, weight=1)

        self._drop_frame = ctk.CTkFrame(
            self,
            height=80,
            border_width=2,
            border_color=("gray60", "gray40"),
            fg_color=("gray90", "gray15"),
        )
        self._drop_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self._drop_frame.grid_propagate(False)
        self._drop_frame.grid_columnconfigure(0, weight=1)
        self._drop_frame.grid_rowconfigure((0, 1, 2), weight=1)

        self._drop_icon = ctk.CTkLabel(
            self._drop_frame,
            text="\U0001f4c1",
            font=ctk.CTkFont(size=24),
        )
        self._drop_icon.grid(row=0, column=0, pady=(8, 0))

        self._drop_text = ctk.CTkLabel(
            self._drop_frame,
            text=t("file.drop_here"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=13),
            text_color=("gray50", "gray60"),
        )
        self._drop_text.grid(row=1, column=0)

        self._browse_hint = ctk.CTkLabel(
            self._drop_frame,
            text=t("file.browse_hint"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
            text_color=("gray50", "gray60"),
        )
        self._browse_hint.grid(row=2, column=0, pady=(0, 6))

        self._drop_frame.bind("<Button-1>", lambda _e: self._browse_files())
        self._drop_icon.bind("<Button-1>", lambda _e: self._browse_files())
        self._drop_text.bind("<Button-1>", lambda _e: self._browse_files())
        self._browse_hint.bind("<Button-1>", lambda _e: self._browse_files())

        self._setup_dnd()

    def _setup_dnd(self):
        try:
            import windnd  # pyright: ignore[reportMissingModuleSource]

            windnd.hook_dropfiles(self._drop_frame, func=self._on_drop)
        except ImportError:
            pass

    def _on_drop(self, files):
        if self._on_files_added:
            paths = []
            for f in files:
                path = f.decode("utf-8") if isinstance(f, bytes) else str(f)
                if self._is_valid_file(path):
                    paths.append(path)
            if paths:
                self._on_files_added(paths)

    def _is_valid_file(self, path: str) -> bool:
        ext = Path(path).suffix.lower()
        if self._file_type == "video":
            return ext in VIDEO_EXTENSIONS
        elif self._file_type == "audio":
            return ext in AUDIO_EXTENSIONS
        return ext in VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

    def _browse_files(self):
        filetypes = self._get_filetypes()
        if self._multiple:
            files = filedialog.askopenfilenames(filetypes=filetypes)
        else:
            result = filedialog.askopenfilename(filetypes=filetypes)
            files = (result,) if result else ()

        if files and self._on_files_added:
            self._on_files_added(list(files))

    def _get_filetypes(self):
        if self._file_type == "video":
            return [
                (
                    t("nav.video"),
                    " ".join(f"*{e}" for e in sorted(VIDEO_EXTENSIONS)),
                ),
                (t("common.all_files"), "*.*"),
            ]
        elif self._file_type == "audio":
            return [
                (
                    t("nav.audio"),
                    " ".join(f"*{e}" for e in sorted(AUDIO_EXTENSIONS)),
                ),
                (t("common.all_files"), "*.*"),
            ]
        all_exts = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
        return [
            (
                t("common.media_files"),
                " ".join(f"*{e}" for e in sorted(all_exts)),
            ),
            (t("common.all_files"), "*.*"),
        ]

    def refresh_texts(self):
        self._drop_text.configure(text=t("file.drop_here"))
        self._browse_hint.configure(text=t("file.browse_hint"))
