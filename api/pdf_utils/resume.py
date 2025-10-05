# api/pdf_utils/resume.py
"""
Main function for generating a resume PDF using ReportLab,
driven 100% by a Blocks registry + a themeable layout_plan.

Supports:
- Frames: "left" | "right" | {"x": float|token, "y": float|token, "w": float|token}
- Page geometry from theme.page (margins_mm, left_col_mm, gap_mm, left_panel_bg)
"""

from __future__ import annotations

from io import BytesIO
from typing import List, Dict, Any, Tuple

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from .config import *  # UI_LANG, CARD_PAD, GAP_AFTER_HEADING, colors...
from .shapes import draw_round_rect
from .blocks import Frame, RenderContext, get  # registry + types
from .theme_loader import get_page_cfg  # ← نقرأ page من الثيم


def build_resume_pdf(
    *,
    layout_plan: List[Dict[str, Any]],   # REQUIRED
    ui_lang: str | None = None,
    rtl_mode: bool = False,
    # اختياري لو أردت تمرير الثيم كاملًا مستقبلًا
    theme: Dict[str, Any] | None = None,
) -> bytes:
    """
    Generate PDF purely from `layout_plan` (+ theme-aware page geometry).

    layout_plan item example:
        {
          "block_id": "header_name",
          "frame": "left" | "right" | {"x": ..., "y": ..., "w": ...},
          "data": {...}
        }
    """
    if not layout_plan or not isinstance(layout_plan, list):
        raise ValueError("blocks-only mode requires a non-empty `layout_plan` list.")

    # ---------- PDF setup ----------
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    PAGE_W, PAGE_H = A4

    # ---------- Page geometry from theme ----------
    page_cfg = get_page_cfg(theme or {})  # يقرأ theme["page"] إن وجد
    marg = (page_cfg.get("margins_mm") or {})
    top_mm    = float(marg.get("top", 16))
    right_mm  = float(marg.get("right", 16))
    bottom_mm = float(marg.get("bottom", 16))
    left_mm   = float(marg.get("left", 16))
    gap_mm    = float(page_cfg.get("gap_mm", 8))
    left_col_mm = float(page_cfg.get("left_col_mm", 62))
    draw_left_panel = bool(page_cfg.get("left_panel_bg"))

    # حواف وإحداثيات عامة
    page_left   = left_mm * mm
    page_right  = PAGE_W - right_mm * mm
    page_top    = PAGE_H - top_mm * mm
    page_bottom = bottom_mm * mm

    # هندسة الأعمدة
    left_x = page_left
    left_w = left_col_mm * mm
    right_x = left_x + left_w + (gap_mm * mm)
    right_w = max(0.0, page_right - right_x)

    # ---------- اختياري: لوح خلفية العمود الأيسر ----------
    # في التصميم القديم كان يتعادل مع "كرت" يسار. الآن نجعله اختياريًا من الثيم.
    if draw_left_panel and left_w > 0:
        # نرسم لوحة تمتد من أعلى الصفحة لأسفلها ضمن هوامش الصفحة
        card_x, card_y = left_x, page_bottom
        card_w, card_h = left_w, (PAGE_H - top_mm * mm) - page_bottom
        # يمكنك تلوينها في Block مخصص (left_panel_bg)؛ هنا حافظنا على مستطيل خفيف:
        draw_round_rect(c, card_x, card_y, card_w, card_h)

    # إطارات المحتوى الابتدائية
    left_content_start_y  = page_top - CARD_PAD
    right_content_start_y = page_top - GAP_AFTER_HEADING

    # ---------- Render context ----------
    ctx: RenderContext = {
        "rtl_mode": rtl_mode,
        "ui_lang": ui_lang or UI_LANG,
        "page_h": PAGE_H,
        "page_top_y": page_top,
        # نمرر أيضًا theme إذا أردت استخدامه داخل بلوكات مستقبلًا
        "theme": theme or {},
    }

    # مؤشرات Y حيّة لكل ممر (عمود)
    y_for = {
        "left":  left_content_start_y,
        "right": right_content_start_y,
    }

    # ---------- دالة تفسير frame ----------
    def _token_value(token: str) -> float:
        """Resolve symbolic tokens like 'left.x', 'right.w', 'page.top'."""
        token = (token or "").strip()
        mapping = {
            "left.x": left_x, "left.w": left_w, "left.y": y_for["left"],
            "right.x": right_x, "right.w": right_w, "right.y": y_for["right"],
            "page.left": page_left, "page.right": page_right,
            "page.top": page_top, "page.bottom": page_bottom,
        }
        return float(mapping.get(token, 0.0))

    def _val(v: Any, fallback: float) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            return _token_value(v)
        return float(fallback)

    def resolve_frame(frame_spec: Any) -> Tuple[Frame, str | None]:
        """
        Returns (Frame, lane)
        lane in {"left","right",None} لتحديث مؤشر Y عند الحاجة.
        """
        if frame_spec == "left":
            return Frame(x=left_x, y=y_for["left"], w=left_w), "left"
        if frame_spec == "right":
            return Frame(x=right_x, y=y_for["right"], w=right_w), "right"
        if isinstance(frame_spec, dict):
            fx = _val(frame_spec.get("x"), right_x)
            fy = _val(frame_spec.get("y"), page_top)
            fw = _val(frame_spec.get("w"), right_w)
            return Frame(x=fx, y=fy, w=fw), None
        # fallback: اعتبرها يمين
        return Frame(x=right_x, y=y_for["right"], w=right_w), "right"

    # ---------- الرسم وفق layout_plan ----------
    for item in layout_plan:
        if not isinstance(item, dict):
            continue

        bid = item.get("block_id")
        if not bid:
            continue

        frame_spec = item.get("frame", "right")
        data = item.get("data") or {}

        block = get(bid)  # registry fetch; raises if unknown

        frame, lane = resolve_frame(frame_spec)

        # ارسم البلوك
        new_y = block.render(c, frame, data, ctx)

        # لو البلوك كان على left/right حدّث مؤشر Y
        if lane in ("left", "right"):
            y_for[lane] = new_y

    # ---------- finalize ----------
    c.showPage()
    c.save()
    out = buffer.getvalue()
    buffer.close()
    return out
