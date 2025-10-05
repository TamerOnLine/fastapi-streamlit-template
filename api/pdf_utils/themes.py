# api/pdf_utils/themes.py
from __future__ import annotations
from reportlab.lib import colors

# افتراضيات عامة تُستخدم إذا لم تُحدَّد في الثيم
DEFAULT_THEME = {
    "colors": {
        "heading": "#222222",
        "subhead": "#0A7D55",
        "left_bg": "#F8F9FA",
        "left_border": "#E3E6EA",
        "rule_right": "#D4D7DC",
        "text": "#000000",
    },
    "sizes": {
        "name": 22,
        "heading": 12,
        "text": 10,
        "right_rule_width": 0.6,
    },
    "spacing": {
        "name_gap": 12,            # نقاط (pt)
        "gap_after_heading": 8,
    },
    "fonts": {
        "latin": "Helvetica",
        "latin_bold": "Helvetica-Bold",
        "arabic": "NotoNaskhArabic",   # مسجل عند بدء التشغيل
    },
}

def to_hex_color(v: str):
    return colors.HexColor(v)
