"""Sağlık skoru hesaplayıcı."""

from __future__ import annotations

from typing import Any


class HealthScoreCalculator:
    """Uyumluluk, çökme riski ve performans skorlarını hesaplar."""

    def __init__(self, scan_result: dict[str, Any]) -> None:
        self.result = scan_result

    def calculate(self) -> dict[str, Any]:
        compatibility = self._calc_compatibility()
        crash_risk = self._calc_crash_risk()
        performance = self._calc_performance()

        overall = round((compatibility + (100 - crash_risk) + performance) / 3, 1)

        return {
            "compatibility": round(compatibility, 1),
            "crash_risk": round(crash_risk, 1),
            "performance": round(performance, 1),
            "overall": overall,
            "grade": self._grade(overall),
            "grade_label": self._grade_label(overall),
        }

    def _calc_compatibility(self) -> float:
        score = 100.0
        mods = self.result.get("mods", [])
        issues = self.result.get("issues", [])

        if not mods:
            return 100.0

        problematic = sum(1 for m in mods if m.get("status") == "problem")
        score -= (problematic / max(len(mods), 1)) * 40

        for issue in issues:
            cat = issue.get("category", "")
            sev = issue.get("severity", "")
            if cat in ("compatibility", "loader", "dependency"):
                if sev == "critical":
                    score -= 15
                elif sev == "error":
                    score -= 8
                elif sev == "warning":
                    score -= 3

        versions = self.result.get("versions", {})
        loader = versions.get("loader", "unknown")
        mod_loaders = {m.get("loader") for m in mods if m.get("loader") not in ("unknown", "")}
        if loader != "unknown" and mod_loaders:
            for ml in mod_loaders:
                if ml and loader not in ml and ml not in loader:
                    if not (loader in ("fabric",) and ml in ("fabric", "quilt")):
                        score -= 10

        return max(0, min(100, score))

    def _calc_crash_risk(self) -> float:
        risk = 0.0
        issues = self.result.get("issues", [])
        logs = self.result.get("logs", {})

        for issue in issues:
            sev = issue.get("severity", "")
            if sev == "critical":
                risk += 20
            elif sev == "error":
                risk += 10
            elif sev == "warning":
                risk += 3

        explained = logs.get("explained_errors", [])
        for err in explained:
            sev = err.get("severity", "")
            if sev == "critical":
                risk += 15
            elif sev == "error":
                risk += 8

        mods = self.result.get("mods", [])
        corrupted = sum(1 for m in mods if m.get("is_corrupted"))
        risk += corrupted * 25

        return min(100, risk)

    def _calc_performance(self) -> float:
        perf = self.result.get("performance", {})
        if perf.get("performance_score") is not None:
            return float(perf["performance_score"])

        score = 100.0
        mods = self.result.get("mods", [])
        score -= len(mods) * 0.5
        shaderpacks = self.result.get("shaderpacks", [])
        if shaderpacks:
            score -= 10
        return max(0, min(100, score))

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 40:
            return "D"
        return "F"

    @staticmethod
    def _grade_label(score: float) -> str:
        if score >= 90:
            return "Mükemmel"
        if score >= 75:
            return "İyi"
        if score >= 60:
            return "Orta"
        if score >= 40:
            return "Zayıf"
        return "Kritik"
