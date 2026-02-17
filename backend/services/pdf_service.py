"""
PDF Generation Service - ReportLab을 사용한 Delivery PDF 생성
Canva 템플릿 링크와 사용 방법을 포함한 PDF를 생성합니다.
"""
import logging
import os
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..config import settings

logger = logging.getLogger(__name__)

# 색상 팔레트
PURPLE = colors.HexColor("#7c3aed")
PURPLE_LIGHT = colors.HexColor("#ede9fe")
GRAY_DARK = colors.HexColor("#1f2937")
GRAY = colors.HexColor("#6b7280")
GRAY_LIGHT = colors.HexColor("#f3f4f6")
WHITE = colors.white

USAGE_INSTRUCTIONS = [
    ("Step 1", "Click the Canva template link above to open the design in Canva."),
    ("Step 2", "Sign in to your Canva account (free account works)."),
    ("Step 3", 'Click "Use template" to create your own copy.'),
    ("Step 4", "Customize text, colors, images, and other elements as needed."),
    ("Step 5", "Download your finished design as PNG, PDF, or other formats."),
    ("Step 6", "The template link is yours to keep — reuse it anytime!"),
]

TERMS = (
    "This is a digital product for personal and commercial use. "
    "Do not resell or redistribute the template link. "
    "Please contact support if you experience any issues."
)


