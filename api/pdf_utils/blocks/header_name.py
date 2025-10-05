from __future__ import annotations
from typing import Any
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

from .base import Frame, RenderContext
from .registry import register
from ..config import NAME_SIZE, HEADING_COLOR, NAME_GAP


class HeaderNameBlock:
    """
    Block: header_name
    data options:
      - name: str (required)
      - centered: bool = True
      - highlight_bg: str | None = "#E0F2FE"        # لون الخلفية (Hex) لبار الهيدر
      - font_size: float | None (default = NAME_SIZE من config)
      - box_h_mm: float = 30                        # ارتفاع شريط الخلفية بالـ mm عند تفعيله
      - inner_offset_mm: float = 10                 # إزاحة النص عموديًا داخل الشريط (mm)
      - pad_mm: float = 4                           # مسافة طفيفة إضافية أسفل الشريط (mm)
    """
    BLOCK_ID = "header_name"

    def render(self, c: Canvas, frame: Frame, data: dict, ctx: RenderContext) -> float:
        name = (data or {}).get("name") or ""
        if not name:
            return frame.y

        centered = bool((data or {}).get("centered", True))
        font_size = float((data or {}).get("font_size", NAME_SIZE))

        # خصائص الشريط الخلفي (اختيارية)
        highlight_bg: str | None = (data or {}).get("highlight_bg")
        box_h_mm = float((data or {}).get("box_h_mm", 30))
        inner_offset_mm = float((data or {}).get("inner_offset_mm", 10))
        pad_mm = float((data or {}).get("pad_mm", 4))

        y_top = frame.y
        baseline_y: float
        next_y: float

        if highlight_bg:
            # نرسم شريط خلفية بعرض الإطار
            box_h = box_h_mm * mm
            pad = pad_mm * mm
            # نجعل الشريط يبدأ قليلاً أسفل y_top لتوفير مسافة علوية لطيفة
            # y_next: الموضع التالي بعد الشريط
            next_y = y_top - box_h - pad

            c.saveState()
            try:
                c.setFillColor(colors.HexColor(highlight_bg))
            except Exception:
                c.setFillColor(colors.HexColor("#E0F2FE"))
            c.setStrokeColor(colors.transparent)
            c.rect(frame.x, next_y + pad, frame.w, box_h, fill=1, stroke=0)
            c.restoreState()

            # خط الأساس للنص داخل الشريط
            baseline_y = next_y + (inner_offset_mm * mm)
        else:
            # السلوك القديم: نكتب الاسم عند y كما هو، ثم نهبط NAME_GAP
            baseline_y = y_top
            next_y = y_top - NAME_GAP

        # نص الاسم
        c.setFillColor(HEADING_COLOR)
        c.setFont("Helvetica-Bold", font_size)
        if centered:
            c.drawCentredString(frame.x + frame.w / 2.0, baseline_y, name)
        else:
            # محاذاة يسار مع مسافة صغيرة داخل الإطار
            c.drawString(frame.x, baseline_y, name)

        # إن كان لدينا شريط خلفي، نعطي مسافة بسيطة إضافية أسفله
        if highlight_bg:
            return next_y - (2 * mm)
        return next_y


register(HeaderNameBlock())
