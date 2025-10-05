from __future__ import annotations
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from reportlab.lib.units import mm

from ..config import UI_LANG
from .base import Frame, RenderContext
from .registry import register

class HeaderBar:
    BLOCK_ID = "header_bar"
    """
    شريط علوي بعرض العمود مع عنوان واختياريًا دائرة بالحروف الأولية.
    data:
      - bg            : لون الخلفية (افتراضي "#FF5A5F")
      - title_on_bar  : bool
      - title         : نص العنوان
      - initials      : حروف أولية داخل دائرة (اختياري)
      - pad_mm        : حافة داخلية عمودية (افتراضي 4)
      - height_mm     : ارتفاع الشريط (افتراضي 16)
      - y_from_top_mm : كم ننزل من أعلى الصفحة (افتراضي 0)
    """

    def render(self, c: Canvas, frame: Frame, data: dict, ctx: RenderContext) -> float:
        bg = colors.HexColor(data.get("bg", "#FF5A5F"))
        pad = float(data.get("pad_mm", 4)) * mm
        title_on_bar = bool(data.get("title_on_bar", True))
        title = (data.get("title") or "").strip()
        initials = (data.get("initials") or "").strip()
        bar_h = float(data.get("height_mm", 16)) * mm
        y_from_top = float(data.get("y_from_top_mm", 0)) * mm

        page_top_y = ctx.get("page_top_y", frame.y)
        bar_top_y = page_top_y - y_from_top

        # خلفية الشريط
        c.setFillColor(bg)
        c.rect(frame.x, bar_top_y - bar_h, frame.w, bar_h, fill=True, stroke=False)

        # عنوان فوق الشريط
        if title_on_bar and title:
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(frame.x + 6 * mm, bar_top_y - 6 * mm - pad, title)

        # دائرة الحروف الأولية (اختياري)
        if initials:
            d = 18 * mm
            cx = frame.x + d / 2 + 4 * mm
            cy = bar_top_y - bar_h / 2
            c.setFillColor(colors.white)
            c.circle(cx, cy, d / 2, stroke=False, fill=True)
            c.setFillColor(bg)
            c.setFont("Helvetica-Bold", 12)
            tw = c.stringWidth(initials, "Helvetica-Bold", 12)
            c.drawString(cx - tw / 2, cy - 4, initials)

        return frame.y

register(HeaderBar())
