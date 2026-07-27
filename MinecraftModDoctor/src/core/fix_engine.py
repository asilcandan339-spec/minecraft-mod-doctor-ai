"""Otomatik düzeltme motoru."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from src.config import DISABLED_MODS_FOLDER
from src.core.backup_manager import BackupManager
from src.core.dependency_resolver import DependencyResolver
from src.utils.minecraft_paths import MinecraftInstallation


class FixEngine:
    """Tespit edilen sorunları otomatik düzeltir."""

    def __init__(self, installation: MinecraftInstallation, scan_result: dict[str, Any] | None = None) -> None:
        self.installation = installation
        self.scan_result = scan_result or {}
        self.mods_dir = installation.mods_dir or installation.game_dir / "mods"
        self.disabled_dir = installation.game_dir / DISABLED_MODS_FOLDER
        self.backup = BackupManager()

    def apply_all_fixes(self) -> list[dict[str, Any]]:
        """Tüm güvenli düzeltmeleri uygular."""
        results = []

        # Önce yedek al
        backup_result = self.backup.create_backup(self.installation.game_dir, "Otomatik düzeltme öncesi")
        results.append({"action": "backup", **backup_result})

        results.append(self._move_incompatible_mods())
        results.append(self._move_corrupted_mods())
        results.append(self._move_duplicate_mods())
        results.append(self._download_missing_dependencies())

        return results

    def _ensure_disabled_dir(self) -> Path:
        self.disabled_dir.mkdir(parents=True, exist_ok=True)
        return self.disabled_dir

    def _move_incompatible_mods(self) -> dict[str, Any]:
        moved = []
        issues = self.scan_result.get("issues", [])
        mods = self.scan_result.get("mods", [])

        incompatible_pairs = []
        for issue in issues:
            if issue.get("category") == "compatibility" and issue.get("severity") == "critical":
                title = issue.get("title", "")
                # "Uyumsuz Mod Çifti: optifine + sodium" formatı
                parts = title.replace("Uyumsuz Mod Çifti:", "").strip().split("+")
                if len(parts) == 2:
                    incompatible_pairs.append((parts[0].strip(), parts[1].strip()))

        disabled = self._ensure_disabled_dir()
        for id_a, id_b in incompatible_pairs:
            # İkincil modu taşı (genelde optifine)
            target = id_a if "optifine" in id_a else id_b
            for mod in mods:
                mod_id = (mod.get("mod_id") or "").lower()
                file_name = mod.get("file_name", "").lower()
                if target in mod_id or target in file_name:
                    src = Path(mod.get("file_path", ""))
                    if src.exists():
                        dest = disabled / src.name
                        shutil.move(str(src), str(dest))
                        moved.append(src.name)

        return {
            "action": "move_incompatible",
            "success": True,
            "moved": moved,
            "message": f"{len(moved)} uyumsuz mod devre dışı bırakıldı." if moved else "Taşınacak uyumsuz mod yok.",
        }

    def _move_corrupted_mods(self) -> dict[str, Any]:
        moved = []
        mods = self.scan_result.get("mods", [])
        disabled = self._ensure_disabled_dir()

        for mod in mods:
            if mod.get("is_corrupted") or not mod.get("is_valid_jar"):
                src = Path(mod.get("file_path", ""))
                if src.exists():
                    dest = disabled / src.name
                    shutil.move(str(src), str(dest))
                    moved.append(src.name)

        return {
            "action": "move_corrupted",
            "success": True,
            "moved": moved,
            "message": f"{len(moved)} bozuk mod devre dışı bırakıldı." if moved else "Bozuk mod yok.",
        }

    def _move_duplicate_mods(self) -> dict[str, Any]:
        moved = []
        mods = self.scan_result.get("mods", [])
        seen: dict[str, dict] = {}
        disabled = self._ensure_disabled_dir()

        for mod in sorted(mods, key=lambda m: m.get("file_name", "")):
            key = (mod.get("mod_id") or mod.get("file_name", "")).lower()
            if key in seen:
                src = Path(mod.get("file_path", ""))
                if src.exists():
                    dest = disabled / src.name
                    shutil.move(str(src), str(dest))
                    moved.append(src.name)
            else:
                seen[key] = mod

        return {
            "action": "move_duplicates",
            "success": True,
            "moved": moved,
            "message": f"{len(moved)} yinelenen mod devre dışı bırakıldı." if moved else "Yinelenen mod yok.",
        }

    def _download_missing_dependencies(self) -> dict[str, Any]:
        deps = self.scan_result.get("dependencies", {}).get("missing", [])
        if not deps:
            return {"action": "download_deps", "success": True, "downloaded": [], "message": "Eksik bağımlılık yok."}

        resolver = DependencyResolver(self.installation)
        versions = self.scan_result.get("versions", {})
        mc_version = versions.get("minecraft_version", "")
        loader = versions.get("loader", "")

        downloaded = []
        for dep in deps:
            mod_id = dep.get("mod_id", "")
            if mod_id:
                result = resolver.download_dependency(mod_id, mc_version, loader)
                if result.get("success"):
                    downloaded.append(mod_id)

        return {
            "action": "download_deps",
            "success": bool(downloaded),
            "downloaded": downloaded,
            "message": f"{len(downloaded)} bağımlılık indirildi." if downloaded else "İndirilecek bağımlılık bulunamadı.",
        }

    def disable_mod(self, mod_path: Path) -> dict[str, Any]:
        """Tek bir modu devre dışı bırakır."""
        mod_path = Path(mod_path)
        if not mod_path.exists():
            return {"success": False, "message": "Mod dosyası bulunamadı."}

        disabled = self._ensure_disabled_dir()
        dest = disabled / mod_path.name
        shutil.move(str(mod_path), str(dest))
        return {"success": True, "message": f"{mod_path.name} devre dışı bırakıldı.", "path": str(dest)}
