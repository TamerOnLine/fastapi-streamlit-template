from __future__ import annotations
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfgen import pathobject
from reportlab.lib import colors
from reportlab.lib.units import mm

from ..config import UI_LANG  # احتياطي لو احتجته لاحقًا
from .base import Frame, RenderContext
from .registry import register

class DecorCurveBlock:
    BLOCK_ID = "decor_curve"
    """
    بلوك زخرفي: شريط علوي خفيف + ركن منحني في أعلى يمين العمود.
    data:
      - radius_mm   : نصف قطر الانحناء (افتراضي 18)
      - bar_h_mm    : ارتفاع الشريط (افتراضي 10)
      - color       : لون التعبئة (افتراضي "#EEF2F7")
      - y_offset_mm : كم ننزل من أعلى الصفحة (افتراضي 0)
    """

    def render(self, c: Canvas, frame: Frame, data: dict, ctx: RenderContext) -> float:
        radius = float(data.get("radius_mm", 18)) * mm
        bar_h  = float(data.get("bar_h_mm", 10)) * mm
        col    = colors.HexColor(data.get("color", "#EEF2F7"))
        y_off  = float(data.get("y_offset_mm", 0)) * mm

        # أعلى الصفحة (من السياق) ثم ننزل بمقدار y_off
        page_top_y = ctx.get("page_top_y", frame.y)
        bar_top_y = page_top_y - y_off

        # شريط أعلى العمود
        c.setFillColor(col)
        c.rect(frame.x, bar_top_y - bar_h, frame.w, bar_h, fill=True, stroke=False)

        # ركن منحني (ربع دائرة) عند أعلى يمين العمود
        px = frame.x + frame.w - radius
        py = bar_top_y - bar_h / 2
        p: pathobject.PDFPathObject = c.beginPath()
        p.moveTo(px, py)
        p.arc(px - radius, py - radius, px + radius, py + radius, startAng=0, extent=90)
        p.lineTo(px, py)
        c.drawPath(p, fill=True, stroke=False)

        # لا نستهلك من تدفّق العمود
        return frame.y

register(DecorCurveBlock())
