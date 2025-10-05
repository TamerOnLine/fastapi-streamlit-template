# api/pdf_utils/resume.py
"""
🔧 Resume PDF Builder
يبني ملف PDF استنادًا إلى كتل (Blocks) وخطة تخطيط (layout plan)
مع دعم الثيمات الديناميكية (Dynamic Themes) واللغات (LTR/RTL).
"""

from __future__ import annotations
from io import BytesIO
from typing import Dict, Any, List, Tuple, Optional

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# استيرادات من مشروعك
from .blocks.base import Frame, RenderContext
from .blocks.registry import get as get_block
from .data_utils import build_ready_from_profile
from .config import UI_LANG

# الثيم الديناميكي
from .theme_loader import load_and_apply

# 🛡️ شبكة الأمان لتوحيد أسماء البلوكات (pprojects→projects…)
from .block_aliases import canonicalize


# ---------------------------------------------------------------------------
# إعدادات الصفحة الافتراضية
PAGE_W, PAGE_H = A4
LEFT_MARGIN = 18 * mm
RIGHT_MARGIN = 18 * mm
TOP_MARGIN = 22 * mm
BOTTOM_MARGIN = 18 * mm


# ---------------------------------------------------------------------------
def build_resume_pdf(
    data: Optional[Dict[str, Any]] = None,
    *,
    layout_plan: Optional[List[Dict[str, Any]]] = None,
    ready: Optional[Dict[str, Any]] = None,
    ui_lang: Optional[str] = None,
    rtl_mode: Optional[bool] = None,
    theme_name: Optional[str] = None,
    theme: Optional[str] = None,  # back-compat: اسم الثيم القديم
) -> bytes:
    """
    🧾 يبني ملف PDF ويعيده على شكل bytes.

    يمكن استدعاؤه بطريقتين:
      1️⃣ عبر الواجهة الجديدة: data تحتوي ui_lang وrtl_mode وprofile (+ layout_inline)
      2️⃣ عبر الواجهة القديمة: layout_plan وready تمرَّر مباشرة

    - theme_name: اسم ملف JSON داخل مجلد themes/ بدون الامتداد.
    """

    # توافق للخلفية مع الوسيط القديم
    if theme and not theme_name:
        theme_name = theme

    # ---------------------------
    # 📦 المسار الجديد (من واجهة Streamlit / الراوت الجديد)
    # ---------------------------
    if data is not None:
        ui = (data.get("ui_lang") or UI_LANG)
        rtl = bool(data.get("rtl_mode"))
        profile = data.get("profile") or {}

        # ✅ تحميل وتطبيق الثيم
        tn = theme_name or data.get("theme_name") or "default"
        theme_dict = load_and_apply(tn)

        # بناء البيانات الجاهزة للكتل
        rd = build_ready_from_profile(profile)

        # استخراج التخطيط والأعمدة (مع التطبيع)
        plan, cols = _resolve_layout_and_columns_from_inline(data)

        return _render_pdf(
            plan,
            rd,
            ui_lang=ui,
            rtl_mode=rtl,
            columns=cols,
            theme=theme_dict,
        )

    # ---------------------------
    # 📦 المسار القديم (توافق)
    # ---------------------------
    ui = ui_lang or UI_LANG
    rtl = bool(rtl_mode)
    rd = ready or {}
    plan = layout_plan or _fallback_layout()
    cols = _fallback_columns()

    # ✅ تحميل الثيم حتى في المسار القديم
    tn = theme_name or "default"
    theme_dict = load_and_apply(tn)

    return _render_pdf(
        plan,
        rd,
        ui_lang=ui,
        rtl_mode=rtl,
        columns=cols,
        theme=theme_dict,
    )


