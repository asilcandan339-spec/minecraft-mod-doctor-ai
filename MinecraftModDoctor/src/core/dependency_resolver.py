"""Bağımlılık çözümleyici ve indirici."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from src.config import MOD_SOURCES
from src.utils.minecraft_paths import MinecraftInstallation


class DependencyResolver:
    """Eksik mod bağımlılıklarını tespit eder ve indirir."""

    MODRINTH_API = MOD_SOURCES["modrinth"]

    def __init__(self, installation: MinecraftInstallation) -> None:
        self.installation = installation
        self.mods_dir = installation.mods_dir or installation.game_dir / "mods"

    def resolve(self) -> dict[str, Any]:
        """Eksik bağımlılıkları listeler."""
        from src.core.mod_analyzer import ModAnalyzer

        analyzer = ModAnalyzer(self.installation)
        mod_result = analyzer.analyze()

        missing = []
        for issue in mod_result.get("issues", []):
            if issue.get("category") == "dependency":
                mod_id = issue.get("mod_id", "")
                download_info = self._lookup_modrinth(mod_id) if mod_id else None
                missing.append({
                    "mod_id": mod_id,
                    "title": issue.get("title", ""),
                    "description": issue.get("description", ""),
                    "source_mod": issue.get("source_mod", ""),
                    "download": download_info,
                })

        return {
            "missing": missing,
            "missing_count": len(missing),
        }

    def _lookup_modrinth(self, mod_id: str) -> dict[str, Any] | None:
        """Modrinth API'den mod bilgisi arar."""
        if not mod_id:
            return None
        try:
            resp = requests.get(
                f"{self.MODRINTH_API}/project/{mod_id}",
                timeout=10,
                headers={"User-Agent": "MinecraftModDoctor/1.0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "source": "modrinth",
                    "title": data.get("title", mod_id),
                    "url": f"https://modrinth.com/mod/{data.get('slug', mod_id)}",
                    "description": data.get("description", "")[:200],
                    "downloads": data.get("downloads", 0),
                }
            # slug ile ara
            search = requests.get(
                f"{self.MODRINTH_API}/search",
                params={"query": mod_id, "limit": 1},
                timeout=10,
                headers={"User-Agent": "MinecraftModDoctor/1.0"},
            )
            if search.status_code == 200:
                hits = search.json().get("hits", [])
                if hits:
                    hit = hits[0]
                    return {
                        "source": "modrinth",
                        "title": hit.get("title", mod_id),
                        "url": f"https://modrinth.com/mod/{hit.get('slug', mod_id)}",
                        "description": hit.get("description", "")[:200],
                        "downloads": hit.get("downloads", 0),
                    }
        except requests.RequestException:
            pass
        return {
            "source": "manual",
            "title": mod_id,
            "url": f"https://modrinth.com/mods?q={mod_id}",
            "description": "Manuel indirme gerekli.",
        }

    def download_dependency(self, mod_id: str, mc_version: str = "", loader: str = "") -> dict[str, Any]:
        """Modrinth'ten bağımlılık indirmeye çalışır."""
        if not self.mods_dir:
            return {"success": False, "message": "Mods klasörü bulunamadı."}

        self.mods_dir.mkdir(parents=True, exist_ok=True)

        try:
            params: dict[str, str] = {}
            if mc_version:
                params["game_versions"] = f'["{mc_version}"]'
            if loader:
                loaders = {"fabric": "fabric", "forge": "forge", "neoforge": "neoforge", "quilt": "quilt"}
                if loader in loaders:
                    params["loaders"] = f'["{loaders[loader]}"]'

            versions_resp = requests.get(
                f"{self.MODRINTH_API}/project/{mod_id}/version",
                params=params,
                timeout=15,
                headers={"User-Agent": "MinecraftModDoctor/1.0"},
            )
            if versions_resp.status_code != 200:
                return {"success": False, "message": f"Modrinth'te {mod_id} bulunamadı."}

            versions = versions_resp.json()
            if not versions:
                return {"success": False, "message": "Uyumlu sürüm bulunamadı."}

            version = versions[0]
            files = version.get("files", [])
            if not files:
                return {"success": False, "message": "İndirilebilir dosya yok."}

            primary = next((f for f in files if f.get("primary")), files[0])
            download_url = primary.get("url", "")
            filename = primary.get("filename", f"{mod_id}.jar")

            dl_resp = requests.get(download_url, timeout=60, headers={"User-Agent": "MinecraftModDoctor/1.0"})
            if dl_resp.status_code != 200:
                return {"success": False, "message": "İndirme başarısız."}

            dest = self.mods_dir / filename
            dest.write_bytes(dl_resp.content)
            return {
                "success": True,
                "message": f"{filename} başarıyla indirildi.",
                "path": str(dest),
            }
        except requests.RequestException as e:
            return {"success": False, "message": f"İndirme hatası: {e}"}
