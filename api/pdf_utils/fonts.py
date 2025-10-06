from __future__ import annotations

from importlib.resources import files
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ============================================================
# Font file paths within the package
# ============================================================
ASSETS = files("api.pdf_utils.assets")
FONT_PATH_NOTO = ASSETS / "NotoNaskhArabic-Regular.ttf"
FONT_PATH_AMIRI = ASSETS / "Amiri-Regular.ttf"  # Could be AmiriQuran depending on download

# ============================================================
# Font names used within ReportLab
# ============================================================
AR_FONT = "NotoNaskhArabic"
AR_FONT_FALLBACK = "Amiri"

# ============================================================
# Helper functions
# ============================================================
def rtl(text: str) -> str:
    """
    Return the input text as-is. This is a placeholder for RTL text reshaping
    and bidirectional support, which can be enabled with arabic_reshaper and python-bidi.

    Args:
        text (str): Input Arabic text.

    Returns:
        str: The unmodified input text, or an empty string if None.
    """
    return text or ""

def _register_ttf_font(name: str, path_str: str) -> None:
    """
    Register a TrueType font with ReportLab.

    Args:
        name (str): The name to register the font under.
        path_str (str): File path to the .ttf font.
    """
    pdfmetrics.registerFont(TTFont(name, path_str))

# ============================================================
# Font registration with safe fallback
# ============================================================
def ensure_fonts() -> None:
    """
    Attempt to register Arabic fonts with ReportLab. Tries to register Noto Naskh first,
    then Amiri as a fallback. If both fail, attempts to register a built-in Unicode font
    to avoid server crashes.

    Modifies:
        AR_FONT (str): Global variable may be updated to fallback font name.
    """
    global AR_FONT

    try:
        _register_ttf_font(AR_FONT, str(FONT_PATH_NOTO))
        print(f"Registered Arabic font: {AR_FONT}")
        return
    except Exception as e:
        print(f"Failed to register {AR_FONT}: {e}")

    try:
        _register_ttf_font(AR_FONT_FALLBACK, str(FONT_PATH_AMIRI))
        AR_FONT = AR_FONT_FALLBACK
        print(f"Fallback font registered: {AR_FONT_FALLBACK}")
        return
    except Exception as e:
        print(f"Failed to register fallback font {AR_FONT_FALLBACK}: {e}")

    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
        AR_FONT = "HeiseiMin-W3"
        print("Using built-in fallback font (HeiseiMin-W3)")
    except Exception as e:
        print(f"Could not register any font: {e}")

# Register fonts upon import
ensure_fonts()

__all__ = ["AR_FONT", "rtl", "ensure_fonts"]
