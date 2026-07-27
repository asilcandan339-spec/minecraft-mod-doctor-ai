"""Kurulum tarayıcı - tüm Minecraft dosyalarını tarar."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.log_analyzer import LogAnalyzer
from src.core.mod_analyzer import ModAnalyzer
from src.core.performance_analyzer import PerformanceAnalyzer
from src.core.health_score import HealthScoreCalculator
from src.core.dependency_resolver import DependencyResolver
from src.utils.minecraft_paths import MinecraftInstallation


class InstallationScanner:
    """Tek bir Minecraft kurulumunu kapsamlı tarar."""

    def __init__(self, installation: MinecraftInstallation) -> None:
        self.installation = installation

    def scan(self, progress_callback=None) -> dict[str, Any]:
        """Tam tarama gerçekleştirir."""
        steps = [
            ("Sürüm bilgisi okunuyor...", self._scan_versions),
            ("Modlar analiz ediliyor...", self._scan_mods),
            ("Log dosyaları inceleniyor...", self._scan_logs),
            ("Yapılandırma taranıyor...", self._scan_config),
            ("Kaynak paketleri kontrol ediliyor...", self._scan_resourcepacks),
            ("Shader paketleri kontrol ediliyor...", self._scan_shaderpacks),
            ("Kütüphaneler kontrol ediliyor...", self._scan_libraries),
            ("Java sürümü tespit ediliyor...", self._detect_java),
            ("Bağımlılıklar çözümleniyor...", self._resolve_dependencies),
            ("Performans analizi...", self._analyze_performance),
            ("Sağlık skoru hesaplanıyor...", self._calculate_health),
        ]

        result: dict[str, Any] = {
            "installation": {
                "name": self.installation.name,
                "launcher_type": self.installation.launcher_type,
                "game_dir": str(self.installation.game_dir),
            },
            "scan_date": datetime.now().isoformat(),
            "versions": {},
            "mods": [],
            "logs": {},
            "config": {},
            "resourcepacks": [],
            "shaderpacks": [],
            "libraries": {},
            "java": {},
            "dependencies": {},
            "performance": {},
            "health": {},
            "issues": [],
        }

        for i, (msg, func) in enumerate(steps):
            if progress_callback:
                progress_callback(i / len(steps), msg)
            partial = func()
            if isinstance(partial, dict):
                for key, val in partial.items():
                    if key == "issues":
                        result["issues"].extend(val)
                    elif key in result and isinstance(result[key], dict) and isinstance(val, dict):
                        result[key].update(val)
                    elif key in result and isinstance(result[key], list) and isinstance(val, list):
                        result[key].extend(val)
                    else:
                        result[key] = val

        # Performans analizi mod listesiyle yeniden hesapla
        from src.core.performance_analyzer import PerformanceAnalyzer
        perf = PerformanceAnalyzer(self.installation).analyze(result.get("mods", []))
        result["performance"] = perf

        # Sağlık skoru
        result = self.finalize_health(result)

        if progress_callback:
            progress_callback(1.0, "Tarama tamamlandı!")

        return result

    def _scan_versions(self) -> dict[str, Any]:
        versions_dir = self.installation.versions_dir
        if not versions_dir or not versions_dir.exists():
            return {
                "versions": {"installed": [], "active": None, "loader": "unknown", "minecraft_version": "unknown"},
                "issues": [{
                    "severity": "warning",
                    "category": "version",
                    "title": "Sürüm Klasörü Bulunamadı",
                    "description": "versions klasörü mevcut değil.",
                    "fix_steps": ["Minecraft'ı launcher'dan bir kez başlatın."],
                }],
            }

        installed = []
        loader = "vanilla"
        mc_version = "unknown"

        for version_dir in versions_dir.iterdir():
            if not version_dir.is_dir():
                continue
            json_file = version_dir / f"{version_dir.name}.json"
            entry = {"id": version_dir.name, "path": str(version_dir)}
            if json_file.exists():
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                    entry["type"] = data.get("type", "release")
                    entry["main_class"] = data.get("mainClass", "")
                    if "fabric" in version_dir.name.lower():
                        loader = "fabric"
                    elif "forge" in version_dir.name.lower():
                        loader = "forge"
                    elif "neoforge" in version_dir.name.lower():
                        loader = "neoforge"
                    elif "quilt" in version_dir.name.lower():
                        loader = "quilt"
                    mc_match = re.search(r"(\d+\.\d+(?:\.\d+)?)", version_dir.name)
                    if mc_match:
                        mc_version = mc_match.group(1)
                except (json.JSONDecodeError, OSError):
                    pass
            installed.append(entry)

        # launcher_profiles.json'dan aktif profil
        profiles_file = self.installation.game_dir / "launcher_profiles.json"
        active = None
        if profiles_file.exists():
            try:
                profiles = json.loads(profiles_file.read_text(encoding="utf-8"))
                selected = profiles.get("selectedProfile", "")
                for pid, profile in profiles.get("profiles", {}).items():
                    if pid == selected or profile.get("name") == selected:
                        active = profile.get("lastVersionId", profile.get("name"))
                        break
            except (json.JSONDecodeError, OSError):
                pass

        return {
            "versions": {
                "installed": installed,
                "active": active,
                "loader": loader,
                "minecraft_version": mc_version,
            },
        }

    def _scan_mods(self) -> dict[str, Any]:
        analyzer = ModAnalyzer(self.installation)
        mod_result = analyzer.analyze()
        return {
            "mods": mod_result.get("mods", []),
            "healthy_mods": mod_result.get("healthy_mods", []),
            "problematic_mods": mod_result.get("problematic_mods", []),
            "mod_count": mod_result.get("mod_count", 0),
            "issues": mod_result.get("issues", []),
        }

    def _scan_logs(self) -> dict[str, Any]:
        analyzer = LogAnalyzer(self.installation)
        log_result = analyzer.analyze()
        issues = []
        for err in log_result.get("explained_errors", []):
            issues.append({
                "severity": err.get("severity", "error"),
                "category": "log",
                "title": err.get("title", ""),
                "description": err.get("explanation", ""),
                "fix_steps": err.get("fix_steps", []),
            })
        return {"logs": log_result, "issues": issues}

    def _scan_config(self) -> dict[str, Any]:
        config_dir = self.installation.config_dir
        configs = []
        issues = []
        if config_dir and config_dir.exists():
            for cfg in config_dir.rglob("*"):
                if cfg.is_file() and cfg.suffix in (".json", ".toml", ".cfg", ".properties"):
                    try:
                        size = cfg.stat().st_size
                        configs.append({
                            "name": cfg.name,
                            "path": str(cfg.relative_to(config_dir)),
                            "size": size,
                        })
                        if size == 0:
                            issues.append({
                                "severity": "warning",
                                "category": "config",
                                "title": f"Boş Yapılandırma: {cfg.name}",
                                "description": f"{cfg.name} dosyası boş, varsayılan ayarlar kullanılacak.",
                                "fix_steps": ["Dosyayı silin, oyun yeniden oluşturacaktır."],
                            })
                    except OSError:
                        pass
        return {"config": {"files": configs, "count": len(configs)}, "issues": issues}

    def _scan_resourcepacks(self) -> dict[str, Any]:
        rp_dir = self.installation.resourcepacks_dir
        packs = []
        if rp_dir and rp_dir.exists():
            for item in rp_dir.iterdir():
                if item.is_dir() or item.suffix == ".zip":
                    try:
                        size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file()) if item.is_dir() else item.stat().st_size
                        packs.append({"name": item.name, "size": size, "path": str(item)})
                    except OSError:
                        packs.append({"name": item.name, "size": 0, "path": str(item)})
        return {"resourcepacks": packs}

    def _scan_shaderpacks(self) -> dict[str, Any]:
        sp_dir = self.installation.shaderpacks_dir
        packs = []
        if sp_dir and sp_dir.exists():
            for item in sp_dir.iterdir():
                if item.is_dir() or item.suffix == ".zip":
                    try:
                        size = item.stat().st_size if item.is_file() else sum(
                            f.stat().st_size for f in item.rglob("*") if f.is_file()
                        )
                        packs.append({"name": item.name, "size": size, "path": str(item)})
                    except OSError:
                        packs.append({"name": item.name, "size": 0, "path": str(item)})
        return {"shaderpacks": packs}

    def _scan_libraries(self) -> dict[str, Any]:
        lib_dir = self.installation.libraries_dir
        issues = []
        lib_count = 0
        missing = []
        if lib_dir and lib_dir.exists():
            jars = list(lib_dir.rglob("*.jar"))
            lib_count = len(jars)
            for jar in jars[:100]:
                try:
                    if jar.stat().st_size < 100:
                        missing.append(str(jar))
                except OSError:
                    missing.append(str(jar))
        if missing:
            issues.append({
                "severity": "error",
                "category": "libraries",
                "title": "Bozuk Kütüphane Dosyaları",
                "description": f"{len(missing)} kütüphane dosyası bozuk veya eksik görünüyor.",
                "fix_steps": [
                    "Launcher'dan 'Oyun Dosyalarını Onar' seçeneğini kullanın.",
                    "Minecraft'ı yeniden yükleyin.",
                ],
            })
        return {
            "libraries": {"count": lib_count, "missing_or_corrupt": missing[:10]},
            "issues": issues,
        }

    def _detect_java(self) -> dict[str, Any]:
        java_info: dict[str, Any] = {"version": "unknown", "path": "", "vendor": ""}
        issues = []

        for cmd in ("java", "javaw"):
            try:
                proc = subprocess.run(
                    [cmd, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                )
                output = proc.stderr + proc.stdout
                match = re.search(r'version "([^"]+)"', output)
                if match:
                    java_info["version"] = match.group(1)
                    java_info["path"] = cmd
                    vendor_match = re.search(r"(.+?) version", output)
                    if vendor_match:
                        java_info["vendor"] = vendor_match.group(1).strip()
                    break
            except (subprocess.SubprocessError, FileNotFoundError, OSError):
                continue

        if java_info["version"] == "unknown":
            issues.append({
                "severity": "warning",
                "category": "java",
                "title": "Java Tespit Edilemedi",
                "description": "Sistem PATH'inde Java bulunamadı.",
                "fix_steps": [
                    "Adoptium'dan Java 17 veya 21 indirin: https://adoptium.net",
                    "Launcher ayarlarından Java yolunu belirtin.",
                ],
            })

        return {"java": java_info, "issues": issues}

    def _resolve_dependencies(self) -> dict[str, Any]:
        resolver = DependencyResolver(self.installation)
        return {"dependencies": resolver.resolve()}

    def _analyze_performance(self) -> dict[str, Any]:
        analyzer = PerformanceAnalyzer(self.installation)
        return {"performance": analyzer.analyze()}

    def _calculate_health(self) -> dict[str, Any]:
        # Geçici olarak mevcut sonuçları kullan - scan içinde son adım
        return {}

    def finalize_health(self, result: dict[str, Any]) -> dict[str, Any]:
        """Sağlık skorunu hesaplar."""
        calc = HealthScoreCalculator(result)
        health = calc.calculate()
        result["health"] = health
        return result
