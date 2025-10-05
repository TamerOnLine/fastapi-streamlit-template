from __future__ import annotations
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from ..config import *
from ..fonts import AR_FONT
from ..labels import t
from ..icons import get_section_icon, draw_heading_with_icon
from ..text import draw_par
from .base import Frame, RenderContext
from .registry import register

class ProjectsBlock:
    BLOCK_ID = "projects"

    def render(self, c, frame: Frame, data: dict, ctx: RenderContext) -> float:
        items = []
        for tpl in (data.get("items") or []):
            title = (tpl[0] or "").strip(); desc = (tpl[1] or "").strip()
            link  = (tpl[2] or "").strip() if len(tpl) > 2 and tpl[2] else None
            if title or desc or link: items.append((title, desc, link))
        if not items: return frame.y

        title = (data.get("title") or t("selected_projects", ctx.get("ui_lang") or UI_LANG))
        y = draw_heading_with_icon(
            c=c, x=frame.x, y=frame.y, title=title, icon=get_section_icon("selected_projects"),
            font="Helvetica-Bold", size=HEADING_SIZE, color=HEADING_COLOR,
            underline_w=frame.w, rule_color=RIGHT_SEC_RULE_COLOR, rule_width=RIGHT_SEC_RULE_WIDTH,
            gap_below=GAP_AFTER_HEADING / 2,
        )
        y -= RIGHT_SEC_RULE_TO_TEXT_GAP

        rtl_mode = bool(ctx.get("rtl_mode"))
        for (ptitle, desc, link) in items:
            c.setFont("Helvetica-Bold", PROJECT_TITLE_SIZE); c.setFillColor(SUBHEAD_COLOR)
            c.drawString(frame.x, y, ptitle)
            y -= PROJECT_TITLE_GAP_BELOW

            c.setFillColor(colors.black)
            y = draw_par(
                c=c, x=frame.x, y=y,
                lines=(desc or "").split("\n"),
                font=(AR_FONT if rtl_mode else "Helvetica"), size=TEXT_SIZE,
                max_w=frame.w, align=("right" if rtl_mode else "left"),
                rtl_mode=rtl_mode, leading=PROJECT_DESC_LEADING,
            )

            y -= PROJECT_LINK_GAP_ABOVE
            if link:
                font_name = "Helvetica-Oblique"
                c.setFont(font_name, PROJECT_LINK_TEXT_SIZE); c.setFillColor(HEADING_COLOR)
                link_text = f"Repo: {link}"
                c.drawString(frame.x, y, link_text)
                tw  = pdfmetrics.stringWidth(link_text, font_name, PROJECT_LINK_TEXT_SIZE)
                asc = pdfmetrics.getAscent(font_name)/1000.0*PROJECT_LINK_TEXT_SIZE
                dsc = abs(pdfmetrics.getDescent(font_name))/1000.0*PROJECT_LINK_TEXT_SIZE
                c.linkURL(link, (frame.x, y - dsc, frame.x + tw, y + asc*0.2), relative=0, thickness=0)
            y -= PROJECT_BLOCK_GAP
        return y

register(ProjectsBlock())
