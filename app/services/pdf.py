from io import BytesIO
from datetime import datetime
from typing import Any
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart

from app.models import Report
from app.utils.enums import ReportType

# Imported lazily inside generate_incident_report_pdf to avoid circular import at module load
# from app.models import IncidentReport


class PDFService:
    """Service for generating PDF documents from reports."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.assets_path = Path(__file__).parent.parent / "assets"

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for professional PDF design."""
        # Header style with centered alignment
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=colors.HexColor('#0b2265'),
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Report title with centered alignment
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a365d'),
            fontName='Helvetica-Bold',
            spaceBefore=12
        ))

        # Section header with centered alignment and rounded effect via styling
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=14,
            spaceAfter=10,
            textColor=colors.HexColor('#ffffff'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            backColor=colors.HexColor('#1a365d')
        ))

        # Field label
        self.styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=2,
            fontName='Helvetica-Bold'
        ))

        # Field value
        self.styles.add(ParagraphStyle(
            name='FieldValue',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor('#2d3748'),
            fontName='Helvetica'
        ))

        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#718096'),
            alignment=TA_CENTER,
            spaceBefore=20
        ))

    # ── Cover page builder ───────────────────────────────────────────────────

    def _build_cover_page(
        self,
        title: str,
        subtitle: str,
        details: list[list[str]],
    ) -> list:
        """
        Build a professional full-cover first page. Returns a list of flowables
        ending with PageBreak() so main content starts on page 2.

        Args:
            title:    Large headline (e.g. "Incident Report")
            subtitle: Smaller descriptor below title (e.g. "Severity: CRITICAL — SAMO TELECOMS × SEACOM")
            details:  List of [label, value] rows for the info table
        """
        elements = []

        # Load logos
        samo_logo = seacom_logo = None
        try:
            p = self.assets_path / "samo-logo.png"
            if p.exists():
                samo_logo = Image(str(p), width=55 * mm, height=20 * mm)
        except Exception:
            pass
        try:
            p = self.assets_path / "seacom-logo.png"
            if p.exists():
                seacom_logo = Image(str(p), width=55 * mm, height=20 * mm)
        except Exception:
            pass

        # ── Blue header band (logos + brand name) ────────────────────────────
        brand_style = ParagraphStyle(
            'CoverBrand',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#a0aec0'),
            alignment=TA_CENTER,
            fontName='Helvetica',
        )
        header_data = [[
            samo_logo or Paragraph("<b>SAMO</b>", self.styles['CompanyHeader']),
            Paragraph("SAMO TELECOMS &amp; SEACOM", brand_style),
            seacom_logo or Paragraph("<b>SEACOM</b>", self.styles['CompanyHeader']),
        ]]
        header_table = Table(header_data, colWidths=[60 * mm, 50 * mm, 60 * mm], rowHeights=[32 * mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0b2265')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 22 * mm))

        # ── Large report title ───────────────────────────────────────────────
        cover_title_style = ParagraphStyle(
            'CoverTitle',
            parent=self.styles['Normal'],
            fontSize=28,
            textColor=colors.HexColor('#1a365d'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=6,
        )
        elements.append(Paragraph(title, cover_title_style))

        # ── Subtitle ─────────────────────────────────────────────────────────
        cover_sub_style = ParagraphStyle(
            'CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=13,
            textColor=colors.HexColor('#4a5568'),
            alignment=TA_CENTER,
            fontName='Helvetica',
        )
        elements.append(Paragraph(subtitle, cover_sub_style))
        elements.append(Spacer(1, 8 * mm))

        # ── Thin navy divider ─────────────────────────────────────────────────
        elements.append(self._create_divider())
        elements.append(Spacer(1, 8 * mm))

        # ── Details table ────────────────────────────────────────────────────
        if details:
            det_table = Table(details, colWidths=[55 * mm, 115 * mm])
            det_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2d3748')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#4a5568')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f7fafc')]),
            ]))
            elements.append(det_table)

        elements.append(Spacer(1, 30 * mm))

        # ── Confidentiality footer ────────────────────────────────────────────
        conf_style = ParagraphStyle(
            'CoverConf',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#a0aec0'),
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique',
        )
        elements.append(Paragraph(
            "CONFIDENTIAL — FOR SAMO TELECOMS AND SEACOM USE ONLY",
            conf_style,
        ))
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph(
            f"Generated {datetime.now().strftime('%d %B %Y %H:%M')} UTC",
            conf_style,
        ))

        # ── Start main content on page 2 ─────────────────────────────────────
        elements.append(PageBreak())
        return elements

    # ── Field reports ────────────────────────────────────────────────────────

    def generate_report_pdf(self, report: Report) -> BytesIO:
        """
        Generate a professional PDF document for a completed report with logos and rounded design elements.

        Args:
            report: The Report model instance to generate PDF for

        Returns:
            BytesIO buffer containing the PDF document
        """
        buffer = BytesIO()

        try:
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm,
                title=f"Report_{report.report_type.value}_{report.id}"
            )

            story = []

            # ── Cover page ────────────────────────────────────────────────────
            report_type_display = self._format_report_type(report.report_type)
            cover_details: list[list[str]] = [
                ["Report Type", report_type_display],
                ["Status", report.status.value.upper()],
                ["Service Provider", report.service_provider or "N/A"],
            ]
            try:
                if report.technician and report.technician.user:
                    u = report.technician.user
                    cover_details.append(["Technician", f"{u.name} {u.surname}"])
                    cover_details.append(["Phone", report.technician.phone or "N/A"])
            except Exception:
                pass
            try:
                if report.task:
                    if report.task.seacom_ref:
                        cover_details.append(["Reference", report.task.seacom_ref])
                    if report.task.site:
                        cover_details.append(["Site", report.task.site.name])
                        cover_details.append(["Region", report.task.site.region.value.replace("-", " ").title()])
            except Exception:
                pass
            cover_details.append(["Generated", self._format_datetime(report.created_at)])
            story.extend(self._build_cover_page(
                title=f"{report_type_display} Report",
                subtitle="Field Report — SAMO TELECOMS × SEACOM",
                details=cover_details,
            ))

            # Create header with company logos
            # Load PNG logos if available
            samo_logo = None
            seacom_logo = None

            try:
                samo_png_path = self.assets_path / "samo-logo.png"
                if samo_png_path.exists():
                    samo_logo = Image(str(samo_png_path), width=70*mm, height=25*mm)
            except Exception:
                pass

            try:
                seacom_png_path = self.assets_path / "seacom-logo.png"
                if seacom_png_path.exists():
                    seacom_logo = Image(str(seacom_png_path), width=70*mm, height=25*mm)
            except Exception:
                pass

            # Build logo row - use images if available, otherwise text
            logo_row = [
                samo_logo if samo_logo else Paragraph("<b>SAMO TELECOMS</b>", self.styles['CompanyHeader']),
                Spacer(1, 0),  # Center spacer
                seacom_logo if seacom_logo else Paragraph("<b>SEACOM</b>", self.styles['CompanyHeader'])
            ]

            logo_table = Table([logo_row], colWidths=[70*mm, 50*mm, 70*mm])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(logo_table)
            story.append(Spacer(1, 10))

            # Divider line
            story.append(self._create_divider())
            story.append(Spacer(1, 10))

            # Report Title - centered
            story.append(Paragraph(f"{report_type_display} Report", self.styles['ReportTitle']))
            story.append(Spacer(1, 14))

            # Report Metadata Section
            story.append(Paragraph("Report Information", self.styles['SectionHeader']))

            metadata_data = [
                ["Report ID", str(report.id)],
                ["Report Type", report_type_display],
                ["Status", report.status.value.upper()],
                ["Service Provider", report.service_provider],
                ["Created Date", self._format_datetime(report.created_at)],
                ["Completed Date", self._format_datetime(report.updated_at)],
            ]

            # Add technician info - with safety checks
            try:
                if report.technician and report.technician.user:
                    user = report.technician.user
                    metadata_data.append(["Technician", f"{user.name} {user.surname}"])
                    metadata_data.append(["Phone", report.technician.phone])
            except Exception:
                pass

            # Add task info - with safety checks
            try:
                if report.task:
                    if report.task.seacom_ref:
                        metadata_data.append(["Task Reference", report.task.seacom_ref])
                    if report.task.site:
                        metadata_data.append(["Site", report.task.site.name])
                        metadata_data.append(["Region", report.task.site.region.value.replace("-", " ").title()])
            except Exception:
                pass

            # Create metadata table with rounded corners effect
            metadata_table = Table(metadata_data, colWidths=[110, 360])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2d3748')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#4a5568')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#ffffff')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f7fafc')]),
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 16))

            # Report Data Section
            if report.data:
                story.append(Paragraph("Report Details", self.styles['SectionHeader']))
                story.append(Spacer(1, 10))
                story.extend(self._render_report_data(report.data))

            # Attachments Section
            if report.attachments:
                story.append(Spacer(1, 16))
                story.append(Paragraph("Attachments", self.styles['SectionHeader']))

                attachment_data = [["Field Name", "Value"]]
                for key, value in report.attachments.items():
                    attachment_data.append([key, str(value)[:60]])

                if len(attachment_data) > 1:
                    att_table = Table(attachment_data, colWidths=[140, 330])
                    att_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#ffffff')),
                        ('TEXTCOLOR', (1, 1), (-1, -1), colors.HexColor('#4a5568')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f7fafc')]),
                    ]))
                    story.append(att_table)

            # Footer
            story.append(Spacer(1, 24))
            story.append(self._create_divider())
            story.append(Spacer(1, 8))
            story.append(Paragraph(
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | "
                f"Report ID: {str(report.id)[:8]}",
                self.styles['Footer']
            ))

            # Build PDF
            doc.build(story)

        except Exception as e:
            raise

        buffer.seek(0)
        return buffer

    # ── Incident reports ─────────────────────────────────────────────────────

    def generate_incident_report_pdf(self, report: "IncidentReport") -> BytesIO:  # type: ignore[name-defined]
        """
        Generate a professional PDF document for an incident report.

        Args:
            report: The IncidentReport model instance

        Returns:
            BytesIO buffer containing the PDF document
        """
        from app.models.incident_report import IncidentReport  # noqa: F401 – satisfies type checker

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title=f"Incident_Report_{report.id}",
        )

        story = []

        # ── Cover page ────────────────────────────────────────────────────────
        inc_severity = str(getattr(report, "severity", "minor")).upper() if hasattr(report, "severity") else "N/A"
        seacom_ref = getattr(report, "seacom_ref", None) or str(report.incident_id)[:8]
        cover_details: list[list[str]] = [
            ["Incident Reference", seacom_ref],
            ["Site", report.site_name],
            ["Technician", report.technician_name],
            ["Severity", inc_severity],
            ["Report Date", self._format_datetime(report.report_date)],
            ["Generated", self._format_datetime(report.created_at)],
        ]
        story.extend(self._build_cover_page(
            title="Incident Report",
            subtitle=f"Severity: {inc_severity} — SAMO TELECOMS × SEACOM",
            details=cover_details,
        ))

        # ── Logos ──────────────────────────────────────────────────────────────
        samo_logo = seacom_logo = None
        try:
            p = self.assets_path / "samo-logo.png"
            if p.exists():
                samo_logo = Image(str(p), width=70 * mm, height=25 * mm)
        except Exception:
            pass
        try:
            p = self.assets_path / "seacom-logo.png"
            if p.exists():
                seacom_logo = Image(str(p), width=70 * mm, height=25 * mm)
        except Exception:
            pass

        logo_row = [
            samo_logo or Paragraph("<b>SAMO TELECOMS</b>", self.styles["CompanyHeader"]),
            Spacer(1, 0),
            seacom_logo or Paragraph("<b>SEACOM</b>", self.styles["CompanyHeader"]),
        ]
        logo_table = Table([logo_row], colWidths=[70 * mm, 50 * mm, 70 * mm])
        logo_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(logo_table)
        story.append(Spacer(1, 10))
        story.append(self._create_divider())
        story.append(Spacer(1, 10))

        # ── Title ──────────────────────────────────────────────────────────────
        story.append(Paragraph("Incident Report", self.styles["ReportTitle"]))
        story.append(Spacer(1, 14))

        # ── Metadata table ─────────────────────────────────────────────────────
        story.append(Paragraph("Report Information", self.styles["SectionHeader"]))
        metadata_data = [
            ["Report ID", str(report.id)],
            ["Incident ID", str(report.incident_id)],
            ["Site", report.site_name],
            ["Technician", report.technician_name],
            ["Report Date", self._format_datetime(report.report_date)],
            ["Generated", self._format_datetime(report.created_at)],
        ]
        metadata_table = Table(metadata_data, colWidths=[110, 360])
        metadata_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2d3748")),
            ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#4a5568")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#ffffff")),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f7fafc")]),
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 16))

        # ── Narrative sections ─────────────────────────────────────────────────
        sections = [
            ("1. Introduction", report.introduction),
            ("2. Problem Statement", report.problem_statement),
            ("3. Findings", report.findings),
            ("4. Actions Taken", report.actions_taken),
            ("5. Root Cause Analysis", report.root_cause_analysis),
            ("6. Conclusion", report.conclusion),
        ]
        for heading, body in sections:
            story.append(Paragraph(heading, self.styles["SectionHeader"]))
            story.append(Spacer(1, 6))
            story.append(Paragraph(body or "N/A", self.styles["FieldValue"]))
            story.append(Spacer(1, 12))

        # ── Signature placeholder ──────────────────────────────────────────────
        story.append(Spacer(1, 24))
        story.append(Paragraph("Technician Signature", self.styles["SectionHeader"]))
        story.append(Spacer(1, 40))
        sig_data = [["Signature: _________________________________", f"Date: {self._format_datetime(report.report_date)}"]]
        sig_table = Table(sig_data, colWidths=[250, 220])
        sig_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ]))
        story.append(sig_table)

        # ── Footer ─────────────────────────────────────────────────────────────
        story.append(Spacer(1, 24))
        story.append(self._create_divider())
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | "
            f"Report ID: {str(report.id)[:8]}",
            self.styles["Footer"],
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer

    # ── Executive summary PDF (management) ───────────────────────────────────

    def generate_executive_summary_pdf(
        self,
        month_label: str,
        sla_compliance: float,
        total_incidents: int,
        total_tasks: int,
        monthly_incidents: list[dict],   # [{month: str, count: int}]
        technician_performance: list[dict],  # [{name: str, incidents: int, tasks: int}]
        regional_performance: list[dict],    # [{region: str, compliance: float}]
    ) -> BytesIO:
        """
        Generate an executive management summary PDF with embedded charts.

        Args:
            month_label:             Display label, e.g. "February 2026"
            sla_compliance:          Overall SLA compliance percentage
            total_incidents:         Total incidents in period
            total_tasks:             Total tasks in period
            monthly_incidents:       Last 6 months incident counts for bar chart
            technician_performance:  Per-technician workload data for bar chart
            regional_performance:    Per-region SLA compliance for summary table

        Returns:
            BytesIO buffer containing the PDF document
        """
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title=f"Executive_Summary_{month_label}",
        )

        story = []

        # ── Cover page ────────────────────────────────────────────────────────
        cover_details: list[list[str]] = [
            ["Period", month_label],
            ["SLA Compliance", f"{sla_compliance:.1f}%"],
            ["Total Incidents", str(total_incidents)],
            ["Total Tasks", str(total_tasks)],
            ["Generated", datetime.now().strftime("%d %B %Y %H:%M UTC")],
        ]
        story.extend(self._build_cover_page(
            title="Executive Management Report",
            subtitle=f"{month_label} — SAMO TELECOMS × SEACOM",
            details=cover_details,
        ))

        # ── Page 2: Logos + Title ─────────────────────────────────────────────
        samo_logo = seacom_logo = None
        try:
            p = self.assets_path / "samo-logo.png"
            if p.exists():
                samo_logo = Image(str(p), width=70 * mm, height=25 * mm)
        except Exception:
            pass
        try:
            p = self.assets_path / "seacom-logo.png"
            if p.exists():
                seacom_logo = Image(str(p), width=70 * mm, height=25 * mm)
        except Exception:
            pass

        logo_row = [
            samo_logo or Paragraph("<b>SAMO TELECOMS</b>", self.styles["CompanyHeader"]),
            Spacer(1, 0),
            seacom_logo or Paragraph("<b>SEACOM</b>", self.styles["CompanyHeader"]),
        ]
        logo_table = Table([logo_row], colWidths=[70 * mm, 50 * mm, 70 * mm])
        logo_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(logo_table)
        story.append(Spacer(1, 8))
        story.append(self._create_divider())
        story.append(Spacer(1, 8))
        story.append(Paragraph("Executive Management Report", self.styles["ReportTitle"]))
        story.append(Paragraph(month_label, self.styles["Footer"]))
        story.append(Spacer(1, 16))

        # ── KPI summary row ───────────────────────────────────────────────────
        story.append(Paragraph("Key Performance Indicators", self.styles["SectionHeader"]))
        kpi_data = [
            ["Metric", "Value"],
            ["SLA Compliance", f"{sla_compliance:.1f}%"],
            ["Total Incidents", str(total_incidents)],
            ["Total Tasks", str(total_tasks)],
        ]
        kpi_table = Table(kpi_data, colWidths=[235, 235])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#ffffff")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#2d3748")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f7fafc")]),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 16))

        # ── Monthly incident trend bar chart ──────────────────────────────────
        if monthly_incidents:
            story.append(Paragraph("Monthly Incident Trend (Last 6 Months)", self.styles["SectionHeader"]))
            story.append(Spacer(1, 8))

            chart_width = 400
            chart_height = 160
            d = Drawing(chart_width, chart_height + 40)
            bc = VerticalBarChart()
            bc.x = 40
            bc.y = 30
            bc.height = chart_height
            bc.width = chart_width - 60
            bc.data = [[entry.get("count", 0) for entry in monthly_incidents]]
            bc.categoryAxis.categoryNames = [entry.get("month", "") for entry in monthly_incidents]
            bc.categoryAxis.labels.angle = 0
            bc.categoryAxis.labels.fontSize = 8
            bc.valueAxis.labels.fontSize = 8
            bc.bars[0].fillColor = colors.HexColor("#1a365d")
            bc.bars[0].strokeColor = colors.HexColor("#0b2265")
            bc.valueAxis.valueMin = 0
            d.add(bc)
            story.append(d)
            story.append(Spacer(1, 16))

        # ── Technician workload bar chart ─────────────────────────────────────
        if technician_performance:
            story.append(Paragraph("Technician Activity (Incidents + Tasks)", self.styles["SectionHeader"]))
            story.append(Spacer(1, 8))

            names = [e.get("name", "Unknown")[:18] for e in technician_performance[:8]]
            totals = [e.get("incidents", 0) + e.get("tasks", 0) for e in technician_performance[:8]]

            chart_w = 400
            chart_h = 140
            d2 = Drawing(chart_w, chart_h + 40)
            hbc = HorizontalBarChart()
            hbc.x = 90
            hbc.y = 10
            hbc.height = chart_h
            hbc.width = chart_w - 110
            hbc.data = [totals]
            hbc.categoryAxis.categoryNames = names
            hbc.categoryAxis.labels.fontSize = 7
            hbc.valueAxis.labels.fontSize = 7
            hbc.bars[0].fillColor = colors.HexColor("#2b6cb0")
            hbc.bars[0].strokeColor = colors.HexColor("#1a365d")
            hbc.valueAxis.valueMin = 0
            d2.add(hbc)
            story.append(d2)
            story.append(Spacer(1, 16))

        # ── Regional SLA compliance table ─────────────────────────────────────
        if regional_performance:
            story.append(Paragraph("Regional SLA Compliance", self.styles["SectionHeader"]))
            reg_data = [["Region", "Compliance %"]]
            for row in regional_performance:
                reg_data.append([
                    row.get("region", "N/A").replace("_", " ").title(),
                    f"{row.get('compliance', 0):.1f}%",
                ])
            reg_table = Table(reg_data, colWidths=[300, 170])
            reg_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#ffffff")),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#2d3748")),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f7fafc")]),
            ]))
            story.append(reg_table)
            story.append(Spacer(1, 16))

        # ── Footer ─────────────────────────────────────────────────────────────
        story.append(self._create_divider())
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | "
            f"Executive Summary — {month_label}",
            self.styles["Footer"],
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer

    # ── Shared helpers ───────────────────────────────────────────────────────

    def _create_divider(self):
        """Create a divider line as a table."""
        divider = Table([[""],], colWidths=[470])
        divider.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1a365d')),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return divider

    def _format_report_type(self, report_type: ReportType) -> str:
        """Format report type enum to display string."""
        return report_type.value.replace("-", " ").title()

    def _format_datetime(self, dt: datetime | None) -> str:
        """Format datetime to display string."""
        if dt is None:
            return "N/A"
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _render_report_data(self, data: dict[str, Any], level: int = 0) -> list:
        """
        Recursively render report data dictionary into PDF elements.

        Args:
            data: The data dictionary to render
            level: Nesting level for indentation

        Returns:
            List of PDF elements
        """
        elements = []
        indent = "    " * level

        for key, value in data.items():
            formatted_key = key.replace("_", " ").title()

            if isinstance(value, dict):
                elements.append(Paragraph(
                    f"{indent}<b>{formatted_key}:</b>",
                    self.styles['FieldValue']
                ))
                elements.extend(self._render_report_data(value, level + 1))
            elif isinstance(value, list):
                elements.append(Paragraph(
                    f"{indent}<b>{formatted_key}:</b>",
                    self.styles['FieldValue']
                ))
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        elements.append(Paragraph(
                            f"{indent}    Item {i + 1}:",
                            self.styles['FieldValue']
                        ))
                        elements.extend(self._render_report_data(item, level + 2))
                    else:
                        elements.append(Paragraph(
                            f"{indent}    • {item}",
                            self.styles['FieldValue']
                        ))
            elif isinstance(value, bool):
                display_value = "Yes" if value else "No"
                elements.append(Paragraph(
                    f"{indent}<b>{formatted_key}:</b> {display_value}",
                    self.styles['FieldValue']
                ))
            else:
                display_value = str(value) if value is not None else "N/A"
                elements.append(Paragraph(
                    f"{indent}<b>{formatted_key}:</b> {display_value}",
                    self.styles['FieldValue']
                ))

        return elements


def get_pdf_service() -> PDFService:
    return PDFService()
