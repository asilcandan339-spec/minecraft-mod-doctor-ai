"""UI tema sabitleri."""

from __future__ import annotations

import customtkinter as ctk

from src.config import COLORS, FONT_FAMILY, FONT_SIZE, FONT_SIZE_LARGE, FONT_SIZE_SMALL, FONT_SIZE_TITLE

# CustomTkinter varsayılan teması
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


def apply_theme(root: ctk.CTk) -> None:
    """Ana pencere temasını uygular."""
    root.configure(fg_color=COLORS["bg_dark"])


class Theme:
    """Tema yardımcı sınıfı."""

    COLORS = COLORS
    FONT = (FONT_FAMILY, FONT_SIZE)
    FONT_SMALL = (FONT_FAMILY, FONT_SIZE_SMALL)
    FONT_LARGE = (FONT_FAMILY, FONT_SIZE_LARGE)
    FONT_TITLE = (FONT_FAMILY, FONT_SIZE_TITLE, "bold")

    @staticmethod
    def accent_button(**kwargs) -> dict:
        return {
            "fg_color": COLORS["accent"],
            "hover_color": COLORS["accent_hover"],
            "text_color": "#ffffff",
            "corner_radius": 12,
            "height": 42,
            "font": (FONT_FAMILY, FONT_SIZE, "bold"),
            **kwargs,
        }

    @staticmethod
    def secondary_button(**kwargs) -> dict:
        return {
            "fg_color": COLORS["bg_light"],
            "hover_color": COLORS["bg_medium"],
            "text_color": COLORS["text"],
            "corner_radius": 12,
            "height": 38,
            "font": (FONT_FAMILY, FONT_SIZE),
            **kwargs,
        }

    @staticmethod
    def card_frame(parent, **kwargs) -> ctk.CTkFrame:
        return ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_medium"],
            corner_radius=16,
            **kwargs,
        )
