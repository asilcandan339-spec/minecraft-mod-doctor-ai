"""Mod analiz motoru."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.config import KNOWN_INCOMPATIBILITIES
from src.utils.jar_reader import ModMetadata, compute_sha256, read_jar_metadata
from src.utils.minecraft_paths import MinecraftInstallation
from src.utils.turkish_messages import LOADER_LABELS


class ModAnalyzer:
    """Mod klasörünü analiz eder."""

    def __init__(self, installation: MinecraftInstallation) -> None:
        self.installation = installation
        self.mods_dir = installation.mods_dir or installation.game_dir / "mods"
        self.mods: list[ModMetadata] = []
        self.issues: list[dict[str, Any]] = []

    def analyze(self) -> dict[str, Any]:
        """Tüm modları analiz eder."""
        self.mods = []
        self.issues = []

        if not self.mods_dir or not self.mods_dir.exists():
            self.issues.append({
                "severity": "warning",
                "category": "mods",
                "title": "Mods Klasörü Bulunamadı",
                "description": f"Mods klasörü mevcut değil: {self.mods_dir}",
                "fix_steps": ["Minecraft'ı en az bir kez başlatın veya mods klasörünü oluşturun."],
            })
            return self._build_result()

        jar_files = list(self.mods_dir.glob("*.jar")) + list(self.mods_dir.glob("*.JAR"))
        disabled_dir = self.mods_dir.parent / "Disabled Mods"
        if disabled_dir.exists():
            pass  # devre dışı modları sayma

        for jar_path in jar_files:
            meta = read_jar_metadata(jar_path)
            meta.sha256 = compute_sha256(jar_path)
            self._validate_mod(meta)
            self.mods.append(meta)

        self._detect_duplicates()
        self._detect_incompatibilities()
        self._check_dependencies()
        self._detect_loader_conflicts()

        return self._build_result()

    def _validate_mod(self, meta: ModMetadata) -> None:
        if meta.is_corrupted:
            meta.issues.append("JAR dosyası bozuk veya hasarlı.")
            self.issues.append({
                "severity": "critical",
                "category": "mods",
                "title": f"Bozuk Mod: {meta.file_name}",
                "description": f"{meta.file_name} dosyası bozuk. Oyun çökmesine neden olabilir.",
                "fix_steps": [
                    "Modu resmi kaynaktan yeniden indirin.",
                    "Bozuk dosyayı 'Disabled Mods' klasörüne taşıyın.",
                ],
            })
        if not meta.is_valid_jar:
            self.issues.append({
                "severity": "error",
                "category": "mods",
                "title": f"Geçersiz Mod: {meta.file_name}",
                "description": f"{meta.file_name} geçerli bir mod dosyası değil.",
                "fix_steps": ["Dosyayı mods klasöründen kaldırın veya yeniden indirin."],
            })
        if meta.file_size < 1024:
            meta.issues.append("Dosya çok küçük, muhtemelen bozuk.")
        if not meta.loader:
            meta.loader = "unknown"
            meta.issues.append("Mod loader tespit edilemedi (Fabric/Forge/NeoForge).")

    def _detect_duplicates(self) -> None:
        by_id: dict[str, list[ModMetadata]] = defaultdict(list)
        by_hash: dict[str, list[ModMetadata]] = defaultdict(list)

        for mod in self.mods:
            key = mod.mod_id.lower() if mod.mod_id else mod.file_name.lower()
            by_id[key].append(mod)
            if mod.sha256:
                by_hash[mod.sha256].append(mod)

        for mod_id, group in by_id.items():
            if len(group) > 1:
                names = ", ".join(m.file_name for m in group)
                for m in group:
                    m.issues.append(f"Yinelenen mod: {mod_id}")
                self.issues.append({
                    "severity": "warning",
                    "category": "mods",
                    "title": f"Yinelenen Mod: {mod_id}",
                    "description": f"Aynı modun birden fazla kopyası var: {names}",
                    "fix_steps": [
                        "En güncel sürümü bırakın, diğerlerini 'Disabled Mods' klasörüne taşıyın.",
                    ],
                })

        for h, group in by_hash.items():
            if len(group) > 1 and group[0].mod_id != group[1].mod_id:
                pass  # farklı modlar aynı hash olamaz genelde

    def _detect_incompatibilities(self) -> None:
        mod_ids = {m.mod_id.lower() for m in self.mods if m.mod_id}
        file_names = {m.file_name.lower() for m in self.mods}

        for id_a, id_b, reason in KNOWN_INCOMPATIBILITIES:
            found_a = id_a in mod_ids or any(id_a in fn for fn in file_names)
            found_b = id_b in mod_ids or any(id_b in fn for fn in file_names)
            if found_a and found_b:
                self.issues.append({
                    "severity": "critical",
                    "category": "compatibility",
                    "title": f"Uyumsuz Mod Çifti: {id_a} + {id_b}",
                    "description": reason,
                    "fix_steps": [
                        f"{id_a} veya {id_b} modlarından birini devre dışı bırakın.",
                        "Render optimizasyonu için Sodium + Iris kombinasyonunu tercih edin (OptiFine yerine).",
                    ],
                })

    def _check_dependencies(self) -> None:
        installed_ids = {m.mod_id.lower() for m in self.mods if m.mod_id}
        # fabric-api gibi yaygın aliaslar
        aliases = {"fabric-api": "fabric", "fabricapi": "fabric-api"}
        for alias, target in aliases.items():
            if target in installed_ids:
                installed_ids.add(alias)

        for mod in self.mods:
            for dep in mod.dependencies:
                if dep.get("type") in ("breaks", "conflicts"):
                    continue
                dep_id = dep.get("id", "").lower()
                if not dep_id or dep_id == "minecraft":
                    continue
                if dep_id.startswith("java"):
                    continue
                if dep_id not in installed_ids and dep_id not in ("fabricloader", "forge", "neoforge", "quilt_loader"):
                    mod.issues.append(f"Eksik bağımlılık: {dep_id}")
                    self.issues.append({
                        "severity": "error",
                        "category": "dependency",
                        "title": f"Eksik Bağımlılık: {dep_id}",
                        "description": f"{mod.display_name or mod.file_name} modu '{dep_id}' bağımlılığını gerektiriyor.",
                        "fix_steps": [
                            f"{dep_id} modunu Modrinth veya CurseForge'dan indirin.",
                            "Mod Doctor otomatik indirme özelliğini kullanın.",
                        ],
                        "mod_id": dep_id,
                        "source_mod": mod.mod_id,
                    })

    def _detect_loader_conflicts(self) -> None:
        loaders = {m.loader for m in self.mods if m.loader and m.loader != "unknown"}
        fabric_like = {"fabric", "quilt"} & loaders
        forge_like = {"forge", "neoforge"} & loaders

        if fabric_like and forge_like:
            self.issues.append({
                "severity": "critical",
                "category": "loader",
                "title": "Karışık Mod Loader",
                "description": "Hem Fabric/Quilt hem Forge/NeoForge modları tespit edildi. Bu modlar birlikte çalışmaz.",
                "fix_steps": [
                    "Kullanmak istediğiniz loader'a göre diğer modları devre dışı bırakın.",
                    "Ayrı bir Minecraft profili oluşturun.",
                ],
            })

    def _build_result(self) -> dict[str, Any]:
        healthy = []
        problematic = []
        for mod in self.mods:
            entry = {
                "mod_id": mod.mod_id,
                "display_name": mod.display_name or mod.file_name,
                "version": mod.version,
                "loader": mod.loader,
                "loader_label": LOADER_LABELS.get(mod.loader, mod.loader),
                "file_name": mod.file_name,
                "file_path": str(mod.file_path),
                "file_size": mod.file_size,
                "minecraft_versions": mod.minecraft_versions,
                "dependencies": mod.dependencies,
                "environment": mod.environment,
                "is_corrupted": mod.is_corrupted,
                "is_valid_jar": mod.is_valid_jar,
                "issues": mod.issues,
                "status": "ok" if not mod.issues and mod.is_valid_jar else "problem",
            }
            if entry["status"] == "ok":
                healthy.append(entry)
            else:
                problematic.append(entry)

        return {
            "mods": [self._mod_to_dict(m) for m in self.mods],
            "healthy_mods": healthy,
            "problematic_mods": problematic,
            "mod_count": len(self.mods),
            "issues": self.issues,
        }

    def _mod_to_dict(self, mod: ModMetadata) -> dict[str, Any]:
        return {
            "mod_id": mod.mod_id,
            "display_name": mod.display_name or mod.file_name,
            "version": mod.version,
            "loader": mod.loader,
            "loader_label": LOADER_LABELS.get(mod.loader, mod.loader),
            "file_name": mod.file_name,
            "file_path": str(mod.file_path),
            "file_size": mod.file_size,
            "minecraft_versions": mod.minecraft_versions,
            "dependencies": mod.dependencies,
            "environment": mod.environment,
            "is_corrupted": mod.is_corrupted,
            "is_valid_jar": mod.is_valid_jar,
            "issues": mod.issues,
            "status": "ok" if not mod.issues and mod.is_valid_jar and not mod.is_corrupted else "problem",
        }
