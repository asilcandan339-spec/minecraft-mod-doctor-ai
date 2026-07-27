"""JAR dosyası okuma ve mod metadata çıkarma."""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import orjson
import toml


@dataclass
class ModMetadata:
    """Mod metadata bilgileri."""

    file_name: str
    file_path: Path
    mod_id: str = ""
    display_name: str = ""
    version: str = ""
    description: str = ""
    authors: list[str] = field(default_factory=list)
    loader: str = ""  # fabric, forge, neoforge, quilt, unknown
    minecraft_versions: list[str] = field(default_factory=list)
    dependencies: list[dict[str, str]] = field(default_factory=list)
    is_valid_jar: bool = True
    is_corrupted: bool = False
    file_size: int = 0
    sha256: str = ""
    environment: str = ""  # client, server, both
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


def _safe_read_json(data: bytes) -> dict | list | None:
    try:
        return orjson.loads(data)
    except orjson.JSONDecodeError:
        try:
            import json
            return json.loads(data.decode("utf-8", errors="replace"))
        except Exception:
            return None


def _parse_fabric_mod_json(content: dict) -> dict[str, Any]:
    deps = []
    for dep_id, dep_info in content.get("depends", {}).items():
        if isinstance(dep_info, str):
            deps.append({"id": dep_id, "version": dep_info, "type": "required"})
        elif isinstance(dep_info, list):
            deps.append({"id": dep_id, "version": "|".join(dep_info), "type": "required"})
    for dep_id, dep_info in content.get("breaks", {}).items():
        ver = dep_info if isinstance(dep_info, str) else "|".join(dep_info)
        deps.append({"id": dep_id, "version": ver, "type": "breaks"})
    for dep_id, dep_info in content.get("conflicts", {}).items():
        ver = dep_info if isinstance(dep_info, str) else "|".join(dep_info)
        deps.append({"id": dep_id, "version": ver, "type": "conflicts"})

    env = content.get("environment", "*")
    if env == "*":
        environment = "both"
    elif "client" in str(env):
        environment = "client"
    elif "server" in str(env):
        environment = "server"
    else:
        environment = "both"

    return {
        "mod_id": content.get("id", ""),
        "display_name": content.get("name", ""),
        "version": content.get("version", ""),
        "description": content.get("description", ""),
        "authors": [a if isinstance(a, str) else a.get("name", "") for a in content.get("authors", [])],
        "loader": "fabric",
        "minecraft_versions": _extract_mc_versions(content.get("depends", {})),
        "dependencies": deps,
        "environment": environment,
        "raw": content,
    }


def _parse_mods_toml(content: str) -> dict[str, Any]:
    try:
        data = toml.loads(content)
    except Exception:
        return {}

    mod_info = data.get("mod", data.get("mods", [{}]))
    if isinstance(mod_info, list):
        mod_info = mod_info[0] if mod_info else {}

    deps = []
    for dep in data.get("dependencies", {}).get(mod_info.get("modId", ""), []):
        if isinstance(dep, dict):
            deps.append({
                "id": dep.get("modId", ""),
                "version": dep.get("versionRange", ""),
                "type": "required" if dep.get("mandatory", True) else "optional",
                "side": dep.get("side", "BOTH"),
            })

    loader = "forge"
    if "neoforge" in content.lower() or mod_info.get("loader", "").lower() == "neoforge":
        loader = "neoforge"

    return {
        "mod_id": mod_info.get("modId", ""),
        "display_name": mod_info.get("displayName", mod_info.get("modId", "")),
        "version": mod_info.get("version", ""),
        "description": mod_info.get("description", ""),
        "authors": mod_info.get("authors", "").split(",") if mod_info.get("authors") else [],
        "loader": loader,
        "minecraft_versions": _extract_mc_versions_from_toml(data),
        "dependencies": deps,
        "environment": "both",
        "raw": data,
    }


def _extract_mc_versions(depends: dict) -> list[str]:
    mc = depends.get("minecraft", "")
    if isinstance(mc, list):
        return mc
    if isinstance(mc, str):
        versions = re.findall(r"\d+\.\d+(?:\.\d+)?", mc)
        return versions if versions else [mc]
    return []


