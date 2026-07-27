"""SQLite veritabanı yönetimi."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import DB_PATH


class Database:
    """Mod Doctor SQLite veritabanı."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    installation_name TEXT NOT NULL,
                    game_dir TEXT NOT NULL,
                    scan_date TEXT NOT NULL,
                    health_compatibility REAL DEFAULT 0,
                    health_crash_risk REAL DEFAULT 0,
                    health_performance REAL DEFAULT 0,
                    summary_json TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS scan_mods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    mod_id TEXT,
                    display_name TEXT,
                    version TEXT,
                    loader TEXT,
                    file_name TEXT,
                    status TEXT DEFAULT 'ok',
                    issues_json TEXT DEFAULT '[]',
                    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS scan_issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    fix_steps_json TEXT DEFAULT '[]',
                    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_date TEXT NOT NULL,
                    source_dir TEXT NOT NULL,
                    backup_path TEXT NOT NULL,
                    file_count INTEGER DEFAULT 0,
                    note TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    messages_json TEXT DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)

    def save_scan(self, installation_name: str, game_dir: str, result: dict[str, Any]) -> int:
        """Tarama sonucunu kaydeder."""
        now = datetime.now(timezone.utc).isoformat()
        health = result.get("health", {})
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO scans
                   (installation_name, game_dir, scan_date,
                    health_compatibility, health_crash_risk, health_performance, summary_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    installation_name,
                    game_dir,
                    now,
                    health.get("compatibility", 0),
                    health.get("crash_risk", 0),
                    health.get("performance", 0),
                    json.dumps(result, ensure_ascii=False, default=str),
                ),
            )
            scan_id = cursor.lastrowid

            for mod in result.get("mods", []):
                conn.execute(
                    """INSERT INTO scan_mods
                       (scan_id, mod_id, display_name, version, loader, file_name, status, issues_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        scan_id,
                        mod.get("mod_id", ""),
                        mod.get("display_name", ""),
                        mod.get("version", ""),
                        mod.get("loader", ""),
                        mod.get("file_name", ""),
                        mod.get("status", "ok"),
                        json.dumps(mod.get("issues", []), ensure_ascii=False),
                    ),
                )

            for issue in result.get("issues", []):
                conn.execute(
                    """INSERT INTO scan_issues
                       (scan_id, severity, category, title, description, fix_steps_json)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        scan_id,
                        issue.get("severity", "info"),
                        issue.get("category", "general"),
                        issue.get("title", ""),
                        issue.get("description", ""),
                        json.dumps(issue.get("fix_steps", []), ensure_ascii=False),
                    ),
                )
            return scan_id

    def get_scans(self, limit: int = 20) -> list[dict]:
        """Son taramaları getirir."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY scan_date DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_scan(self, scan_id: int) -> dict | None:
        """Tek tarama detayını getirir."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["mods"] = [dict(r) for r in conn.execute(
                "SELECT * FROM scan_mods WHERE scan_id = ?", (scan_id,)
            ).fetchall()]
            result["issues"] = [dict(r) for r in conn.execute(
                "SELECT * FROM scan_issues WHERE scan_id = ?", (scan_id,)
            ).fetchall()]
            return result

    def save_backup_record(self, source_dir: str, backup_path: str, file_count: int, note: str = "") -> int:
        """Yedek kaydı oluşturur."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO backups (backup_date, source_dir, backup_path, file_count, note) VALUES (?, ?, ?, ?, ?)",
                (now, source_dir, backup_path, file_count, note),
            )
            return cursor.lastrowid

    def get_backups(self, limit: int = 20) -> list[dict]:
        """Yedek kayıtlarını getirir."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM backups ORDER BY backup_date DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
