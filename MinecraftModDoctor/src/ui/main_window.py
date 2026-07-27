"""Ana uygulama penceresi."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.ai.assistant import AIAssistant
from src.config import APP_NAME, APP_VERSION, COLORS
from src.core.backup_manager import BackupManager
from src.core.fix_engine import FixEngine
from src.core.installation_scanner import InstallationScanner
from src.database.db import Database
from src.reports.pdf_generator import PDFReportGenerator
from src.ui.components.ai_chat import AIChatPanel
from src.ui.components.health_gauge import HealthGauge
from src.ui.components.results_panel import ResultsPanel
from src.ui.theme import Theme, apply_theme
from src.utils.minecraft_paths import MinecraftInstallation, detect_all_installations


class MainWindow(ctk.CTk):
    """Minecraft Mod Doctor AI ana penceresi."""

    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1200x800")
        self.minsize(900, 650)
        apply_theme(self)

        self.db = Database()
        self.backup_manager = BackupManager(self.db)
        self.assistant = AIAssistant()
        self.scan_result: dict | None = None
        self.current_installation: MinecraftInstallation | None = None
        self.installations: list[MinecraftInstallation] = []
        self._scanning = False

        self._build_ui()
        self._detect_installations()

    def _build_ui(self) -> None:
        # Üst başlık
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=70, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(title_frame, text="⛏️ Minecraft Mod Doctor AI", font=Theme.FONT_TITLE, text_color=COLORS["accent"]).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Mod Analiz ve Onarım Aracı", font=Theme.FONT_SMALL, text_color=COLORS["text_dim"]).pack(anchor="w")

        # Kurulum seçici
        select_frame = ctk.CTkFrame(header, fg_color="transparent")
        select_frame.pack(side="right", padx=20, pady=15)
        ctk.CTkLabel(select_frame, text="Kurulum:", font=Theme.FONT_SMALL).pack(side="left", padx=(0, 5))
        self.installation_var = ctk.StringVar(value="Tespit ediliyor...")
        self.installation_menu = ctk.CTkOptionMenu(
            select_frame, variable=self.installation_var, values=["Tespit ediliyor..."],
            width=280, font=Theme.FONT_SMALL, fg_color=COLORS["bg_light"],
            button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
            command=self._on_installation_change,
        )
        self.installation_menu.pack(side="left")

        # Ana içerik
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=10)

        # Sol panel - butonlar ve sağlık
        left_panel = ctk.CTkFrame(content, fg_color=COLORS["bg_medium"], width=320, corner_radius=16)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        ctk.CTkLabel(left_panel, text="İşlemler", font=Theme.FONT_LARGE, text_color=COLORS["accent"]).pack(pady=(20, 15))

        buttons = [
            ("🔍 Minecraft'ı Tara", self._start_scan, Theme.accent_button()),
            ("💾 Analizi Kaydet", self._save_analysis, Theme.secondary_button()),
            ("📄 PDF Raporu Oluştur", self._generate_pdf, Theme.secondary_button()),
            ("↩️ Yedekten Geri Yükle", self._restore_backup, Theme.secondary_button()),
            ("🤖 AI'ye Sor", self._open_ai_chat, Theme.accent_button()),
            ("🔧 Otomatik Düzelt", self._auto_fix, Theme.secondary_button()),
            ("🔄 Kurulumları Yenile", self._detect_installations, Theme.secondary_button()),
        ]

        for text, command, style in buttons:
            btn = ctk.CTkButton(left_panel, text=text, command=command, **style)
            btn.pack(fill="x", padx=20, pady=6)

        # İlerleme çubuğu
        self.progress_label = ctk.CTkLabel(left_panel, text="", font=Theme.FONT_SMALL, text_color=COLORS["text_dim"])
        self.progress_label.pack(pady=(15, 5))
        self.progress_bar = ctk.CTkProgressBar(left_panel, width=260, progress_color=COLORS["accent"])
        self.progress_bar.pack(padx=20)
        self.progress_bar.set(0)

        # Sağlık göstergesi
        self.health_gauge = HealthGauge(left_panel)
        self.health_gauge.pack(pady=20, padx=10, fill="x")

        # Sağ panel - sonuçlar
        right_panel = ctk.CTkFrame(content, fg_color=COLORS["bg_medium"], corner_radius=16)
        right_panel.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_panel, text="Analiz Sonuçları", font=Theme.FONT_LARGE, text_color=COLORS["accent"]).pack(anchor="w", padx=20, pady=(15, 5))

        self.results_panel = ResultsPanel(right_panel)
        self.results_panel.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Alt durum çubuğu
        status_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=30, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        self.status_label = ctk.CTkLabel(status_bar, text="Hazır", font=Theme.FONT_SMALL, text_color=COLORS["text_dim"])
        self.status_label.pack(side="left", padx=15, pady=5)

    def _detect_installations(self) -> None:
        self._set_status("Minecraft kurulumları aranıyor...")
        self.installations = detect_all_installations(include_custom_scan=False)
        if not self.installations:
            self.installations = detect_all_installations(include_custom_scan=True)

        names = [inst.name for inst in self.installations] if self.installations else ["Kurulum bulunamadı"]
        self.installation_menu.configure(values=names)
        if self.installations:
            self.installation_var.set(self.installations[0].name)
            self.current_installation = self.installations[0]
            self._set_status(f"{len(self.installations)} kurulum bulundu.")
        else:
            self._set_status("Minecraft kurulumu bulunamadı.")

    def _on_installation_change(self, choice: str) -> None:
        for inst in self.installations:
            if inst.name == choice:
                self.current_installation = inst
                break

    def _start_scan(self) -> None:
        if self._scanning:
            return
        if not self.current_installation:
            messagebox.showwarning("Uyarı", "Lütfen bir Minecraft kurulumu seçin.")
            return

        self._scanning = True
        self._set_status("Tarama başlatılıyor...")
        self.progress_bar.set(0)

        def scan_thread():
            try:
                scanner = InstallationScanner(self.current_installation)

                def progress(pct, msg):
                    self.after(0, lambda: self._update_progress(pct, msg))

                result = scanner.scan(progress_callback=progress)
                self.after(0, lambda: self._on_scan_complete(result))
            except Exception as e:
                self.after(0, lambda: self._on_scan_error(str(e)))

        threading.Thread(target=scan_thread, daemon=True).start()

    def _update_progress(self, pct: float, msg: str) -> None:
        self.progress_bar.set(pct)
        self.progress_label.configure(text=msg)
        self._set_status(msg)

    def _on_scan_complete(self, result: dict) -> None:
        self._scanning = False
        self.scan_result = result
        self.assistant.set_context(result)
        self.results_panel.show_results(result)
        health = result.get("health", {})
        self.health_gauge.update_scores(health)
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Tarama tamamlandı!")
        mod_count = result.get("mod_count", 0)
        issue_count = len(result.get("issues", []))
        self._set_status(f"Tarama tamamlandı: {mod_count} mod, {issue_count} sorun.")

    def _on_scan_error(self, error: str) -> None:
        self._scanning = False
        self.progress_bar.set(0)
        self._set_status(f"Hata: {error}")
        messagebox.showerror("Tarama Hatası", f"Tarama sırasında hata oluştu:\n{error}")

    def _save_analysis(self) -> None:
        if not self.scan_result or not self.current_installation:
            messagebox.showinfo("Bilgi", "Önce bir tarama yapın.")
            return
        scan_id = self.db.save_scan(
            self.current_installation.name,
            str(self.current_installation.game_dir),
            self.scan_result,
        )
        messagebox.showinfo("Kaydedildi", f"Analiz veritabanına kaydedildi (ID: {scan_id}).")

    def _generate_pdf(self) -> None:
        if not self.scan_result:
            messagebox.showinfo("Bilgi", "Önce bir tarama yapın.")
            return
        try:
            generator = PDFReportGenerator()
            path = generator.generate(self.scan_result)
            self._set_status(f"PDF oluşturuldu: {path}")
            if messagebox.askyesno("PDF Oluşturuldu", f"Rapor kaydedildi:\n{path}\n\nAçmak ister misiniz?"):
                import os
                os.startfile(str(path))
        except Exception as e:
            messagebox.showerror("PDF Hatası", f"PDF oluşturulamadı:\n{e}")

    def _restore_backup(self) -> None:
        if not self.current_installation:
            messagebox.showwarning("Uyarı", "Kurulum seçilmedi.")
            return

        backups = self.backup_manager.list_backups()
        if not backups:
            messagebox.showinfo("Bilgi", "Henüz yedek bulunmuyor.")
            return

        backup_dir = filedialog.askdirectory(
            title="Geri yüklenecek yedeği seçin",
            initialdir=str(Path(backups[0]["path"]).parent) if backups else "",
        )
        if not backup_dir:
            return

        if not messagebox.askyesno("Onay", "Yedek geri yüklenecek. Devam edilsin mi?"):
            return

        result = self.backup_manager.restore_backup(Path(backup_dir), self.current_installation.game_dir)
        if result.get("success"):
            messagebox.showinfo("Başarılı", result.get("message", "Geri yükleme tamamlandı."))
        else:
            messagebox.showerror("Hata", result.get("message", "Geri yükleme başarısız."))

    def _open_ai_chat(self) -> None:
        if self.scan_result:
            self.assistant.set_context(self.scan_result)
        AIChatPanel(self, self.assistant)

    def _auto_fix(self) -> None:
        if not self.scan_result or not self.current_installation:
            messagebox.showinfo("Bilgi", "Önce bir tarama yapın.")
            return

        if not messagebox.askyesno(
            "Otomatik Düzeltme",
            "Bu işlem:\n• Yedek alacak\n• Uyumsuz/bozuk modları devre dışı bırakacak\n• Eksik bağımlılıkları indirmeye çalışacak\n\nDevam edilsin mi?",
        ):
            return

        self._set_status("Otomatik düzeltme uygulanıyor...")
        fix_engine = FixEngine(self.current_installation, self.scan_result)
        results = fix_engine.apply_all_fixes()

        messages = []
        for r in results:
            messages.append(f"• {r.get('action', '')}: {r.get('message', '')}")

        messagebox.showinfo("Düzeltme Tamamlandı", "\n".join(messages))
        self._set_status("Otomatik düzeltme tamamlandı. Yeniden tarama önerilir.")
        self._start_scan()

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)