def _extract_mc_versions_from_toml(data: dict) -> list[str]:
    versions = []
    for dep_list in data.get("dependencies", {}).values():
        if isinstance(dep_list, list):
            for dep in dep_list:
                if isinstance(dep, dict) and dep.get("modId") == "minecraft":
                    vr = dep.get("versionRange", "")
                    found = re.findall(r"\d+\.\d+(?:\.\d+)?", vr)
                    versions.extend(found)
    return versions


def _parse_quilt_mod_json(content: dict) -> dict[str, Any]:
    result = _parse_fabric_mod_json(content)
    result["loader"] = "quilt"
    return result


def read_jar_metadata(jar_path: Path) -> ModMetadata:
    """JAR dosyasından mod metadata okur."""
    meta = ModMetadata(
        file_name=jar_path.name,
        file_path=jar_path,
        file_size=jar_path.stat().st_size if jar_path.exists() else 0,
    )

    if not jar_path.exists():
        meta.is_valid_jar = False
        meta.issues.append("Dosya bulunamadı.")
        return meta

    if jar_path.suffix.lower() not in (".jar", ".zip"):
        meta.issues.append("Geçerli bir JAR dosyası değil.")
        return meta

    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            if zf.testzip() is not None:
                meta.is_corrupted = True
                meta.is_valid_jar = False
                meta.issues.append("JAR dosyası bozuk veya hasarlı.")
                return meta

            names = zf.namelist()

            # Fabric
            if "fabric.mod.json" in names:
                with zf.open("fabric.mod.json") as f:
                    content = _safe_read_json(f.read())
                    if content and isinstance(content, dict):
                        parsed = _parse_fabric_mod_json(content)
                        _apply_parsed(meta, parsed)

            # Quilt
            elif "quilt.mod.json" in names:
                with zf.open("quilt.mod.json") as f:
                    content = _safe_read_json(f.read())
                    if content and isinstance(content, dict):
                        parsed = _parse_quilt_mod_json(content)
                        _apply_parsed(meta, parsed)

            # Forge / NeoForge mods.toml
            mods_toml_paths = [n for n in names if n.endswith("mods.toml")]
            if mods_toml_paths and not meta.mod_id:
                with zf.open(mods_toml_paths[0]) as f:
                    parsed = _parse_mods_toml(f.read().decode("utf-8", errors="replace"))
                    _apply_parsed(meta, parsed)

            # META-INF fallback
            if not meta.mod_id:
                manifest_paths = [n for n in names if n == "META-INF/MANIFEST.MF"]
                if manifest_paths:
                    with zf.open(manifest_paths[0]) as f:
                        manifest = f.read().decode("utf-8", errors="replace")
                        _parse_manifest(meta, manifest)

            if not meta.mod_id:
                meta.mod_id = jar_path.stem.lower().replace(" ", "-")
                meta.display_name = jar_path.stem
                meta.issues.append("Mod metadata okunamadı, dosya adından tahmin edildi.")

    except zipfile.BadZipFile:
        meta.is_corrupted = True
        meta.is_valid_jar = False
        meta.issues.append("ZIP/JAR formatı geçersiz - dosya bozuk.")
    except Exception as e:
        meta.is_valid_jar = False
        meta.issues.append(f"Okuma hatası: {e}")

    return meta


def _apply_parsed(meta: ModMetadata, parsed: dict[str, Any]) -> None:
    meta.mod_id = parsed.get("mod_id", meta.mod_id)
    meta.display_name = parsed.get("display_name", meta.display_name)
    meta.version = parsed.get("version", meta.version)
    meta.description = parsed.get("description", meta.description)
    meta.authors = parsed.get("authors", meta.authors)
    meta.loader = parsed.get("loader", meta.loader)
    meta.minecraft_versions = parsed.get("minecraft_versions", meta.minecraft_versions)
    meta.dependencies = parsed.get("dependencies", meta.dependencies)
    meta.environment = parsed.get("environment", meta.environment)
    meta.raw_metadata = parsed.get("raw", {})


def _parse_manifest(meta: ModMetadata, manifest: str) -> None:
    for line in manifest.splitlines():
        if line.startswith("Implementation-Title:"):
            meta.display_name = line.split(":", 1)[1].strip()
        elif line.startswith("Implementation-Version:"):
            meta.version = line.split(":", 1)[1].strip()


def compute_sha256(jar_path: Path) -> str:
    """JAR dosyasının SHA256 hash'ini hesaplar."""
    import hashlib
    h = hashlib.sha256()
    try:
        with open(jar_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""
