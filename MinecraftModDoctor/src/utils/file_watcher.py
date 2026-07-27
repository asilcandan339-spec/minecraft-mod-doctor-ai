"""Watchdog dosya izleme - mods klasörü değişikliklerini izler."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ModsFolderWatcher:
    """Mods klasöründeki değişiklikleri izler."""

    def __init__(self, mods_dir: Path, on_change: Callable[[], None]) -> None:
        self.mods_dir = Path(mods_dir)
        self.on_change = on_change
        self._observer: Observer | None = None

    def start(self) -> None:
        if not self.mods_dir.exists():
            return

        handler = _ChangeHandler(self.on_change)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.mods_dir), recursive=False)
        self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None


class _ChangeHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback

    def on_any_event(self, event) -> None:
        if not event.is_directory and event.src_path.endswith(".jar"):
            self.callback()
