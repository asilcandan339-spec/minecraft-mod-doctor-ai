"""Minecraft kurulum yollarını tespit eder."""

from __future__ import annotations

import os
import winreg
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class MinecraftInstallation:
    """Tek bir Minecraft kurulumunu temsil eder."""

    name: str
    root_path: Path
    launcher_type: str
    game_dir: Path
    versions_dir: Path | None = None
    mods_dir: Path | None = None
    logs_dir: Path | None = None
    crash_reports_dir: Path | None = None
    config_dir: Path | None = None
    resourcepacks_dir: Path | None = None
    shaderpacks_dir: Path | None = None
    libraries_dir: Path | None = None
    extra_info: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.game_dir = Path(self.game_dir)
        self.root_path = Path(self.root_path)
        if self.versions_dir is None:
            self.versions_dir = self.game_dir / "versions"
        if self.mods_dir is None:
            self.mods_dir = self.game_dir / "mods"
        if self.logs_dir is None:
            self.logs_dir = self.game_dir / "logs"
        if self.crash_reports_dir is None:
            self.crash_reports_dir = self.game_dir / "crash-reports"
        if self.config_dir is None:
            self.config_dir = self.game_dir / "config"
        if self.resourcepacks_dir is None:
            self.resourcepacks_dir = self.game_dir / "resourcepacks"
        if self.shaderpacks_dir is None:
            self.shaderpacks_dir = self.game_dir / "shaderpacks"
        if self.libraries_dir is None:
            self.libraries_dir = self.root_path / "libraries"
            if not self.libraries_dir.exists():
                self.libraries_dir = self.game_dir / "libraries"


def _read_registry(key_path: str, value_name: str = "") -> str | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            if value_name:
                val, _ = winreg.QueryValueEx(key, value_name)
                return str(val) if val else None
            return winreg.QueryValue(key, None)
    except OSError:
        return None


def _default_minecraft_dir() -> Path:
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / ".minecraft"


def _detect_official_launcher() -> Iterator[MinecraftInstallation]:
    mc_dir = _default_minecraft_dir()
    if mc_dir.exists():
        yield MinecraftInstallation(
            name="Resmi Minecraft Launcher",
            root_path=mc_dir,
            launcher_type="official",
            game_dir=mc_dir,
        )


def _detect_tlauncher() -> Iterator[MinecraftInstallation]:
    appdata = os.environ.get("APPDATA", "")
    paths = [
        Path(appdata) / ".minecraft",
        Path(os.environ.get("LOCALAPPDATA", "")) / "TLauncher",
    ]
    for p in paths:
        has_tlauncher = (p / "TLauncher.exe").exists()
        has_versions = (p / "versions").exists()
        if p.exists() and (has_tlauncher or has_versions):
            tlauncher = Path(os.environ.get("LOCALAPPDATA", "")) / "TLauncher"
            if tlauncher.exists():
                yield MinecraftInstallation(
                    name="TLauncher",
                    root_path=tlauncher if tlauncher.exists() else p,
                    launcher_type="tlauncher",
                    game_dir=p,
                )
                return
    tlauncher_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "TLauncher"
    if tlauncher_dir.exists():
        mc = _default_minecraft_dir()
        yield MinecraftInstallation(
            name="TLauncher",
            root_path=tlauncher_dir,
            launcher_type="tlauncher",
            game_dir=mc if mc.exists() else tlauncher_dir,
        )


def _detect_prism_launcher() -> Iterator[MinecraftInstallation]:
    appdata = os.environ.get("APPDATA", "")
    paths = [
        Path(appdata) / "PrismLauncher",
        Path(appdata) / "PolyMC",
        Path(appdata) / "MultiMC",
    ]
    for base in paths:
        if not base.exists():
            continue
        instances = base / "instances"
        if instances.exists():
            for inst in instances.iterdir():
                if inst.is_dir() and (inst / "minecraft").exists():
                    yield MinecraftInstallation(
                        name=f"Prism Launcher - {inst.name}",
                        root_path=base,
                        launcher_type="prism",
                        game_dir=inst / "minecraft",
                        extra_info={"instance": inst.name},
                    )
        else:
            yield MinecraftInstallation(
                name="Prism Launcher",
                root_path=base,
                launcher_type="prism",
                game_dir=base,
            )


