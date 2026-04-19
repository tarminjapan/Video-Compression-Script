"""
Video compression view placeholder.
"""

import customtkinter as ctk

from ..i18n import t
from ..theme.fonts import DEFAULT_FONT_FAMILY


class VideoView(ctk.CTkFrame):
    """Placeholder view for video compression functionality."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            self,
            text=t("nav.video"),
            font=ctk.CTkFont(family=DEFAULT_FONT_FAMILY, size=18, weight="bold"),
        )
        label.grid(row=0, column=0)
