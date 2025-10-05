# api/pdf_utils/debug_assets.py
"""
Debug utilities to inspect asset paths and fonts used by the PDF utils.
Compatible with the current paths.py (ASSETS, ICONS_DIR).
"""

from __future__ import annotations
from typing import Dict, Any

from .paths import ASSETS, ICONS_DIR  # <- ثوابت متاحة في paths.py
from .fonts import _AR_NAME, _AR_PATH, _UI_NAME, _UI_PATH  # تعرض حالة الخطوط إن وُجدت

def gather_assets_info() -> Dict[str, Any]:
    """Return a JSON-serializable report about assets and fonts."""
    info: Dict[str, Any] = {}

    # Paths
    info["paths"] = {
        "ASSETS": str(ASSETS),
        "ICONS_DIR": str(ICONS_DIR),
    }

    # Fonts (names + resolved paths if available)
    info["fonts"] = {
        "arabic": {"name": _AR_NAME, "path": str(_AR_PATH) if _AR_PATH else None},
        "symbols": {"name": _UI_NAME, "path": str(_UI_PATH) if _UI_PATH else None},
    }

    # Icons count (best-effort)
    try:
        from .icons import ICON_PATHS  # خريطة أسماء -> مسارات
        info["icons"] = {"count": len(ICON_PATHS), "sample": list(ICON_PATHS.keys())[:10]}
    except Exception as e:
        info["icons"] = {"error": repr(e)}

    return info


def print_assets_info() -> None:
    """Human-readable print (legacy helper)."""
    print("ASSETS:", ASSETS)
    print("ICONS_DIR:", ICONS_DIR)
    print("Arabic font:", _AR_NAME, _AR_PATH)
    print("Symbols font:", _UI_NAME, _UI_PATH)


if __name__ == "__main__":
    import json
    # اطبع تقريرًا منظّمًا JSON عند التشغيل كـ module
    print(json.dumps(gather_assets_info(), indent=2, ensure_ascii=False))
