"""PDF rapor oluşturucu."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.config import COLORS, REPORTS_DIR


class PDFReportGenerator:
    """Güzel PDF rapor oluşturur."""

    GREEN = colors.HexColor(COLORS["accent"])
    DARK = colors.HexColor(COLORS["bg_dark"])
    RED = colors.HexColor(COLORS["danger"])
    ORANGE = colors.HexColor(COLORS["warning"])

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=22,
            textColor=self.GREEN,
            alignment=TA_CENTER,
            spaceAfter=20,
        )
        self.heading_style = ParagraphStyle(
            "CustomHeading",
            parent=self.styles["Heading2"],
            fontSize=14,
            textColor=self.DARK,
            spaceBefore=15,
            spaceAfter=8,
        )
        self.body_style = ParagraphStyle(
            "CustomBody",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
        )

    def generate(self, scan_result: dict[str, Any], output_path: Path | None = None) -> Path:
        """PDF raporu oluşturur."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = REPORTS_DIR / f"mod_doctor_rapor_{timestamp}.pdf"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = []
        story.append(Paragraph("Minecraft Mod Doctor AI", self.title_style))
        story.append(Paragraph("Analiz Raporu", self.body_style))
        story.append(Spacer(1, 10))

        inst = scan_result.get("installation", {})
        story.append(Paragraph(f"Kurulum: {inst.get('name', 'Bilinmiyor')}", self.body_style))
        story.append(Paragraph(f"Tarih: {scan_result.get('scan_date', datetime.now().isoformat())}", self.body_style))
        story.append(Spacer(1, 15))

        # Sağlık skoru
        health = scan_result.get("health", {})
        if health:
            story.append(Paragraph("Sağlık Skoru", self.heading_style))
            health_data = [
                ["Metrik", "Değer"],
                ["Uyumluluk", f"%{health.get('compatibility', 0)}"],
                ["Çökme Riski", f"%{health.get('crash_risk', 0)}"],
                ["Performans", f"%{health.get('performance', 0)}"],
                ["Genel Not", f"{health.get('grade_label', '')} ({health.get('grade', '')})"],
            ]
            story.append(self._make_table(health_data))
            story.append(Spacer(1, 10))

        # Sorunlar
        issues = scan_result.get("issues", [])
        if issues:
            story.append(Paragraph(f"Sorunlar ({len(issues)})", self.heading_style))
            for issue in issues[:20]:
                sev = issue.get("severity", "info")
                color = self.RED if sev == "critical" else self.ORANGE if sev == "warning" else self.DARK
                style = ParagraphStyle("issue", parent=self.body_style, textColor=color)
                story.append(Paragraph(f"<b>{issue.get('title', '')}</b> [{sev}]", style))
                story.append(Paragraph(issue.get("description", ""), self.body_style))
                for step in issue.get("fix_steps", [])[:3]:
                    story.append(Paragraph(f"  → {step}", self.body_style))
                story.append(Spacer(1, 5))

        # Sağlıklı modlar
        healthy = scan_result.get("healthy_mods", [])
        if healthy:
            story.append(Paragraph(f"Sağlıklı Modlar ({len(healthy)})", self.heading_style))
            mod_data = [["Mod", "Sürüm", "Loader"]]
            for mod in healthy[:30]:
                mod_data.append([
                    mod.get("display_name", "")[:30],
                    mod.get("version", "")[:15],
                    mod.get("loader_label", mod.get("loader", "")),
                ])
            story.append(self._make_table(mod_data))

        # Eksik bağımlılıklar
        deps = scan_result.get("dependencies", {}).get("missing", [])
        if deps:
            story.append(Paragraph(f"Eksik Bağımlılıklar ({len(deps)})", self.heading_style))
            for dep in deps:
                story.append(Paragraph(f"• {dep.get('title', dep.get('mod_id', ''))}", self.body_style))
                dl = dep.get("download")
                if dl and dl.get("url"):
                    story.append(Paragraph(f"  Link: {dl['url']}", self.body_style))

        # Performans
        perf = scan_result.get("performance", {})
        if perf:
            story.append(Paragraph("Performans", self.heading_style))
            story.append(Paragraph(f"Tahmini FPS: ~{perf.get('estimated_fps', '?')}", self.body_style))
            story.append(Paragraph(f"Tahmini RAM: {perf.get('estimated_total_ram_mb', '?')} MB", self.body_style))
            for rec in perf.get("recommendations", [])[:5]:
                story.append(Paragraph(f"• {rec}", self.body_style))

        story.append(Spacer(1, 20))
        story.append(Paragraph(
            "Bu rapor Minecraft Mod Doctor AI tarafından otomatik oluşturulmuştur.",
            ParagraphStyle("footer", parent=self.body_style, alignment=TA_CENTER, textColor=colors.grey),
        ))

        doc.build(story)
        return output_path

    def _make_table(self, data: list[list[str]]) -> Table:
        table = Table(data, colWidths=[8 * cm, 8 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f5f5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return table
