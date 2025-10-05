from __future__ import annotations
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from reportlab.lib.units import mm

from ..config import UI_LANG
from .base import Frame, RenderContext
from .registry import register

class LinksInline:
    BLOCK_ID = "links_inline"
    """
    سطر روابط متتالية يفصلها ' · '
    data:
      - items     : list[str]
      - accent    : لون النص (افتراضي "#0A7D55")
      - font_size : حجم الخط (افتراضي 9)
      - gap_mm    : مسافة رأسية بعد السطر (افتراضي 8)
    """

    def render(self, c: Canvas, frame: Frame, data: dict, ctx: RenderContext) -> float:
        items = [str(v).strip() for v in (data.get("items") or []) if str(v).strip()]
        accent = colors.HexColor(data.get("accent", "#0A7D55"))
        font_size = float(data.get("font_size", 9))
        gap = float(data.get("gap_mm", 8)) * mm

        if not items:
            return frame.y

        text = " · ".join(items)
        c.setFillColor(accent)
        c.setFont("Helvetica", font_size)
        c.drawString(frame.x, frame.y - 4 * mm, text)

        return frame.y - gap

register(LinksInline())
