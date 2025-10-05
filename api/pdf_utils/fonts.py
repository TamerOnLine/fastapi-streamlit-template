"""
Font utility module for PDF generation.
Includes support for registering Arabic and symbol fonts with fallback options.
"""

from __future__ import annotations

from pathlib import Path
import platform

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .paths import ASSETS

# Optional RTL support
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    AR_OK = True
except Exception:
    AR_OK = False


def rtl(txt: str) -> str:
    """
    Reshapes and reorders Arabic text for correct RTL display if supported.

    Args:
        txt (str): Input text.

    Returns:
        str: Reshaped and reordered text, or original if RTL support is unavailable.
    """
    if not txt:
        return ""
    if AR_OK:
        return get_display(arabic_reshaper.reshape(txt))
    return txt


def register_font_safe(path: Path, name: str, fallback: str = "Helvetica") -> str:
    """
    Registers a TrueType font with a fallback in case of failure.

    Args:
        path (Path): Path to the font file.
        name (str): Name to register the font as.
        fallback (str): Fallback font name.

    Returns:
        str: Registered font name or fallback.
    """
    try:
        if path and path.is_file():
            pdfmetrics.registerFont(TTFont(name, str(path)))
            return name
    except Exception:
        pass
    return fallback


def find_arabic_font() -> tuple[str, Path | None]:
    """
    Attempts to locate a suitable Arabic font.

    Search order:
    1) From project assets.
    2) From common system paths.

    Returns:
        tuple[str, Path | None]: Font name and path or fallback.
    """
    # 1) From assets
    cand = ASSETS / "NotoNaskhArabic-Regular.ttf"
    if cand.exists():
        return "NotoNaskh", cand

    # 2) System paths
    sys = platform.system().lower()
    candidates: list[Path] = []
    if "windows" in sys:
        candidates += [
            Path(r"C:\Windows\Fonts\NotoNaskhArabic-Regular.ttf"),
            Path(r"C:\Windows\Fonts\arial.ttf"),  # Lower quality Arabic fallback
        ]
    elif "linux" in sys:
        candidates += [
            Path("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoNaskhArabicUI-Regular.ttf"),
        ]
    elif "darwin" in sys:  # macOS
        candidates += [
            Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
            Path("/Library/Fonts/NotoNaskhArabic-Regular.ttf"),
        ]

    for p in candidates:
        if p.exists():
            return "NotoNaskh", p

    return "Helvetica", None  # Fallback


def find_symbol_font() -> tuple[str, Path | None]:
    """
    Locates a font for symbols/emojis based on the operating system.

    Returns:
        tuple[str, Path | None]: Font name and path or fallback.
    """
    sys = platform.system().lower()
    if "windows" in sys:
        p = Path(r"C:\Windows\Fonts\seguisym.ttf")
        return "SegoeUISymbol", p if p.exists() else None
    elif "linux" in sys:
        p = Path("/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf")
        return "NotoSansSymbols2", p if p.exists() else None
    elif "darwin" in sys:
        p = Path("/System/Library/Fonts/Supplemental/Apple Symbols.ttf")
        return "AppleSymbols", p if p.exists() else None
    return "Helvetica", None


# Register Arabic font
_AR_NAME, _AR_PATH = find_arabic_font()
AR_FONT = register_font_safe(_AR_PATH, _AR_NAME, fallback="Helvetica")

# Register symbol font
_UI_NAME, _UI_PATH = find_symbol_font()
UI_FONT = register_font_safe(_UI_PATH, _UI_NAME, fallback="Helvetica")
