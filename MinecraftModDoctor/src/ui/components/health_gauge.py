"""Sağlık skoru göstergesi."""

from __future__ import annotations

import customtkinter as ctk

from src.config import COLORS
from src.ui.theme import Theme


class HealthGauge(ctk.CTkFrame):
    """Uyumluluk, çökme riski ve performans göstergesi."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self) -> None:
        self.title = ctk.CTkLabel(self, text="Sağlık Skoru", font=Theme.FONT_TITLE, text_color=COLORS["accent"])
        self.title.pack(pady=(0, 10))

        self.overall_label = ctk.CTkLabel(self, text="—", font=("Segoe UI", 36, "bold"), text_color=COLORS["text"])
        self.overall_label.pack()

        self.grade_label = ctk.CTkLabel(self, text="Tarama bekleniyor", font=Theme.FONT, text_color=COLORS["text_dim"])
        self.grade_label.pack(pady=(0, 15))

        metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=10)

        self.compatibility_bar = self._create_metric(metrics_frame, "Uyumluluk", 0)
        self.crash_bar = self._create_metric(metrics_frame, "Çökme Riski", 1)
        self.performance_bar = self._create_metric(metrics_frame, "Performans", 2)

    def _create_metric(self, parent, label: str, row: int) -> ctk.CTkProgressBar:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=4)

        lbl = ctk.CTkLabel(frame, text=label, font=Theme.FONT_SMALL, width=120, anchor="w")
        lbl.pack(side="left")

        bar = ctk.CTkProgressBar(frame, width=200, height=14, corner_radius=7,
                                  progress_color=COLORS["accent"], fg_color=COLORS["bg_light"])
        bar.pack(side="left", padx=10)
        bar.set(0)

        value_lbl = ctk.CTkLabel(frame, text="—%", font=Theme.FONT_SMALL, width=40)
        value_lbl.pack(side="left")
        bar.value_label = value_lbl  # type: ignore
        return bar

    def update_scores(self, health: dict) -> None:
        """Skorları günceller."""
        overall = health.get("overall", 0)
        self.overall_label.configure(text=f"{overall:.0f}%")
        self.grade_label.configure(text=f"{health.get('grade_label', '')} ({health.get('grade', '')})")

        self.compatibility_bar.set(health.get("compatibility", 0) / 100)
        self.compatibility_bar.value_label.configure(text=f"{health.get('compatibility', 0):.0f}%")  # type: ignore

        crash = health.get("crash_risk", 0)
        self.crash_bar.set(crash / 100)
        self.crash_bar.configure(progress_color=COLORS["danger"] if crash > 50 else COLORS["warning"])
        self.crash_bar.value_label.configure(text=f"{crash:.0f}%")  # type: ignore

        self.performance_bar.set(health.get("performance", 0) / 100)
        self.performance_bar.value_label.configure(text=f"{health.get('performance', 0):.0f}%")  # type: ignore

    def reset(self) -> None:
        self.overall_label.configure(text="—")
        self.grade_label.configure(text="Tarama bekleniyor")
        for bar in (self.compatibility_bar, self.crash_bar, self.performance_bar):
            bar.set(0)
            bar.value_label.configure(text="—%")  # type: ignore
