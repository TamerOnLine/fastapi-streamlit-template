import json
import sys
import pathlib

ALLOWED_BLOCKS = {
    "header_name", "contact_info", "key_skills", "languages",
    "text_section", "projects", "education", "social_links",
    "avatar_circle", "decor_curve", "left_panel_bg"
}

def load(p: pathlib.Path) -> dict:
    """
    Loads and parses a JSON file.

    Args:
        p (Path): Path to the JSON file.

    Returns:
        dict: Parsed JSON content.
    """
    return json.loads(p.read_text(encoding="utf-8"))

def check_layout(name: str, data: dict) -> list[str]:
    """
    Validates a layout dictionary for expected structure and block usage.

    Args:
        name (str): File name for context.
        data (dict): Parsed layout content.

    Returns:
        list[str]: List of validation error messages.
    """
    errs = []
    seen_ts = 0
    items = data.get("layout") or []
    if not isinstance(items, list) or not items:
        errs.append("layout must be non-empty list")
        return errs
    for i, it in enumerate(items):
        bid = (it.get("block_id") if isinstance(it, dict) else None)
        if not bid:
            errs.append(f"layout[{i}] missing block_id")
            continue
        if bid not in ALLOWED_BLOCKS:
            errs.append(f"layout[{i}] unknown block '{bid}'")
        if bid == "text_section":
            seen_ts += 1
    if seen_ts > 1:
        errs.append("text_section appears more than once")
    return errs

def main(root: str = ".") -> None:
    """
    Validates all theme and layout files in the specified root directory.

    Args:
        root (str): Root directory to search for theme and layout files.
    """
    root_path = pathlib.Path(root)
    bad = 0
    for p in (root_path / "themes").glob("*.theme.json"):
        d = load(p)
        if "layout" in d:
            e = check_layout(p.name, d)
            if e:
                print("[THEME]", p.name, "ERR:", e)
                bad += 1
    for p in (root_path / "layouts").glob("*.layout.json"):
        d = load(p)
        e = check_layout(p.name, d)
        if e:
            print("[LAYOUT]", p.name, "ERR:", e)
            bad += 1
    print("OK" if bad == 0 else f"FOUND {bad} invalid file(s)")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
