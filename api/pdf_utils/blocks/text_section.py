from __future__ import annotations
from reportlab.lib import colors
from ..config import *
from ..text import draw_par
from ..icons import draw_heading_with_icon
from .base import Frame, RenderContext
from .registry import register

class TextSectionBlock:
    BLOCK_ID = "text_section"

    def render(self, c, frame: Frame, data: dict, ctx: RenderContext) -> float:
        title = (data.get("title") or "").strip()
        lines = [str(x).strip() for x in (data.get("lines") or []) if str(x).strip()]
        if not title or not lines: return frame.y

        y = draw_heading_with_icon(
            c=c, x=frame.x, y=frame.y, title=title, icon=None,
            font="Helvetica-Bold", size=RIGHT_SEC_HEADING_SIZE, color=HEADING_COLOR,
            underline_w=frame.w, rule_color=RIGHT_SEC_RULE_COLOR, rule_width=RIGHT_SEC_RULE_WIDTH,
            gap_below=GAP_AFTER_HEADING / 2,
        )
        y -= RIGHT_SEC_RULE_TO_TEXT_GAP

        c.setFont("Helvetica", RIGHT_SEC_TEXT_SIZE); c.setFillColor(colors.black)
        y = draw_par(c, frame.x, y, lines, "Helvetica", RIGHT_SEC_TEXT_SIZE,
                     frame.w, "left", False, BODY_LEADING, RIGHT_SEC_PARA_GAP)
        y -= RIGHT_SEC_SECTION_GAP
        return y

register(TextSectionBlock())
