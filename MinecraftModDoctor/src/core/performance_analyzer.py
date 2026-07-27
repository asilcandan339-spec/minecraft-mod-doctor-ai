"""Performans analiz modülü."""

from __future__ import annotations

from typing import Any

import psutil

from src.utils.minecraft_paths import MinecraftInstallation

# Bilinen ağır modlar (tahmini bellek kullanımı MB)
HEAVY_MODS: dict[str, int] = {
    "create": 400,
    "terrafirmacraft": 500,
    "immersive-engineering": 350,
    "applied-energistics-2": 300,
    "ae2": 300,
    "botania": 200,
    "twilightforest": 250,
    "betterend": 200,
    "betternether": 200,
    "distant-horizons": 800,
    "iris": 150,
    "sodium": 50,
    "optifine": 100,
    "shaders": 200,
    "journeymap": 150,
    "dynmap": 200,
}


class PerformanceAnalyzer:
    """Sistem ve mod performans analizi."""

    def __init__(self, installation: MinecraftInstallation) -> None:
        self.installation = installation

    def analyze(self, mods: list[dict] | None = None) -> dict[str, Any]:
        """Performans metriklerini hesaplar."""
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        cpu_count = psutil.cpu_count(logical=True) or 4

        estimated_mod_ram = 0
        heavy_mods = []
        if mods:
            for mod in mods:
                mod_id = (mod.get("mod_id") or mod.get("file_name", "")).lower()
                for key, ram in HEAVY_MODS.items():
                    if key in mod_id:
                        estimated_mod_ram += ram
                        heavy_mods.append({
                            "name": mod.get("display_name", mod.get("file_name", "")),
                            "estimated_ram_mb": ram,
                        })
                        break
                else:
                    estimated_mod_ram += 30  # ortalama mod başına

        base_ram = 1500  # Minecraft taban
        shader_extra = 0
        sp_dir = self.installation.shaderpacks_dir
        if sp_dir and sp_dir.exists() and any(sp_dir.iterdir()):
            shader_extra = 1000

        total_estimated = base_ram + estimated_mod_ram + shader_extra
        available_ram_mb = mem.available // (1024 * 1024)

        # FPS tahmini (kaba)
        fps_base = 60
        if cpu_count >= 8:
            fps_base = 80
        elif cpu_count >= 4:
            fps_base = 60
        else:
            fps_base = 40

        fps_penalty = len(heavy_mods) * 5 + (shader_extra // 200)
        estimated_fps = max(15, fps_base - fps_penalty)

        if mem.total < 8 * (1024 ** 3):
            estimated_fps = max(10, estimated_fps - 15)

        performance_score = 100
        if total_estimated > available_ram_mb:
            performance_score -= 30
        if cpu_percent > 80:
            performance_score -= 20
        if len(heavy_mods) > 5:
            performance_score -= 15
        if shader_extra > 0 and mem.total < 16 * (1024 ** 3):
            performance_score -= 10
        performance_score = max(0, min(100, performance_score))

        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": cpu_count,
                "model": self._get_cpu_model(),
            },
            "ram": {
                "total_mb": mem.total // (1024 * 1024),
                "available_mb": available_ram_mb,
                "used_percent": mem.percent,
            },
            "estimated_mod_ram_mb": estimated_mod_ram,
            "estimated_total_ram_mb": total_estimated,
            "estimated_fps": estimated_fps,
            "heavy_mods": heavy_mods,
            "performance_score": performance_score,
            "recommendations": self._recommendations(total_estimated, available_ram_mb, heavy_mods, mem.total),
        }

    def _get_cpu_model(self) -> str:
        try:
            import platform
            return platform.processor() or "Bilinmiyor"
        except Exception:
            return "Bilinmiyor"

    def _recommendations(
        self,
        estimated_ram: int,
        available: int,
        heavy_mods: list,
        total_ram: int,
    ) -> list[str]:
        recs = []
        if estimated_ram > available:
            recs.append(
                f"Tahmini RAM kullanımı ({estimated_ram} MB) kullanılabilir bellekten ({available} MB) fazla. "
                "JVM argümanlarına daha fazla RAM ayırın veya mod sayısını azaltın."
            )
        if total_ram < 8 * (1024 ** 3):
            recs.append("8 GB'dan az RAM ile modlu Minecraft zorlanabilir. 16 GB önerilir.")
        if len(heavy_mods) > 3:
            names = ", ".join(m["name"] for m in heavy_mods[:5])
            recs.append(f"Ağır modlar tespit edildi: {names}. FPS düşüşü yaşayabilirsiniz.")
        if not recs:
            recs.append("Sistem kaynaklarınız modlu oyun için yeterli görünüyor.")
        return recs
