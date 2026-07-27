#!/usr/bin/env python3
"""Minecraft Mod Doctor AI - Giriş noktası."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app import run

if __name__ == "__main__":
    run()
