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

from app.models import Report
from app.utils.enums import ReportType


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
            report_type_display = self._format_report_type(report.report_type)
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
