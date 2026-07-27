"""AI sohbet paneli."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import END

from src.ai.assistant import AIAssistant
from src.config import COLORS
from src.ui.theme import Theme


class AIChatPanel(ctk.CTkToplevel):
    """AI asistan sohbet penceresi."""

    EXAMPLE_QUESTIONS = [
        "Bu mod neden çalışmıyor?",
        "FPS neden düşük?",
        "Bu crash neden oldu?",
        "Hangi modu kaldırmalıyım?",
    ]

    def __init__(self, master, assistant: AIAssistant, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.assistant = assistant
        self.title("AI Asistan - Mod Doctor")
        self.geometry("700x550")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(master)
        self._build()

    def _build(self) -> None:
        header = ctk.CTkLabel(
            self, text="🤖 AI Asistan", font=Theme.FONT_TITLE, text_color=COLORS["accent"],
        )
        header.pack(pady=15)

        self.chat_display = ctk.CTkTextbox(
            self, width=660, height=350, font=Theme.FONT,
            fg_color=COLORS["bg_medium"], text_color=COLORS["text"],
            corner_radius=12, wrap="word",
        )
        self.chat_display.pack(padx=20, pady=5)
        self.chat_display.configure(state="disabled")

        examples_frame = ctk.CTkFrame(self, fg_color="transparent")
        examples_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(examples_frame, text="Örnek sorular:", font=Theme.FONT_SMALL, text_color=COLORS["text_dim"]).pack(anchor="w")
        for q in self.EXAMPLE_QUESTIONS:
            btn = ctk.CTkButton(
                examples_frame, text=q, **Theme.secondary_button(), height=28,
                command=lambda question=q: self._set_question(question),
            )
            btn.pack(anchor="w", pady=2)

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=10)

        self.input_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Sorunuzu yazın...",
            font=Theme.FONT, height=40, corner_radius=12,
            fg_color=COLORS["bg_light"],
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self._send())

        send_btn = ctk.CTkButton(input_frame, text="Gönder", width=100, **Theme.accent_button(), command=self._send)
        send_btn.pack(side="right")

        welcome = self.assistant.ask("merhaba")
        self._append_message("Asistan", welcome)

    def _set_question(self, question: str) -> None:
        self.input_entry.delete(0, END)
        self.input_entry.insert(0, question)

    def _send(self) -> None:
        question = self.input_entry.get().strip()
        if not question:
            return
        self.input_entry.delete(0, END)
        self._append_message("Siz", question)

        self.chat_display.configure(state="normal")
        self.chat_display.insert(END, "\n⏳ Düşünüyor...\n")
        self.chat_display.configure(state="disabled")
        self.update()

        response = self.assistant.ask(question)

        self.chat_display.configure(state="normal")
        content = self.chat_display.get("1.0", END)
        if "⏳ Düşünüyor..." in content:
            self.chat_display.delete("end-2l", "end-1l")
        self.chat_display.configure(state="disabled")

        self._append_message("Asistan", response)

    def _append_message(self, sender: str, message: str) -> None:
        self.chat_display.configure(state="normal")
        prefix = "🟢" if sender == "Asistan" else "🔵"
        self.chat_display.insert(END, f"\n{prefix} {sender}:\n{message}\n")
        self.chat_display.see(END)
        self.chat_display.configure(state="disabled")
