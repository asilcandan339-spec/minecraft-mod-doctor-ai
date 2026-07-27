"""Yerleşik AI asistan - tarama bağlamına göre Türkçe yanıt verir."""

from __future__ import annotations

import re
from typing import Any

import requests

from src.config import AI_API_KEY, AI_API_URL


class AIAssistant:
    """Minecraft mod sorunları için AI asistan."""

    SYSTEM_PROMPT = (
        "Sen Minecraft Mod Doctor AI asistanısın. Türkçe yanıt ver. "
        "Kullanıcının mod, crash, performans ve uyumluluk sorularını basit dille açıkla. "
        "Teknik jargon kullanma, herkesin anlayacağı şekilde yaz. "
        "Çözüm adımları numaralı liste olarak ver."
    )

    def __init__(self, scan_context: dict[str, Any] | None = None) -> None:
        self.scan_context = scan_context or {}
        self.history: list[dict[str, str]] = []

    def set_context(self, scan_result: dict[str, Any]) -> None:
        self.scan_context = scan_result

    def ask(self, question: str) -> str:
        """Kullanıcı sorusuna yanıt verir."""
        self.history.append({"role": "user", "content": question})

        # Harici API varsa kullan
        if AI_API_URL and AI_API_KEY:
            response = self._ask_external_api(question)
            if response:
                self.history.append({"role": "assistant", "content": response})
                return response

        # Yerel bilgi tabanlı yanıt
        response = self._local_response(question)
        self.history.append({"role": "assistant", "content": response})
        return response

    def _ask_external_api(self, question: str) -> str | None:
        try:
            context_summary = self._build_context_summary()
            resp = requests.post(
                AI_API_URL,
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT + "\n\nTarama bağlamı:\n" + context_summary},
                        *self.history,
                    ],
                },
                headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except requests.RequestException:
            pass
        return None

    def _local_response(self, question: str) -> str:
        q = question.lower()

        if any(w in q for w in ("crash", "çök", "çökme", "hata")):
            return self._answer_crash(question)
        if any(w in q for w in ("fps", "performans", "kasma", "lag", "yavaş")):
            return self._answer_performance(question)
        if any(w in q for w in ("mod", "uyumsuz", "çalışmıyor", "yüklen")):
            return self._answer_mod(question)
        if any(w in q for w in ("kaldır", "sil", "hangi mod")):
            return self._answer_which_mod(question)
        if any(w in q for w in ("bağımlılık", "dependency", "eksik")):
            return self._answer_dependency(question)
        if any(w in q for w in ("java", "sürüm", "version")):
            return self._answer_java(question)

        return self._answer_general(question)

    def _answer_crash(self, question: str) -> str:
        logs = self.scan_context.get("logs", {})
        errors = logs.get("explained_errors", [])
        if errors:
            lines = ["Son taramada tespit edilen hatalar:\n"]
            for i, err in enumerate(errors[:5], 1):
                lines.append(f"{i}. **{err.get('title', '')}**")
                lines.append(f"   {err.get('explanation', '')}")
                fixes = err.get("fix_steps", [])
                if fixes:
                    lines.append("   Çözüm:")
                    for j, fix in enumerate(fixes[:3], 1):
                        lines.append(f"   {j}. {fix}")
                lines.append("")
            return "\n".join(lines)

        return (
            "Henüz bir tarama yapılmamış veya log dosyasında hata bulunamadı.\n\n"
            "Genel crash çözüm adımları:\n"
            "1. Son eklediğiniz modu kaldırın.\n"
            "2. 'Minecraft'ı Tara' butonuna tıklayın.\n"
            "3. Otomatik düzeltmeleri uygulayın.\n"
            "4. JVM argümanlarına -Xmx4G ekleyin.\n"
            "5. Java sürümünüzün Minecraft sürümünüzle uyumlu olduğundan emin olun."
        )

    def _answer_performance(self, question: str) -> str:
        perf = self.scan_context.get("performance", {})
        if perf:
            fps = perf.get("estimated_fps", "?")
            heavy = perf.get("heavy_mods", [])
            recs = perf.get("recommendations", [])
            lines = [
                f"Tahmini FPS: ~{fps}",
                f"CPU Kullanımı: %{perf.get('cpu', {}).get('percent', '?')}",
                f"RAM: {perf.get('ram', {}).get('available_mb', '?')} MB kullanılabilir",
                "",
            ]
            if heavy:
                lines.append("Ağır modlar:")
                for m in heavy:
                    lines.append(f"  - {m.get('name', '')} (~{m.get('estimated_ram_mb', 0)} MB)")
                lines.append("")
            lines.append("Öneriler:")
            for i, rec in enumerate(recs, 1):
                lines.append(f"{i}. {rec}")
            lines.extend([
                "",
                "FPS artırmak için:",
                "1. Sodium + Iris kullanın (OptiFine yerine).",
                "2. Shader'ı kapatın veya hafif shader seçin.",
                "3. Render mesafesini düşürün.",
                "4. JVM'e -Xmx6G veya daha fazla RAM ayırın.",
            ])
            return "\n".join(lines)

        return (
            "FPS düşüklüğü genellikle şu nedenlerden kaynaklanır:\n"
            "1. Çok fazla mod (50+ mod FPS'i ciddi düşürür).\n"
            "2. Ağır shader paketleri (BSL, Complementary vb.).\n"
            "3. Yetersiz RAM (-Xmx değerini artırın).\n"
            "4. OptiFine + Sodium çakışması.\n"
            "5. Distant Horizons gibi ağır modlar.\n\n"
            "Önce 'Minecraft'ı Tara' yapın, performans analizi otomatik çalışacaktır."
        )

    def _answer_mod(self, question: str) -> str:
        problematic = self.scan_context.get("problematic_mods", [])
        if not problematic:
            mods = self.scan_context.get("mods", [])
            problematic = [m for m in mods if m.get("status") == "problem"]

        if problematic:
            lines = ["Sorunlu modlar:\n"]
            for mod in problematic[:10]:
                lines.append(f"• **{mod.get('display_name', mod.get('file_name', ''))}**")
                for issue in mod.get("issues", [])[:3]:
                    lines.append(f"  - {issue}")
                lines.append("")
            lines.append("Bu modları 'Disabled Mods' klasörüne taşıyarak devre dışı bırakabilirsiniz.")
            return "\n".join(lines)

        return (
            "Mod çalışmama nedenleri:\n"
            "1. Yanlış Minecraft sürümü.\n"
            "2. Yanlış mod loader (Fabric modu Forge'da çalışmaz).\n"
            "3. Eksik bağımlılık (Fabric API gibi).\n"
            "4. Bozuk JAR dosyası.\n"
            "5. Başka bir modla çakışma.\n\n"
            "Tarama yaparak detaylı analiz alabilirsiniz."
        )

    def _answer_which_mod(self, question: str) -> str:
        issues = self.scan_context.get("issues", [])
        critical_mods = []
        for issue in issues:
            if issue.get("severity") == "critical":
                critical_mods.append(issue.get("title", ""))

        if critical_mods:
            lines = ["Kaldırmanızı önerdiğim modlar/sorunlar:\n"]
            for i, title in enumerate(critical_mods[:5], 1):
                lines.append(f"{i}. {title}")
            lines.append("\nModları silmek yerine 'Disabled Mods' klasörüne taşımanızı öneririm.")
            return "\n".join(lines)

        return (
            "Hangi modu kaldıracağınızı belirlemek için:\n"
            "1. Son eklediğiniz modu ilk olarak kaldırın.\n"
            "2. Yarı yarıya bölerek test edin (50 mod → 25 mod).\n"
            "3. OptiFine + Sodium/Iris çakışması varsa OptiFine'ı kaldırın.\n"
            "4. Yinelenen modlardan eski sürümü kaldırın.\n"
            "5. Otomatik düzeltme özelliğini kullanın."
        )

    def _answer_dependency(self, question: str) -> str:
        deps = self.scan_context.get("dependencies", {}).get("missing", [])
        if deps:
            lines = ["Eksik bağımlılıklar:\n"]
            for dep in deps:
                lines.append(f"• {dep.get('title', dep.get('mod_id', ''))}")
                dl = dep.get("download")
                if dl and dl.get("url"):
                    lines.append(f"  İndir: {dl['url']}")
            lines.append("\nMod Doctor otomatik indirme özelliğini kullanabilirsiniz.")
            return "\n".join(lines)

        return (
            "Yaygın eksik bağımlılıklar:\n"
            "• Fabric modları → Fabric API gerekli\n"
            "• Forge modları → Forge'un doğru sürümü gerekli\n"
            "• Cloth Config, Architectury API gibi kütüphane modları\n\n"
            "Tarama yaparak eksik bağımlılıkları otomatik tespit edebilirsiniz."
        )

    def _answer_java(self, question: str) -> str:
        java = self.scan_context.get("java", {})
        versions = self.scan_context.get("versions", {})
        mc = versions.get("minecraft_version", "bilinmiyor")

        lines = [
            f"Minecraft sürümü: {mc}",
            f"Java sürümü: {java.get('version', 'tespit edilemedi')}",
            "",
            "Java sürüm rehberi:",
            "• Minecraft 1.20.5+ → Java 21",
            "• Minecraft 1.18 - 1.20.4 → Java 17",
            "• Minecraft 1.17 → Java 16",
            "• Minecraft 1.16 ve altı → Java 8",
            "",
            "İndirme: https://adoptium.net",
        ]
        return "\n".join(lines)

    def _answer_general(self, question: str) -> str:
        health = self.scan_context.get("health", {})
        mod_count = self.scan_context.get("mod_count", len(self.scan_context.get("mods", [])))

        if health:
            return (
                f"Minecraft Mod Doctor AI asistanına hoş geldiniz!\n\n"
                f"Son tarama özeti:\n"
                f"• Mod sayısı: {mod_count}\n"
                f"• Uyumluluk: %{health.get('compatibility', '?')}\n"
                f"• Çökme riski: %{health.get('crash_risk', '?')}\n"
                f"• Performans: %{health.get('performance', '?')}\n"
                f"• Genel not: {health.get('grade_label', '?')} ({health.get('grade', '?')})\n\n"
                f"Sorabileceğiniz örnek sorular:\n"
                f"• Bu mod neden çalışmıyor?\n"
                f"• FPS neden düşük?\n"
                f"• Bu crash neden oldu?\n"
                f"• Hangi modu kaldırmalıyım?"
            )

        return (
            "Merhaba! Ben Minecraft Mod Doctor AI asistanıyım.\n\n"
            "Size mod sorunları, crash analizi, performans ve uyumluluk konularında yardımcı olabilirim.\n\n"
            "Başlamak için önce 'Minecraft'ı Tara' butonuna tıklayın, ardından sorunuzu sorun.\n\n"
            "Örnek sorular:\n"
            "• Bu mod neden çalışmıyor?\n"
            "• FPS neden düşük?\n"
            "• Bu crash neden oldu?\n"
            "• Hangi modu kaldırmalıyım?"
        )

    def _build_context_summary(self) -> str:
        parts = []
        inst = self.scan_context.get("installation", {})
        if inst:
            parts.append(f"Kurulum: {inst.get('name', '')}")
        health = self.scan_context.get("health", {})
        if health:
            parts.append(f"Sağlık: Uyumluluk %{health.get('compatibility')}, Risk %{health.get('crash_risk')}")
        mods = self.scan_context.get("mods", [])
        parts.append(f"Mod sayısı: {len(mods)}")
        issues = self.scan_context.get("issues", [])
        parts.append(f"Sorun sayısı: {len(issues)}")
        return "\n".join(parts)

    def get_history(self) -> list[dict[str, str]]:
        return self.history.copy()

    def clear_history(self) -> None:
        self.history.clear()