def _detect_curseforge() -> Iterator[MinecraftInstallation]:
    appdata = os.environ.get("APPDATA", "")
    cf_paths = [
        Path(appdata) / "curseforge" / "minecraft",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Overwolf" / "Curse" / "Minecraft",
    ]
    for base in cf_paths:
        instances = base / "Instances"
        if instances.exists():
            for inst in instances.iterdir():
                if inst.is_dir():
                    mc = inst / "minecraft" if (inst / "minecraft").exists() else inst
                    yield MinecraftInstallation(
                        name=f"CurseForge - {inst.name}",
                        root_path=base,
                        launcher_type="curseforge",
                        game_dir=mc,
                        extra_info={"instance": inst.name},
                    )
        elif base.exists():
            yield MinecraftInstallation(
                name="CurseForge Launcher",
                root_path=base,
                launcher_type="curseforge",
                game_dir=base / "Install" if (base / "Install").exists() else base,
            )


def _detect_multimc() -> Iterator[MinecraftInstallation]:
    appdata = os.environ.get("APPDATA", "")
    base = Path(appdata) / "MultiMC"
    if not base.exists():
        return
    instances = base / "instances"
    if instances.exists():
        for inst in instances.iterdir():
            if inst.is_dir() and (inst / ".minecraft").exists():
                yield MinecraftInstallation(
                    name=f"MultiMC - {inst.name}",
                    root_path=base,
                    launcher_type="multimc",
                    game_dir=inst / ".minecraft",
                    extra_info={"instance": inst.name},
                )


def _detect_gdlauncher() -> Iterator[MinecraftInstallation]:
    appdata = os.environ.get("APPDATA", "")
    base = Path(appdata) / "gdlauncher_next"
    if not base.exists():
        base = Path(appdata) / "gdlauncher"
    if base.exists():
        instances = base / "instances"
        if instances.exists():
            for inst in instances.iterdir():
                mc = inst / "minecraft" if (inst / "minecraft").exists() else inst
                if mc.is_dir():
                    yield MinecraftInstallation(
                        name=f"GDLauncher - {inst.name}",
                        root_path=base,
                        launcher_type="gdlauncher",
                        game_dir=mc,
                        extra_info={"instance": inst.name},
                    )


def _detect_sklauncher() -> Iterator[MinecraftInstallation]:
    appdata = os.environ.get("APPDATA", "")
    sk_dir = Path(appdata) / "SKlauncher"
    mc = _default_minecraft_dir()
    if sk_dir.exists() or (mc / "sklauncher").exists():
        yield MinecraftInstallation(
            name="SKLauncher",
            root_path=sk_dir if sk_dir.exists() else mc,
            launcher_type="sklauncher",
            game_dir=mc,
        )


def _scan_custom_folders() -> Iterator[MinecraftInstallation]:
    """Bilinen konumlarda .minecraft benzeri klasörleri ara."""
    search_roots = [
        Path(os.environ.get("USERPROFILE", "")),
        Path("D:/"),
        Path("E:/"),
    ]
    seen: set[Path] = set()
    for root in search_roots:
        if not root.exists():
            continue
        try:
            for path in root.rglob(".minecraft"):
                if path.is_dir() and path not in seen:
                    seen.add(path)
                    if (path / "mods").exists() or (path / "versions").exists():
                        yield MinecraftInstallation(
                            name=f"Özel Kurulum - {path.parent.name}",
                            root_path=path,
                            launcher_type="custom",
                            game_dir=path,
                        )
        except (PermissionError, OSError):
            continue


def detect_all_installations(include_custom_scan: bool = False) -> list[MinecraftInstallation]:
    """Tüm Minecraft kurulumlarını tespit eder."""
    installations: list[MinecraftInstallation] = []
    seen_dirs: set[Path] = set()

    detectors = [
        _detect_official_launcher,
        _detect_tlauncher,
        _detect_sklauncher,
        _detect_prism_launcher,
        _detect_curseforge,
        _detect_multimc,
        _detect_gdlauncher,
    ]
    if include_custom_scan:
        detectors.append(_scan_custom_folders)

    for detector in detectors:
        for inst in detector():
            resolved = inst.game_dir.resolve()
            if resolved not in seen_dirs:
                seen_dirs.add(resolved)
                installations.append(inst)

    return installations
