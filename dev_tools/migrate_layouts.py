from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List
from sys import stderr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
THEMES = PROJECT_ROOT / "themes"
LAYOUTS = PROJECT_ROOT / "layouts"

# Import block canonicalization logic
sys.path.append(str((PROJECT_ROOT / "api" / "pdf_utils").resolve()))
from block_aliases import canonicalize, CANONICAL_BLOCKS  # type: ignore

def normalize_layout_value(layout_value: Any) -> Dict[str, Any]:
    """
    Ensures layout value is returned as a dict with a standardized list of blocks.

    Args:
        layout_value (Any): Raw layout value (dict or list).

    Returns:
        Dict[str, Any]: Normalized layout dictionary.
    """
    if isinstance(layout_value, dict):
        items = layout_value.get("layout", [])
        return {"layout": normalize_list(items)}
    elif isinstance(layout_value, list):
        return {"layout": normalize_list(layout_value)}
    return {"layout": []}

def normalize_list(items: List[Any]) -> List[Dict[str, Any]]:
    """
    Converts layout items to standardized block dictionaries with canonical block IDs.

    Args:
        items (List[Any]): Raw layout items.

    Returns:
        List[Dict[str, Any]]: Normalized layout items.
    """
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
    """
    Fixes layout structure in a JSON file and writes a `.fixed` version.

    Args:
        path (Path): Path to the JSON file.
        is_theme (bool): Indicates if the file is a theme.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERR] cannot read {path.name}: {e}", file=stderr)
        return

    layout_value = data.get("layout_inline") or data.get("layout")
    fixed = normalize_layout_value(layout_value)

    if "layout_inline" in data:
        data["layout_inline"] = fixed
        data.pop("layout", None)
    else:
        data["layout"] = fixed["layout"]

    wanted = [b["block_id"] for b in fixed["layout"]]
    unknown = [b for b in wanted if b not in CANONICAL_BLOCKS]
    if unknown:
        print(f"[WARN] {path.name}: unknown blocks -> {unknown}")

    out_path = path.with_suffix(path.suffix + ".fixed")
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out_path.name}")

def main():
    """
    Processes all theme and layout JSON files and writes normalized versions.
    """
    if THEMES.exists():
        for p in THEMES.glob("*.theme.json"):
            fix_file(p, is_theme=True)
    if LAYOUTS.exists():
        for p in LAYOUTS.glob("*.layout.json"):
            fix_file(p, is_theme=False)

if __name__ == "__main__":
    main()