# api/pdf_utils/theme_loader.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from . import config as cfg  # سنطبّق overrides على ثوابت config.py لديك 

THEMES_DIR = Path("themes")

def load_theme(theme_name: str = "default") -> Dict[str, Any]:
    path = THEMES_DIR / f"{theme_name}.theme.json"
    if not path.is_file():
        # fallback إلى default
        path = THEMES_DIR / "default.theme.json"
        if not path.is_file():
            return {"style": {}, "layout": [], "defaults": {}}
    return json.loads(path.read_text(encoding="utf-8"))

def apply_style_overrides(style: Dict[str, Any]) -> None:
    """
    يطبّق قيم style على ثوابت config.py (monkey-patch للثوابت).
    أمثلة: HEADING_COLOR, RULE_COLOR, NAME_SIZE, GAP_AFTER_HEADING, ...
    """
    if not style:
        return

    from reportlab.lib import colors

    def to_color(v: Any):
        if isinstance(v, str) and v.strip().startswith("#"):
            return colors.HexColor(v.strip())
        return v

    for k, v in style.items():
        if hasattr(cfg, k):
            val = to_color(v)
            setattr(cfg, k, val)

# api/pdf_utils/theme_loader.py (أضف في النهاية)
def get_page_cfg(theme: dict) -> dict:
    return theme.get("page") or {}

