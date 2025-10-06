"""
Debug utilities to inspect asset paths and fonts used by the PDF utils.
Compatible with the current paths.py (ASSETS, ICONS_DIR).
"""

from __future__ import annotations

import json
from typing import Any, Dict

from .paths import ASSETS, ICONS_DIR
from .fonts import _AR_NAME, _AR_PATH, _UI_NAME, _UI_PATH

def gather_assets_info() -> Dict[str, Any]:
    """
    Return a JSON-serializable report about assets and fonts.

    Returns:
        Dict[str, Any]: Dictionary containing paths, font information, and icon stats.
    """
    info: Dict[str, Any] = {
        "paths": {
            "ASSETS": str(ASSETS),
            "ICONS_DIR": str(ICONS_DIR),
        },
        "fonts": {
            "arabic": {"name": _AR_NAME, "path": str(_AR_PATH) if _AR_PATH else None},
            "symbols": {"name": _UI_NAME, "path": str(_UI_PATH) if _UI_PATH else None},
        },
    }

    try:
        from .icons import ICON_PATHS
        info["icons"] = {
            "count": len(ICON_PATHS),
            "sample": list(ICON_PATHS.keys())[:10],
        }
    except Exception as e:
        info["icons"] = {"error": repr(e)}

    return info

def print_assets_info() -> None:
    """
    Print human-readable summary of key paths and fonts (legacy helper).
    """
    print("ASSETS:", ASSETS)
    print("ICONS_DIR:", ICONS_DIR)
    print("Arabic font:", _AR_NAME, _AR_PATH)
    print("Symbols font:", _UI_NAME, _UI_PATH)

if __name__ == "__main__":
    # Print organized JSON report if executed as script
    print(json.dumps(gather_assets_info(), indent=2, ensure_ascii=False))