# ---------------------------------------------------------------------------
def _render_pdf(
    layout_plan: List[Dict[str, Any]] | Dict[str, Any],
    ready: Dict[str, Any],
    *,
    ui_lang: str,
    rtl_mode: bool,
    columns: Dict[str, Tuple[float, float]],
    theme: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    يرسم كل الكتل داخل الصفحة بناءً على خطة التخطيط layout_plan
    """

    # --- تطبيع المدخل: لو وصل dict خذ منه "layout"، وحوّل النصوص إلى كائنات ---
    if isinstance(layout_plan, dict):
        layout_plan = layout_plan.get("layout", [])

    fixed_plan: List[Dict[str, Any]] = []
    for it in layout_plan or []:
        if isinstance(it, dict) and it.get("block_id"):
            fixed_plan.append(it)
        elif isinstance(it, str) and it.strip():
            fixed_plan.append({"block_id": it.strip()})
        else:
            print(f"[⚠️] Skipping invalid layout item in _render: {it!r}")

    layout_plan = fixed_plan

    # 🛡️ شبكة أمان وقت التشغيل: طبّق aliases (pprojects→projects، educatioon→education، …)
    for it in layout_plan:
        it["block_id"] = canonicalize(it["block_id"])

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    # إعداد السياق العام للصفحة
    ctx: RenderContext = {
        "ui_lang": ui_lang,
        "rtl_mode": rtl_mode,
        "page_top_y": PAGE_H - TOP_MARGIN,
        "page_h": PAGE_H,
        "theme": theme or {},
        # يمكنك إضافة مفاتيح أخرى من التخطيط (frames/page) إن رغبت لاحقًا
    }

    # تنفيذ الكتل واحدة تلو الأخرى حسب الخطة
    for block_conf in layout_plan:
        try:
            block_id = block_conf.get("block_id")
            block = get_block(block_id)

            frame_dict = block_conf.get("frame") or {}
            frame = Frame(
                x=float(frame_dict.get("x", LEFT_MARGIN)),
                y=float(frame_dict.get("y", PAGE_H - TOP_MARGIN)),
                w=float(frame_dict.get("w", PAGE_W - LEFT_MARGIN - RIGHT_MARGIN)),
            )

            # بيانات البلوك: من ready أولاً ثم من layout_conf
            block_data = ready.get(block_id) or block_conf.get("data") or {}

            # رسم البلوك فعليًا
            new_y = block.render(c, frame, block_data, ctx)

            # تحديث y في حال استخدم لاحقًا
            frame.y = new_y

        except Exception as e:
            print(f"[⚠️] Block '{block_conf.get('block_id') if isinstance(block_conf, dict) else block_conf}' failed: {e}")
            continue

    # إنهاء الصفحة
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 🧱 أدوات داخلية (للتوافق مع نظام التخطيط)
# ---------------------------------------------------------------------------

def _resolve_layout_and_columns_from_inline(data: Dict[str, Any]):
    """
    يحدّد التخطيط من البيانات القادمة من الراوت.
    يدعم:
      - data["layout_inline"] كـ dict يحتوي "layout"/"frames"/"page"
      - أو كـ list مباشرة
    ويُعيد دائمًا قائمة layout مناسبة للرسم.
    """
    li = data.get("layout_inline")
    if li is None:
        # لا يوجد تخطيط: استخدم الاحتياطي
        plan = _fallback_layout()
        cols = _fallback_columns()
        return plan, cols

    # إذا جاء كـ dict: استخرج القائمة من "layout"
    if isinstance(li, dict):
        plan = li.get("layout") or []
    elif isinstance(li, list):
        plan = li
    else:
        plan = _fallback_layout()

    # طبيع (normalize): حوّل العناصر النصية إلى dict block_id
    norm_plan: List[Dict[str, Any]] = []
    for it in plan:
        if isinstance(it, dict) and it.get("block_id"):
            norm_plan.append(it)
        elif isinstance(it, str) and it.strip():
            norm_plan.append({"block_id": it.strip()})
        else:
            # تجاهل المدخل غير الصالح
            print(f"[⚠️] Skipping invalid layout item in _resolve: {it!r}")

    # 🛡️ طبّق aliases مبكرًا أيضًا (حماية مزدوجة)
    for it in norm_plan:
        it["block_id"] = canonicalize(it["block_id"])

    cols = _fallback_columns()
    return norm_plan, cols


def _fallback_layout() -> List[Dict[str, Any]]:
    """
    تخطيط احتياطي بسيط في حال غياب ملف layout.
    """
    return [
        {
            "block_id": "header_name",
            "frame": {"x": LEFT_MARGIN, "y": PAGE_H - TOP_MARGIN, "w": PAGE_W - LEFT_MARGIN - RIGHT_MARGIN},
            "data": {"centered": True, "highlight_bg": "#E0F2FE", "box_h_mm": 30},
        },
        {"block_id": "key_skills", "frame": {"x": LEFT_MARGIN, "y": PAGE_H - 60 * mm, "w": 80 * mm}},
        {"block_id": "projects", "frame": {"x": 110 * mm, "y": PAGE_H - 60 * mm, "w": 85 * mm}},
    ]


def _fallback_columns() -> Dict[str, Tuple[float, float]]:
    """
    يحدّد أعمدة احتياطية (عمودين).
    """
    total_w = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN
    left_w = total_w * 0.4
    right_w = total_w * 0.55
    return {
        "left": (LEFT_MARGIN, left_w),
        "right": (LEFT_MARGIN + left_w + 5 * mm, right_w),
    }