class PDFService:
    """ReportLab 기반 Delivery PDF 생성 서비스"""

    def __init__(self):
        self.pdf_dir = Path(settings.pdf_dir)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

    def generate_delivery_pdf(
        self,
        template_id: int,
        template_name: str,
        template_link: str,
        description: str = "",
        category: str = "",
    ) -> str:
        """
        Delivery PDF 생성 후 파일 경로 반환.

        Args:
            template_id: DB의 CanvaTemplate ID
            template_name: 템플릿 이름
            template_link: Canva 템플릿 링크 URL
            description: 템플릿 설명 (선택)
            category: 카테고리 (선택)

        Returns:
            생성된 PDF 파일의 절대 경로 문자열
        """
        filename = f"delivery_{template_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = self.pdf_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = self._build_story(
            template_name=template_name,
            template_link=template_link,
            description=description,
            category=category,
        )

        doc.build(story)
        logger.info(f"PDF generated: {filepath}")
        return str(filepath)

    def _build_story(
        self,
        template_name: str,
        template_link: str,
        description: str,
        category: str,
    ) -> list:
        """PDF 콘텐츠 블록 구성"""
        styles = getSampleStyleSheet()
        story = []

        # ── 헤더 배너 ──────────────────────────────
        header_data = [[
            Paragraph(
                '<font color="white" size="18"><b>🎨 Canva Template</b></font>',
                ParagraphStyle(
                    "HeaderTitle",
                    fontName="Helvetica-Bold",
                    fontSize=18,
                    textColor=WHITE,
                    alignment=TA_CENTER,
                    spaceAfter=4,
                ),
            ),
            Paragraph(
                '<font color="white" size="10">Digital Delivery</font>',
                ParagraphStyle(
                    "HeaderSub",
                    fontName="Helvetica",
                    fontSize=10,
                    textColor=WHITE,
                    alignment=TA_CENTER,
                ),
            ),
        ]]
        header_table = Table([[Paragraph(
            f'<font color="white"><b>🎨  Canva Template  ·  Digital Delivery</b></font>',
            ParagraphStyle(
                "Banner",
                fontName="Helvetica-Bold",
                fontSize=16,
                textColor=WHITE,
                alignment=TA_CENTER,
            ),
        )]], colWidths=[17 * cm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PURPLE),
            ("TOPPADDING", (0, 0), (-1, -1), 16),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("ROUNDEDCORNERS", [8]),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.5 * cm))

        # ── 템플릿 이름 ──────────────────────────────
        story.append(Paragraph(
            template_name,
            ParagraphStyle(
                "TemplateName",
                fontName="Helvetica-Bold",
                fontSize=22,
                textColor=GRAY_DARK,
                alignment=TA_CENTER,
                spaceAfter=6,
            ),
        ))

        if category:
            story.append(Paragraph(
                f"Category: {category}",
                ParagraphStyle(
                    "Category",
                    fontName="Helvetica",
                    fontSize=11,
                    textColor=GRAY,
                    alignment=TA_CENTER,
                    spaceAfter=4,
                ),
            ))

        story.append(Spacer(1, 0.3 * cm))
        story.append(HRFlowable(width="100%", thickness=1, color=PURPLE_LIGHT))
        story.append(Spacer(1, 0.4 * cm))

        # ── 설명 ──────────────────────────────────
        if description:
            story.append(Paragraph(
                description,
                ParagraphStyle(
                    "Description",
                    fontName="Helvetica",
                    fontSize=11,
                    textColor=GRAY,
                    alignment=TA_LEFT,
                    spaceAfter=8,
                    leading=16,
                ),
            ))
            story.append(Spacer(1, 0.3 * cm))

        # ── 템플릿 링크 박스 ──────────────────────────
        story.append(Paragraph(
            "Your Template Link",
            ParagraphStyle(
                "SectionTitle",
                fontName="Helvetica-Bold",
                fontSize=13,
                textColor=GRAY_DARK,
                spaceAfter=8,
            ),
        ))

        link_table = Table([[
            Paragraph(
                f'<link href="{template_link}"><font color="#7c3aed"><b>{template_link}</b></font></link>',
                ParagraphStyle(
                    "LinkStyle",
                    fontName="Helvetica",
                    fontSize=10,
                    textColor=PURPLE,
                    wordWrap="CJK",
                ),
            )
        ]], colWidths=[17 * cm])
        link_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PURPLE_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ("BOX", (0, 0), (-1, -1), 1.5, PURPLE),
            ("ROUNDEDCORNERS", [6]),
        ]))
        story.append(link_table)
        story.append(Spacer(1, 0.6 * cm))

        # ── 사용 방법 ──────────────────────────────
        story.append(Paragraph(
            "How to Use This Template",
            ParagraphStyle(
                "SectionTitle",
                fontName="Helvetica-Bold",
                fontSize=13,
                textColor=GRAY_DARK,
                spaceAfter=8,
            ),
        ))

        step_data = []
        for step, instruction in USAGE_INSTRUCTIONS:
            step_data.append([
                Paragraph(
                    f"<b>{step}</b>",
                    ParagraphStyle(
                        "StepLabel",
                        fontName="Helvetica-Bold",
                        fontSize=10,
                        textColor=PURPLE,
                    ),
                ),
                Paragraph(
                    instruction,
                    ParagraphStyle(
                        "StepText",
                        fontName="Helvetica",
                        fontSize=10,
                        textColor=GRAY_DARK,
                        leading=14,
                    ),
                ),
            ])

        steps_table = Table(step_data, colWidths=[2.5 * cm, 14.5 * cm])
        steps_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, GRAY_LIGHT]),
        ]))
        story.append(steps_table)
        story.append(Spacer(1, 0.6 * cm))

        # ── 이용 약관 ──────────────────────────────
        story.append(HRFlowable(width="100%", thickness=1, color=GRAY_LIGHT))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            f"<b>Terms of Use:</b> {TERMS}",
            ParagraphStyle(
                "Terms",
                fontName="Helvetica",
                fontSize=9,
                textColor=GRAY,
                leading=13,
            ),
        ))
        story.append(Spacer(1, 0.3 * cm))

        # ── 푸터 ──────────────────────────────────
        now = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(
            f"Generated on {now}  ·  Thank you for your purchase!",
            ParagraphStyle(
                "Footer",
                fontName="Helvetica",
                fontSize=9,
                textColor=GRAY,
                alignment=TA_CENTER,
            ),
        ))

        return story


# 싱글턴 인스턴스
pdf_service = PDFService()
