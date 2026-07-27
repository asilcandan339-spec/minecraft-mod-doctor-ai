"""Uygulama yapılandırması."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Minecraft Mod Doctor AI"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Mod Doctor Team"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "MinecraftModDoctor"
DB_PATH = DATA_DIR / "moddoctor.db"
BACKUP_DIR = DATA_DIR / "backups"
REPORTS_DIR = DATA_DIR / "reports"
CACHE_DIR = DATA_DIR / "cache"
DISABLED_MODS_FOLDER = "Disabled Mods"

DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Minecraft yeşil tema
COLORS = {
    "bg_dark": "#1a1a1a",
    "bg_medium": "#2d2d2d",
    "bg_light": "#3d3d3d",
    "accent": "#55aa33",
    "accent_hover": "#6bc94a",
    "accent_dark": "#3d7a24",
    "text": "#e0e0e0",
    "text_dim": "#a0a0a0",
    "danger": "#e74c3c",
    "warning": "#f39c12",
    "success": "#27ae60",
    "info": "#3498db",
}

FONT_FAMILY = "Segoe UI"
FONT_SIZE = 13
FONT_SIZE_SMALL = 11
FONT_SIZE_LARGE = 16
FONT_SIZE_TITLE = 22

# Bilinen uyumsuz mod çiftleri (mod_id_a, mod_id_b)
KNOWN_INCOMPATIBILITIES: list[tuple[str, str, str]] = [
    ("optifine", "sodium", "OptiFine ve Sodium aynı anda kullanılamaz."),
    ("optifine", "iris", "OptiFine ve Iris shader modu çakışır."),
    ("rubidium", "optifine", "Rubidium (Embeddium) OptiFine ile uyumsuzdur."),
    ("sodium", "rubidium", "Sodium ve Rubidium aynı render modudur, ikisini birden kullanmayın."),
]

# Resmi indirme kaynakları
MOD_SOURCES = {
    "modrinth": "https://api.modrinth.com/v2",
    "curseforge": "https://www.curseforge.com/minecraft/mc-mods",
}

# AI yapılandırması (isteğe bağlı harici API)
AI_API_URL = os.environ.get("MODDOCTOR_AI_URL", "")
AI_API_KEY = os.environ.get("MODDOCTOR_AI_KEY", "")
