"""Uygulama başlatıcı."""

from __future__ import annotations

import sys
from pathlib import Path

# Proje kökünü path'e ekle
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui.main_window import MainWindow


def run() -> None:
    """Uygulamayı başlatır."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run()
