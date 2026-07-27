"""Yedekleme yöneticisi."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from src.config import BACKUP_DIR
from src.database.db import Database


class BackupManager:
    """Mods ve yapılandırma yedekleme."""

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()

    def create_backup(self, game_dir: Path, note: str = "") -> dict:
        """Mods klasörünü yedekler."""
        game_dir = Path(game_dir)
        mods_dir = game_dir / "mods"
        config_dir = game_dir / "config"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = BACKUP_DIR / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        file_count = 0
        if mods_dir.exists():
            dest_mods = backup_path / "mods"
            shutil.copytree(mods_dir, dest_mods, dirs_exist_ok=True)
            file_count += sum(1 for _ in dest_mods.rglob("*") if _.is_file())

        if config_dir.exists():
            dest_config = backup_path / "config"
            shutil.copytree(config_dir, dest_config, dirs_exist_ok=True)
            file_count += sum(1 for _ in dest_config.rglob("*") if _.is_file())

        meta = {
            "date": timestamp,
            "source": str(game_dir),
            "file_count": file_count,
            "note": note,
        }
        (backup_path / "backup_meta.txt").write_text(
            f"Tarih: {timestamp}\nKaynak: {game_dir}\nDosya: {file_count}\nNot: {note}",
            encoding="utf-8",
        )

        self.db.save_backup_record(str(game_dir), str(backup_path), file_count, note)

        return {
            "success": True,
            "backup_path": str(backup_path),
            "file_count": file_count,
            "message": f"Yedek oluşturuldu: {backup_name} ({file_count} dosya)",
        }

    def restore_backup(self, backup_path: Path, game_dir: Path) -> dict:
        """Yedeği geri yükler."""
        backup_path = Path(backup_path)
        game_dir = Path(game_dir)

        if not backup_path.exists():
            return {"success": False, "message": "Yedek klasörü bulunamadı."}

        restored = 0
        mods_backup = backup_path / "mods"
        config_backup = backup_path / "config"

        # Geri yüklemeden önce mevcut durumu yedekle
        self.create_backup(game_dir, note="Geri yükleme öncesi otomatik yedek")

        if mods_backup.exists():
            dest = game_dir / "mods"
            dest.mkdir(parents=True, exist_ok=True)
            for item in mods_backup.iterdir():
                dest_item = dest / item.name
                if item.is_file():
                    shutil.copy2(item, dest_item)
                    restored += 1
                elif item.is_dir():
                    if dest_item.exists():
                        shutil.rmtree(dest_item)
                    shutil.copytree(item, dest_item)
                    restored += sum(1 for _ in dest_item.rglob("*") if _.is_file())

        if config_backup.exists():
            dest = game_dir / "config"
            dest.mkdir(parents=True, exist_ok=True)
            for item in config_backup.iterdir():
                dest_item = dest / item.name
                if item.is_file():
                    shutil.copy2(item, dest_item)
                    restored += 1

        return {
            "success": True,
            "restored_files": restored,
            "message": f"Yedek geri yüklendi: {restored} dosya",
        }

    def list_backups(self) -> list[dict]:
        """Mevcut yedekleri listeler."""
        backups = []
        if BACKUP_DIR.exists():
            for item in sorted(BACKUP_DIR.iterdir(), reverse=True):
                if item.is_dir() and item.name.startswith("backup_"):
                    meta_file = item / "backup_meta.txt"
                    note = ""
                    if meta_file.exists():
                        note = meta_file.read_text(encoding="utf-8")
                    file_count = sum(1 for _ in item.rglob("*") if _.is_file())
                    backups.append({
                        "name": item.name,
                        "path": str(item),
                        "file_count": file_count,
                        "meta": note,
                    })
        db_backups = self.db.get_backups()
        return backups if backups else [
            {"name": b.get("backup_path", "").split("\\")[-1], "path": b.get("backup_path", ""), "file_count": b.get("file_count", 0), "meta": b.get("note", "")}
            for b in db_backups
        ]
