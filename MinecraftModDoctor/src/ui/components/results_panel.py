"""Sonuçlar paneli."""

from __future__ import annotations

import customtkinter as ctk
import webbrowser

from src.config import COLORS
from src.ui.theme import Theme


class ResultsPanel(ctk.CTkScrollableFrame):
    """Tarama sonuçlarını gösterir."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._placeholder = ctk.CTkLabel(
            self, text="Henüz tarama yapılmadı.\n'Minecraft'ı Tara' butonuna tıklayın.",
            font=Theme.FONT_LARGE, text_color=COLORS["text_dim"],
        )
        self._placeholder.pack(expand=True, pady=50)

    def show_results(self, scan_result: dict) -> None:
        """Sonuçları gösterir."""
        for widget in self.winfo_children():
            widget.destroy()

        # Özet
        mod_count = scan_result.get("mod_count", len(scan_result.get("mods", [])))
        issue_count = len(scan_result.get("issues", []))
        summary = Theme.card_frame(self)
        summary.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(summary, text="📊 Tarama Özeti", font=Theme.FONT_LARGE, text_color=COLORS["accent"]).pack(anchor="w", padx=15, pady=(10, 5))
        ctk.CTkLabel(summary, text=f"Mod sayısı: {mod_count}  |  Sorun: {issue_count}", font=Theme.FONT).pack(anchor="w", padx=15, pady=(0, 10))

        # Sorunlar
        issues = scan_result.get("issues", [])
        if issues:
            self._section("⚠️ Sorunlar", issues, self._render_issue)

        # Uyarılar / log hataları
        logs = scan_result.get("logs", {})
        explained = logs.get("explained_errors", [])
        if explained:
            self._section("📋 Log Analizi", explained, self._render_log_error)

        # Sorunlu modlar
        problematic = scan_result.get("problematic_mods", [])
        if problematic:
            self._section("🔴 Sorunlu Modlar", problematic, self._render_mod)

        # Sağlıklı modlar
        healthy = scan_result.get("healthy_mods", [])
        if healthy:
            self._section("✅ Sağlıklı Modlar", healthy[:20], self._render_mod, collapsed=len(healthy) > 10)

        # Eksik bağımlılıklar
        deps = scan_result.get("dependencies", {}).get("missing", [])
        if deps:
            self._section("📦 Eksik Bağımlılıklar", deps, self._render_dependency)

        # Performans
        perf = scan_result.get("performance", {})
        if perf:
            self._render_performance(perf)

    def _section(self, title: str, items: list, render_func, collapsed: bool = False) -> None:
        frame = Theme.card_frame(self)
        frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(frame, text=f"{title} ({len(items)})", font=Theme.FONT_LARGE, text_color=COLORS["accent"]).pack(anchor="w", padx=15, pady=(10, 5))
        display_items = items[:10] if collapsed else items[:20]
        for item in display_items:
            render_func(frame, item)
        if len(items) > len(display_items):
            ctk.CTkLabel(frame, text=f"... ve {len(items) - len(display_items)} daha", font=Theme.FONT_SMALL, text_color=COLORS["text_dim"]).pack(anchor="w", padx=15, pady=5)
        ctk.CTkLabel(frame, text="").pack(pady=5)

    def _render_issue(self, parent, issue: dict) -> None:
        sev = issue.get("severity", "info")
        color = COLORS["danger"] if sev == "critical" else COLORS["warning"] if sev == "warning" else COLORS["text"]
        item_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_light"], corner_radius=8)
        item_frame.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(item_frame, text=issue.get("title", ""), font=(Theme.FONT[0], Theme.FONT[1], "bold"), text_color=color, wraplength=500, justify="left").pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(item_frame, text=issue.get("description", ""), font=Theme.FONT_SMALL, wraplength=500, justify="left").pack(anchor="w", padx=10, pady=(0, 5))
        for step in issue.get("fix_steps", [])[:2]:
            ctk.CTkLabel(item_frame, text=f"→ {step}", font=Theme.FONT_SMALL, text_color=COLORS["accent"], wraplength=480, justify="left").pack(anchor="w", padx=20, pady=1)
        ctk.CTkLabel(item_frame, text="").pack(pady=3)

    def _render_log_error(self, parent, err: dict) -> None:
        self._render_issue(parent, {
            "severity": err.get("severity", "error"),
            "title": err.get("title", ""),
            "description": err.get("explanation", ""),
            "fix_steps": err.get("fix_steps", []),
        })

    def _render_mod(self, parent, mod: dict) -> None:
        item_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_light"], corner_radius=8)
        item_frame.pack(fill="x", padx=15, pady=3)
        name = mod.get("display_name", mod.get("file_name", ""))
        status = "✅" if mod.get("status") == "ok" else "❌"
        ctk.CTkLabel(item_frame, text=f"{status} {name} v{mod.get('version', '?')} [{mod.get('loader_label', '')}]", font=Theme.FONT, wraplength=500, justify="left").pack(anchor="w", padx=10, pady=5)
        for issue in mod.get("issues", [])[:2]:
            ctk.CTkLabel(item_frame, text=f"  • {issue}", font=Theme.FONT_SMALL, text_color=COLORS["warning"], wraplength=480, justify="left").pack(anchor="w", padx=15)

    def _render_dependency(self, parent, dep: dict) -> None:
        item_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_light"], corner_radius=8)
        item_frame.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(item_frame, text=dep.get("title", dep.get("mod_id", "")), font=Theme.FONT, wraplength=500, justify="left").pack(anchor="w", padx=10, pady=5)
        dl = dep.get("download")
        if dl and dl.get("url"):
            btn = ctk.CTkButton(
                item_frame, text="🔗 İndir", width=100, height=28,
                **Theme.accent_button(), command=lambda u=dl["url"]: webbrowser.open(u),
            )
            btn.pack(anchor="w", padx=10, pady=(0, 8))

    def _render_performance(self, perf: dict) -> None:
        frame = Theme.card_frame(self)
        frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(frame, text="⚡ Performans", font=Theme.FONT_LARGE, text_color=COLORS["accent"]).pack(anchor="w", padx=15, pady=(10, 5))
        ctk.CTkLabel(frame, text=f"Tahmini FPS: ~{perf.get('estimated_fps', '?')}", font=Theme.FONT).pack(anchor="w", padx=15)
        ctk.CTkLabel(frame, text=f"Tahmini RAM: {perf.get('estimated_total_ram_mb', '?')} MB", font=Theme.FONT).pack(anchor="w", padx=15)
        ctk.CTkLabel(frame, text=f"CPU: %{perf.get('cpu', {}).get('percent', '?')}  |  Kullanılabilir RAM: {perf.get('ram', {}).get('available_mb', '?')} MB", font=Theme.FONT).pack(anchor="w", padx=15, pady=(0, 5))
        for rec in perf.get("recommendations", [])[:3]:
            ctk.CTkLabel(frame, text=f"• {rec}", font=Theme.FONT_SMALL, wraplength=500, justify="left").pack(anchor="w", padx=20, pady=1)
        ctk.CTkLabel(frame, text="").pack(pady=5)

    def clear(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()
        self._placeholder = ctk.CTkLabel(
            self, text="Henüz tarama yapılmadı.\n'Minecraft'ı Tara' butonuna tıklayın.",
            font=Theme.FONT_LARGE, text_color=COLORS["text_dim"],
        )
        self._placeholder.pack(expand=True, pady=50)
