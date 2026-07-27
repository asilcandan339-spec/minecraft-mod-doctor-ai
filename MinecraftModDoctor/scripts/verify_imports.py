"""Modul import dogrulama scripti."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODULES = [
    "src.config",
    "src.utils.minecraft_paths",
    "src.utils.jar_reader",
    "src.utils.turkish_messages",
    "src.database.db",
    "src.core.mod_analyzer",
    "src.core.log_analyzer",
    "src.core.installation_scanner",
    "src.core.dependency_resolver",
    "src.core.performance_analyzer",
    "src.core.health_score",
    "src.core.backup_manager",
    "src.core.fix_engine",
    "src.ai.assistant",
    "src.reports.pdf_generator",
    "src.ui.theme",
    "src.ui.main_window",
]


def main() -> int:
    failed = []
    for mod in MODULES:
        try:
            __import__(mod)
            print(f"OK  {mod}")
        except Exception as e:
            print(f"FAIL {mod}: {e}")
            failed.append(mod)
    if failed:
        print(f"\n{len(failed)} modul basarisiz.")
        return 1
    print(f"\nTum {len(MODULES)} modul basariyla yuklendi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
