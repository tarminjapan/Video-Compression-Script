"""
File list display component for AmeCompression GUI.

Shows selected files with name, size, format icon, and remove buttons.
"""

from pathlib import Path

import customtkinter as ctk

from ...config import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS
from ..i18n import t
from ..theme.fonts import DEFAULT_FONT_FAMILY


class FileListFrame(ctk.CTkFrame):
    """Scrollable file list with remove buttons and file count."""

    def __init__(self, master, on_change=None, **kwargs):
        super().__init__(master, **kwargs)
        self._files: list[dict] = []
        self._on_change = on_change

        self.grid_columnconfigure(0, weight=1)

        self._header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._header_frame.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="ew")
        self._header_frame.grid_columnconfigure(1, weight=1)

        self._count_label = ctk.CTkLabel(
            self._header_frame,
            text=t("file.no_files"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
        )
        self._count_label.grid(row=0, column=0, sticky="w")

        self._clear_btn = ctk.CTkButton(
            self._header_frame,
            text=t("file.clear_all"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            width=80,
            height=28,
            command=self.clear_all,
        )
        self._clear_btn.grid(row=0, column=1, sticky="e")

        self._scroll_frame = ctk.CTkScrollableFrame(self, height=120)
        self._scroll_frame.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="ew")
        self._scroll_frame.grid_columnconfigure(0, weight=1)

    def add_files(self, paths: list[str]):
        for path in paths:
            p = Path(path)
            if not p.exists():
                continue
            resolved = str(p.resolve())
            if any(f["path"] == resolved for f in self._files):
                continue
            ext = p.suffix.lower()
            if ext in VIDEO_EXTENSIONS:
                file_type = "video"
            elif ext in AUDIO_EXTENSIONS:
                file_type = "audio"
            else:
                file_type = "unknown"
            self._files.append(
                {
                    "path": resolved,
                    "name": p.name,
                    "size": p.stat().st_size,
                    "format": ext.upper().lstrip("."),
                    "type": file_type,
                }
            )
        self._refresh_list()
        if self._on_change:
            self._on_change()

    def move_file_up(self, index: int):
        if index > 0:
            self._files[index - 1], self._files[index] = (
                self._files[index],
                self._files[index - 1],
            )
            self._refresh_list()
            if self._on_change:
                self._on_change()

    def move_file_down(self, index: int):
        if index < len(self._files) - 1:
            self._files[index + 1], self._files[index] = (
                self._files[index],
                self._files[index + 1],
            )
            self._refresh_list()
            if self._on_change:
                self._on_change()

    def remove_file(self, index: int):
        if 0 <= index < len(self._files):
            self._files.pop(index)
            self._refresh_list()
            if self._on_change:
                self._on_change()

    def clear_all(self):
        self._files.clear()
        self._refresh_list()
        if self._on_change:
            self._on_change()

    def get_files(self) -> list[dict]:
        return list(self._files)

    def get_file_paths(self) -> list[str]:
        return [f["path"] for f in self._files]

    def _refresh_list(self):
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

        if not self._files:
            self._count_label.configure(text=t("file.no_files"))
            return

        self._count_label.configure(text=t("file.selected_count", count=len(self._files)))

        for i, file_info in enumerate(self._files):
            row = ctk.CTkFrame(self._scroll_frame, fg_color="transparent", height=32)
            row.grid(row=i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)

            icon = "\U0001f3ac" if file_info["type"] == "video" else "\U0001f3b5"
            ctk.CTkLabel(
                row,
                text=icon,
                width=24,
                font=ctk.CTkFont(size=14),
            ).grid(row=0, column=0, padx=(4, 2))

            name_text = file_info["name"]
            if len(name_text) > 30:
                name_text = name_text[:27] + "..."
            ctk.CTkLabel(
                row,
                text=name_text,
                anchor="w",
                font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=12),
            ).grid(row=0, column=1, sticky="w", padx=4)

            size_str = self._format_size(file_info["size"])
            ctk.CTkLabel(
                row,
                text=f"{file_info['format']} | {size_str}",
                width=110,
                font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=11),
                text_color=("gray40", "gray60"),
            ).grid(row=0, column=2, padx=4)

            reorder_frame = ctk.CTkFrame(row, fg_color="transparent", width=52)
            reorder_frame.grid(row=0, column=3, padx=(2, 2))
            reorder_frame.grid_propagate(False)

            ctk.CTkButton(
                reorder_frame,
                text="\u25b2",
                width=22,
                height=14,
                font=ctk.CTkFont(size=8),
                fg_color="transparent",
                text_color=("gray40", "gray60"),
                hover_color=("gray75", "gray30"),
                command=lambda idx=i: self.move_file_up(idx),
            ).grid(row=0, column=0, padx=0, pady=(2, 0))

            ctk.CTkButton(
                reorder_frame,
                text="\u25bc",
                width=22,
                height=14,
                font=ctk.CTkFont(size=8),
                fg_color="transparent",
                text_color=("gray40", "gray60"),
                hover_color=("gray75", "gray30"),
                command=lambda idx=i: self.move_file_down(idx),
            ).grid(row=1, column=0, padx=0, pady=(0, 2))

            ctk.CTkButton(
                row,
                text="\u2715",
                width=28,
                height=24,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                text_color=("gray40", "gray60"),
                hover_color=("gray75", "gray30"),
                command=lambda idx=i: self.remove_file(idx),
            ).grid(row=0, column=4, padx=(4, 4))

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def refresh_texts(self):
        if self._files:
            self._count_label.configure(text=t("file.selected_count", count=len(self._files)))
        else:
            self._count_label.configure(text=t("file.no_files"))
        self._clear_btn.configure(text=t("file.clear_all"))
        self._refresh_list()
