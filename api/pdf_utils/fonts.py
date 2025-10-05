from __future__ import annotations
from importlib.resources import files
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ============================================================
# 🧩 مسارات ملفات الخطوط داخل الحزمة
# ============================================================
ASSETS = files("api.pdf_utils.assets")
FONT_PATH_NOTO = ASSETS / "NotoNaskhArabic-Regular.ttf"
FONT_PATH_AMIRI = ASSETS / "Amiri-Regular.ttf"   # قد تكون AmiriQuran حسب ما تم تنزيله

# ============================================================
# 🎨 أسماء الخطوط داخل ReportLab
# ============================================================
AR_FONT = "NotoNaskhArabic"
AR_FONT_FALLBACK = "Amiri"

# ============================================================
# 🧠 دوال مساعدة
# ============================================================
def rtl(text: str) -> str:
    """
    واجهة مطلوبة من text.py.
    حالياً تُعيد النص كما هو (بدون تشكيل/إعادة ترتيب).
    لاحقاً يمكن تفعيل arabic_reshaper + python-bidi إن رغبت.
    """
    return text or ""

def _register_ttf_font(name: str, path_str: str) -> None:
    pdfmetrics.registerFont(TTFont(name, path_str))

# ============================================================
# ⚙️ تسجيل الخطوط مع fallback آمن
# ============================================================
def ensure_fonts() -> None:
    """
    نسجّل خط Noto Naskh أولاً، ثم Amiri كبديل.
    لو فشل الاثنان، نستخدم خطاً مدمجاً في ReportLab لضمان عدم تعطل السيرفر.
    """
    global AR_FONT

    # جرّب Noto Naskh
    try:
        _register_ttf_font(AR_FONT, str(FONT_PATH_NOTO))
        print(f"✅ Registered Arabic font: {AR_FONT}")
        return
    except Exception as e:
        print(f"⚠️ Failed to register {AR_FONT}: {e}")

    # جرّب Amiri
    try:
        _register_ttf_font(AR_FONT_FALLBACK, str(FONT_PATH_AMIRI))
        AR_FONT = AR_FONT_FALLBACK
        print(f"✅ Fallback font registered: {AR_FONT_FALLBACK}")
        return
    except Exception as e:
        print(f"⚠️ Failed to register fallback font {AR_FONT_FALLBACK}: {e}")

    # آخر حل: خط مدمج (لن يعرض العربية بشكل مثالي لكنه يمنع الانهيار)
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
        AR_FONT = "HeiseiMin-W3"
        print("🟡 Using built-in fallback font (HeiseiMin-W3)")
    except Exception as e:
        # كمل بدون تسجيل (نادر جداً)
        print(f"❌ Could not register any font: {e}")

# نفّذ التسجيل عند الاستيراد
ensure_fonts()

__all__ = ["AR_FONT", "rtl", "ensure_fonts"]
