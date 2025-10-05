# tools/migrate_layouts.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List
from sys import stderr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
THEMES = PROJECT_ROOT / "themes"
LAYOUTS = PROJECT_ROOT / "layouts"

# استيراد aliases
import sys
sys.path.append(str((PROJECT_ROOT / "api" / "pdf_utils").resolve()))
from block_aliases import canonicalize, CANONICAL_BLOCKS  # type: ignore

def normalize_layout_value(layout_value: Any) -> Dict[str, Any]:
    """أعد دائمًا dict فيه 'layout': [ {block_id:...} ]"""
    if isinstance(layout_value, dict):
        items = layout_value.get("layout", [])
        return {"layout": normalize_list(items)}
    elif isinstance(layout_value, list):
        return {"layout": normalize_list(layout_value)}
    return {"layout": []}

def normalize_list(items: List[Any]) -> List[Dict[str, Any]]:
    out = []
    for it in items or []:
        if isinstance(it, str):
            bid = canonicalize(it)
            out.append({"block_id": bid})
        elif isinstance(it, dict) and it.get("block_id"):
            it = dict(it)
            it["block_id"] = canonicalize(it["block_id"])
            out.append(it)
        else:
            print(f"[skip] invalid layout item: {it!r}", file=stderr)
    return out

def fix_file(path: Path, is_theme: bool) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERR] cannot read {path.name}: {e}", file=stderr)
        return

    # الثيم قد يحمل layout_inline أو layout
    layout_value = data.get("layout_inline") or data.get("layout")
    fixed = normalize_layout_value(layout_value)

    # احفظ النتيجة في نفس المفتاح الذي كان مستخدمًا
    if "layout_inline" in data:
        data["layout_inline"] = fixed
        data.pop("layout", None)
    else:
        data["layout"] = fixed["layout"]

    # تقارير مفيدة
    wanted = [b["block_id"] for b in fixed["layout"]]
    unknown = [b for b in wanted if b not in CANONICAL_BLOCKS]
    if unknown:
        print(f"[WARN] {path.name}: unknown blocks -> {unknown}")

    # اكتب نسخة جديدة بدون تدمير الملف الأصلي
    out_path = path.with_suffix(path.suffix + ".fixed")
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out_path.name}")

def main():
    if THEMES.exists():
        for p in THEMES.glob("*.theme.json"):
            fix_file(p, is_theme=True)
    if LAYOUTS.exists():
        for p in LAYOUTS.glob("*.layout.json"):
            fix_file(p, is_theme=False)

if __name__ == "__main__":
    main()
