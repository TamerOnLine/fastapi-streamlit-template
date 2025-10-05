# api/pdf_utils/text.py
"""
🧩 أدوات النصوص العامة في نظام PDF Builder
----------------------------------------
- wrap_text(): تقسيم النص إلى أسطر تناسب العرض المحدد.
- draw_par(): رسم فقرات نصية (مع دعم RTL والخطوط العربية واتصال الحروف).
- draw_label_value(): رسم سطر بشكل (label: value).

يدعم النظام تلقائيًا الخط العربي NotoNaskhArabic عند تفعيل rtl_mode.
"""

from __future__ import annotations
from typing import List, Optional, Iterable

from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import simpleSplit

# ✨ دعم العربية المتصلة + الاتجاه
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _AR_ENABLED = True
except Exception:
    # لو المكتبات غير مثبتة، نعطّل التشكيل ونكمل عادي
    arabic_reshaper = None
    get_display = None
    _AR_ENABLED = False


# ============================================================
# 🧠 المساعدات الأساسية للنصوص
# ============================================================

def _to_text(text_or_lines: str | Iterable[str]) -> str:
    """
    يحول الإدخال إلى نص موحّد.
    يدعم:
    - نص مفرد (str)
    - قائمة أسطر (list[str]) حيث كل عنصر يُعتبر فقرة/سطر.
    """
    if not text_or_lines:
        return ""
    if isinstance(text_or_lines, (list, tuple)):
        return "\n".join(str(x).strip() for x in text_or_lines if str(x).strip())
    return str(text_or_lines)


def wrap_text(text: str, font: str, size: float, max_width: float) -> List[str]:
    """
    تقسيم النص إلى أسطر تناسب العرض المحدد.
    يستخدم simpleSplit لضمان توافق العرض مع الخط الحقيقي.
    """
    text = _to_text(text)
    if not text:
        return []

    try:
        pdfmetrics.getAscentDescent(font, size)
    except Exception:
        font = "Helvetica"

    return simpleSplit(text, font, size, max_width)


# ============================================================
# 🖋️ رسم النصوص العامة
# ============================================================

def _shape_ar_line(line: str) -> str:
    """تشكيل السطر العربي (اتصال الحروف + اتجاه العرض) إن توفرت المكتبات."""
    if not _AR_ENABLED or not line:
        return line
    try:
        return get_display(arabic_reshaper.reshape(line))
    except Exception:
        return line


def draw_par(
    c: canvas.Canvas,
    x: float,
    y: float,
    text: str | Iterable[str],
    font: Optional[str] = None,
    size: float = 10.0,
    max_w: float = 160.0,
    align: str = "left",
    color: Optional[colors.Color] = None,
    leading: float = 14.0,
    para_gap: float = 6.0,
    rtl_mode: bool = False,
    ctx: Optional[dict] = None,
) -> float:
    """
    يرسم فقرة/فقرات نصية بمحاذاة محددة ودعم RTL واتصال الحروف العربية.
    يُعيد قيمة Y بعد الانتهاء.
    """
    text = _to_text(text)
    if not text:
        return y

    is_rtl = bool(rtl_mode or (ctx and ctx.get("rtl_mode")))

    # 🕌 اختيار الخط (عربي / لاتيني)
    if is_rtl:
        font = "NotoNaskhArabic"
    else:
        font = font or "Helvetica"

    # إعداد الخط واللون
    c.setFont(font, size)
    c.setFillColor(color or colors.black)

    # نلف الأسطر قبل الحساب
    lines = wrap_text(text, font, size, max_w)
    if not lines:
        return y

    alg = (align or "left").lower()

    for raw_ln in lines:
        ln = _shape_ar_line(raw_ln) if is_rtl else raw_ln
        w = pdfmetrics.stringWidth(ln, font, size)

        if alg == "center":
            dx = (max_w - w) / 2.0
            draw_x = (x + dx) if not is_rtl else (x + max_w - w - dx)
        elif alg in ("right", "end"):
            draw_x = x + max_w - w
        else:
            draw_x = x if not is_rtl else (x + max_w - w)

        c.drawString(draw_x, y, ln)
        y -= leading

    y -= para_gap
    return y


def draw_label_value(
    c: canvas.Canvas,
    x: float,
    y: float,
    label: str,
    value: str,
    label_font: str = "Helvetica-Bold",
    value_font: str = "Helvetica",
    size: float = 10.0,
    gap: float = 3.0,
    rtl_mode: bool = False,
    ctx: Optional[dict] = None,
) -> float:
    """
    رسم سطر (label: value) مع دعم RTL.
    """
    if not (label or value):
        return y

    is_rtl = bool(rtl_mode or (ctx and ctx.get("rtl_mode")))
    if is_rtl:
        label_font = value_font = "NotoNaskhArabic"

    label = (label or "").strip()
    value = (value or "").strip()

    c.setFont(label_font, size)
    c.setFillColor(colors.black)

    # شكّل النصوص العربية قبل القياس
    label_draw = _shape_ar_line(label) if is_rtl else label
    value_draw = _shape_ar_line(value) if is_rtl else value

    label_w = pdfmetrics.stringWidth(label_draw, label_font, size) if label_draw else 0

    if label_draw:
        c.drawString(x, y, label_draw)

    if value_draw:
        c.setFont(value_font, size)
        draw_x = (x + gap) if is_rtl else (x + label_w + gap)
        c.drawString(draw_x, y, value_draw)

    return y - (size + 2.0)
