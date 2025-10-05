from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Tuple, Optional
from base64 import b64decode

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# من هيكل مشروعك الحالي
from .blocks.base import Frame, RenderContext
from .blocks.registry import get as get_block
from .data_utils import build_ready_from_profile
from .config import UI_LANG


# ---------- أدوات مساعدة ----------
def _decode_avatar_from_profile(profile: Dict[str, Any]) -> Optional[bytes]:
    avatar = (profile or {}).get("avatar") or {}
    b64 = avatar.get("bytes_b64")
    if not b64:
        return None
    try:
        return b64decode(b64.encode("ascii"))
    except Exception:
        return None

def _fallback_columns() -> Dict[str, Tuple[float, float]]:
    return {
        "left":  (16 * mm, 60 * mm),
        "right": (84 * mm, 110 * mm),
    }

def _fallback_layout() -> List[Dict[str, Any]]:
    return [
        {"block_id": "decor_curve",  "col": "right", "data": {"radius_mm": 20, "bar_h_mm": 10, "color": "#EEF2F7"}},
        {"block_id": "avatar_circle","col": "right", "data": {"max_d_mm": 46, "align": "right"}},
        {"block_id": "header_name",  "col": "left",  "data": {"centered": False}},
        {"block_id": "text_section", "col": "left",  "data": {"title": "", "rule": True}, "source": "summary"},
        {"block_id": "key_skills",   "col": "right", "data": {"with_bars": True}},
    ]

def _resolve_layout_and_columns_from_inline(data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Tuple[float, float]]]:
    li = (data or {}).get("layout_inline") or {}
    layout = li.get("layout")
    columns = li.get("columns")

    # columns
    if columns and isinstance(columns, dict):
        cols_xy = {}
        for key in ["left", "right"]:
            col = columns.get(key) or {}
            x = float(col.get("x_mm", 16.0)) * mm
            w = float(col.get("w_mm", 60.0 if key == "left" else 110.0)) * mm
            cols_xy[key] = (x, w)
        cols = cols_xy if len(cols_xy) == 2 else _fallback_columns()
    else:
        cols = _fallback_columns()

    # layout
    if layout and isinstance(layout, list) and any(isinstance(it, dict) and it.get("block_id") for it in layout):
        plan = layout
    else:
        plan = _fallback_layout()

    return plan, cols


# ---------- الدالة الرئيسية (متوافقة مع واجهتين) ----------
def build_resume_pdf(
    data: Optional[Dict[str, Any]] = None,
    *,
    # واجهة قديمة (يستعملها الراوت الحالي لديك)
    layout_plan: Optional[List[Dict[str, Any]]] = None,
    ready: Optional[Dict[str, Any]] = None,
    ui_lang: Optional[str] = None,
    rtl_mode: Optional[bool] = None,
    theme: Optional[str] = None,   # يُتجاهل هنا (التلوين من الثيم غير مفعل في هذا الإصدار)
) -> bytes:
    """
    واجهتان مدعومتان:
    1) الجديدة: build_resume_pdf(data={ "ui_lang":.., "rtl_mode":.., "profile":{...}, "layout_inline":{...} })
    2) القديمة: build_resume_pdf(layout_plan=..., ready=..., ui_lang="en", rtl_mode=False)

    تُعيد bytes لملف PDF.
    """
    # -------- مسار الواجهة الجديدة --------
    if data is not None:
        ui = (data.get("ui_lang") or UI_LANG)
        rtl = bool(data.get("rtl_mode"))
        profile = data.get("profile") or {}

        # حوّل profile إلى ready كما تتوقع البلوكات
        rd = build_ready_from_profile(profile)

        # دعم avatar inline إن وجد
        avatar_bytes = _decode_avatar_from_profile(profile)
        if avatar_bytes:
            prev = rd.get("avatar_circle") or {}
            rd["avatar_circle"] = {**prev, "photo_bytes": avatar_bytes}

        # تخطيط وأعمدة (inline أو fallback)
        plan, cols = _resolve_layout_and_columns_from_inline(data)
        return _render_pdf(plan, rd, ui_lang=ui, rtl_mode=rtl, columns=cols)

    # -------- مسار الواجهة القديمة (المستخدمة حاليًا في الراوت) --------
    # ui, rtl, plan, rd قادمة من الراوت
    ui = ui_lang or UI_LANG
    rtl = bool(rtl_mode)
    rd = ready or {}
    plan = layout_plan or _fallback_layout()
    cols = _fallback_columns()
    return _render_pdf(plan, rd, ui_lang=ui, rtl_mode=rtl, columns=cols)


# ---------- قلب الرسم ----------
def _render_pdf(
    layout_plan: List[Dict[str, Any]],
    ready: Dict[str, Any],
    *,
    ui_lang: str,
    rtl_mode: bool,
    columns: Dict[str, Tuple[float, float]],  # {"left": (x,w), "middle": (x,w), "right": (x,w), ...}
) -> bytes:
    PAGE_W, PAGE_H = A4
    top_margin = 16 * mm
    bottom_margin = 16 * mm

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    # حضّر Y لكل عمود ديناميكيًا
    col_state: Dict[str, Dict[str, float]] = {}
    for cid, (x, w) in columns.items():
        col_state[cid] = {"x": x, "w": w, "y": PAGE_H - top_margin}

    ctx: RenderContext = {
        "ui_lang": ui_lang,
        "rtl_mode": rtl_mode,
        "page_top_y": PAGE_H - top_margin,
        "page_h": PAGE_H,
    }

    for item in (layout_plan or []):
        bid = (item or {}).get("block_id")
        cid = (item or {}).get("col") or "right"  # اسم العمود المطلوب
        custom = (item or {}).get("data") or {}
        if not bid:
            continue

        # احصل على بلوك
        try:
            block = get_block(bid)  # instance من registry
        except KeyError:
            continue

        # بيانات البلوك: ready + تخصيص layout
        base_data = ready.get(bid) or {}
        block_data = {**base_data, **custom} if custom else base_data

        # اختَر عمودًا: لو غير موجود، اسقط على "right" أو أول عمود متاح
        if cid not in col_state:
            cid = "right" if "right" in col_state else next(iter(col_state))

        x, w, y = col_state[cid]["x"], col_state[cid]["w"], col_state[cid]["y"]
        frame = Frame(x=x, y=y, w=w)
        new_y = block.render(c, frame, block_data, ctx)

        # حدّث Y للعمود مع احترام الحد الأدنى
        col_state[cid]["y"] = max(bottom_margin, new_y)

    c.showPage()
    c.save()
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

