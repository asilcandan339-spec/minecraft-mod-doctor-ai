"""Log ve crash-report analiz motoru."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.minecraft_paths import MinecraftInstallation
from src.utils.turkish_messages import SEVERITY_LABELS, ErrorExplanation, explain_error, explain_generic_exception


class LogAnalyzer:
    """Minecraft log dosyalarını analiz eder."""

    ERROR_KEYWORDS = re.compile(
        r"(ERROR|FATAL|Exception|Error:|Caused by:|Crash|failed|Could not|Unable to)",
        re.IGNORECASE,
    )

    def __init__(self, installation: MinecraftInstallation) -> None:
        self.installation = installation
        self.logs_dir = installation.logs_dir or installation.game_dir / "logs"
        self.crash_dir = installation.crash_reports_dir or installation.game_dir / "crash-reports"

    def analyze(self) -> dict[str, Any]:
        """Tüm log ve crash dosyalarını analiz eder."""
        results: dict[str, Any] = {
            "latest_log": None,
            "debug_log": None,
            "crash_reports": [],
            "errors": [],
            "warnings": [],
            "explained_errors": [],
            "summary": "",
        }

        latest = self.logs_dir / "latest.log" if self.logs_dir else None
        debug = self.logs_dir / "debug.log" if self.logs_dir else None

        if latest and latest.exists():
            results["latest_log"] = self._analyze_log_file(latest, "latest.log")
        if debug and debug.exists():
            results["debug_log"] = self._analyze_log_file(debug, "debug.log")

        if self.crash_dir and self.crash_dir.exists():
            crash_files = sorted(
                self.crash_dir.glob("crash-*.txt"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for crash in crash_files[:5]:
                results["crash_reports"].append(self._analyze_crash_report(crash))

        all_errors = []
        if results["latest_log"]:
            all_errors.extend(results["latest_log"].get("explained", []))
        for crash in results["crash_reports"]:
            all_errors.extend(crash.get("explained", []))

        seen_titles: set[str] = set()
        for err in all_errors:
            title = err.get("title", "")
            if title not in seen_titles:
                seen_titles.add(title)
                results["explained_errors"].append(err)
                sev = err.get("severity", "error")
                if sev in ("critical", "error"):
                    results["errors"].append(err)
                else:
                    results["warnings"].append(err)

        error_count = len(results["errors"])
        warning_count = len(results["warnings"])
        if error_count == 0 and warning_count == 0:
            results["summary"] = "Log dosyalarında ciddi bir hata tespit edilmedi."
        else:
            results["summary"] = (
                f"{error_count} hata ve {warning_count} uyarı tespit edildi. "
                "Detaylar aşağıda Türkçe olarak açıklanmıştır."
            )

        return results

    def _analyze_log_file(self, path: Path, label: str) -> dict[str, Any]:
        content = self._read_file(path)
        lines = content.splitlines()
        error_lines = [ln for ln in lines if self.ERROR_KEYWORDS.search(ln)]

        explained = []
        for line in error_lines[:50]:
            exp = explain_error(line)
            if exp:
                explained.append(self._explanation_to_dict(exp))
            elif "Exception" in line or "Error" in line:
                exp = explain_generic_exception(line)
                explained.append(self._explanation_to_dict(exp))

        # Çok satırlı stack trace grupla
        stack_blocks = self._extract_stack_traces(content)
        for block in stack_blocks[:10]:
            exp = explain_error(block)
            if exp:
                d = self._explanation_to_dict(exp)
                if d["title"] not in {e["title"] for e in explained}:
                    explained.append(d)

        return {
            "file": label,
            "path": str(path),
            "size": path.stat().st_size,
            "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            "line_count": len(lines),
            "error_line_count": len(error_lines),
            "explained": explained,
            "raw_error_lines": error_lines[:20],
        }

    def _analyze_crash_report(self, path: Path) -> dict[str, Any]:
        content = self._read_file(path)
        explained = []

        # Crash report başlık bilgisi
        mc_version = self._extract_crash_field(content, "Minecraft Version")
        loader_info = self._extract_crash_field(content, "Fabric Mods") or self._extract_crash_field(content, "Forge")
        description = self._extract_crash_field(content, "Description")

        exp = explain_error(content)
        if exp:
            explained.append(self._explanation_to_dict(exp))
        else:
            for line in content.splitlines():
                if "Exception" in line:
                    exp = explain_generic_exception(line)
                    explained.append(self._explanation_to_dict(exp))
                    break

        return {
            "file": path.name,
            "path": str(path),
            "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            "minecraft_version": mc_version,
            "loader_info": loader_info[:200] if loader_info else "",
            "description": description,
            "explained": explained,
            "content_preview": content[:2000],
        }

    def _extract_stack_traces(self, content: str) -> list[str]:
        blocks = []
        current = []
        for line in content.splitlines():
            if self.ERROR_KEYWORDS.search(line):
                if current:
                    blocks.append("\n".join(current))
                current = [line]
            elif current and (line.startswith("\t") or line.startswith(" ") or "at " in line or "Caused by" in line):
                current.append(line)
            elif current:
                blocks.append("\n".join(current))
                current = []
        if current:
            blocks.append("\n".join(current))
        return blocks

    def _extract_crash_field(self, content: str, field: str) -> str:
        match = re.search(rf"{re.escape(field)}:\s*(.+)", content)
        return match.group(1).strip() if match else ""

    def _read_file(self, path: Path, max_size: int = 5_000_000) -> str:
        try:
            size = path.stat().st_size
            if size > max_size:
                with open(path, "rb") as f:
                    f.seek(max(0, size - max_size))
                    data = f.read()
                return data.decode("utf-8", errors="replace")
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    @staticmethod
    def _explanation_to_dict(exp: ErrorExplanation) -> dict[str, Any]:
        return {
            "title": exp.title,
            "explanation": exp.explanation,
            "fix_steps": exp.fix_steps,
            "severity": exp.severity,
            "severity_label": SEVERITY_LABELS.get(exp.severity, exp.severity),
            "original": exp.original[:300],
        }
