# api/pdf_utils/themes.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List

# مجلد themes في جذر المشروع
THEMES_DIR = Path(__file__).resolve().parents[2] / "themes"

def _normalize_name(name: str | None) -> str:
    n = (name or "default").strip()
    # أزل أي لاحقات شائعة
    for suf in (".theme.json", ".theme", ".json"):
        if n.lower().endswith(suf):
            n = n[: -len(suf)]
            break
    return n

def _candidate_paths(base: str) -> List[Path]:
    """
    جرّب كل التركيبات المحتملة لاسم الثيم.
    """
    names = [
        f"{base}.theme.json",
        f"{base}.json",
        base,  # لو تم تمرير اسم ملف كامل مسبقاً
    ]
    paths: List[Path] = []
    for nm in names:
        p = THEMES_DIR / nm
        paths.append(p)
    return paths

def load_theme(theme_name: str | None) -> Dict[str, Any]:
    base = _normalize_name(theme_name)

    for fp in _candidate_paths(base):
        if fp.exists():
            with fp.open("r", encoding="utf-8") as f:
                theme = json.load(f)
            # ضمان المفاتيح الأساسية
            theme.setdefault("layout", [])
            theme.setdefault("columns", [{"id": "right", "flex": 1}])
            theme.setdefault("page", {})
            theme.setdefault("defaults", {})
            print(f">> [themes] loaded: {fp.name}")
            return theme

    # لو لم نعثر على أي ملف.. اطبع قائمة الملفات للمساعدة
    try:
        available = sorted(p.name for p in THEMES_DIR.glob("*.json"))
    except Exception:
        available = []
    print(f"[warn] theme '{theme_name}' not found in {THEMES_DIR}")
    print(f"[warn] available themes: {available}")

    # Fallback آمن
    return {
        "name": "fallback",
        "columns": [{"id": "right", "flex": 1}],
        "layout": [
            {"block_id": "header_name", "col": "right"},
            {"block_id": "key_skills",  "col": "right"},
        ],
        "page": {},
        "defaults": {},
    }

def _build_layout_inline_from_theme(theme_name: str | None) -> Dict[str, Any]:
    theme = load_theme(theme_name)
    return {
        "name": theme.get("name"),
        "columns": theme.get("columns") or [{"id": "right", "flex": 1}],
        "layout": theme.get("layout") or [],
        "page": theme.get("page", {}),
        "defaults": theme.get("defaults", {}),
    }
