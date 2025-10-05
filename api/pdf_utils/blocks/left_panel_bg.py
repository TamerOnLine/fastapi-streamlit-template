# api/pdf_utils/blocks/left_panel_bg.py
from __future__ import annotations
from reportlab.lib.units import mm
from reportlab.lib import colors
from .base import Frame, RenderContext
from .registry import register
from ..config import LEFT_BG, LEFT_BORDER, CARD_PAD
from ..shapes import draw_round_rect

class LeftPanelBG:
    BLOCK_ID = "left_panel_bg"

    def render(self, c, frame: Frame, data: dict, ctx: RenderContext) -> float:
        # يرسم لوحة ممتدة من أعلى الصفحة لأسفلها ضمن عرض العمود الأيسر
        # نفترض أن y في البداية = top، ونريد تغطية العمود كله: نستخدم ارتفاع كبير
        pad = data.get("pad_mm", 4) * mm if data else 4 * mm
        x = frame.x - pad
        w = frame.w + 2 * pad
        # استخدم ارتفاع الصفحة من CurrentFrame في ctx إن توفر (سنمرّره لاحقاً)
        page_h = ctx.get("page_h") or (297 * mm)  # A4 default fallback
        top_y = ctx.get("page_top_y") or frame.y
        h = (top_y - (20 * mm))  # تقريبي لتحت؛ يمكن ضبطه حسب احتياجك

        c.saveState()
        c.setFillColor(LEFT_BG or colors.HexColor("#F7F8FA"))
        c.setStrokeColor(LEFT_BORDER or colors.HexColor("#E3E6EA"))
        draw_round_rect(c, x, top_y - h, w, h, r=6, fill=1, stroke=0)
        c.restoreState()
        return frame.y  # لا نغيّر Y للكتل التالية

register(LeftPanelBG())
