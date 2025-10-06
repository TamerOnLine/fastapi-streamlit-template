from __future__ import annotations

import json
import difflib
from pathlib import Path
from typing import Any, Dict, List

PROJECT = Path(__file__).resolve().parents[1]
THEMES = PROJECT / "themes"
LAYOUTS = PROJECT / "layouts"
OUTPUTS = PROJECT / "outputs"

REGISTERED = {
    "header_name", "avatar_circle", "decor_curve",
    "contact_info", "social_links",
    "key_skills", "languages",
    "text_section", "projects", "education"
}

DECORATIVE = {"avatar_circle", "decor_curve"}

ALIASES = {
    "experience": "projects",
    "eexperience": "projects",
    "expeerience": "projects",
    "skills_grid": "key_skills",
    "links_inline": "social_links",
    "volunteer": None,
    "texxt_section": "text_section",
    "educcation": "education"
}

def default_data_for_block(block_id: str) -> Any:
    if block_id in DECORATIVE:
        return None
    if block_id == "header_name":
        return {"name": "Tamer Hammadeh Faour", "title": "Backend Developer"}
    if block_id == "contact_info":
        return {"email": "tamer@example.com", "phone": "+49 000 000", "location": "Berlin"}
    if block_id == "social_links":
        return [
            ["GitHub", "https://github.com/TamerOnLine"],
            ["LinkedIn", "https://linkedin.com/in/tameronline"]
        ]
    if block_id == "key_skills":
        return ["FastAPI", "PostgreSQL", "ReportLab", "Streamlit"]
    if block_id == "languages":
        return ["Arabic — Native", "English — B1", "German — A2"]
    if block_id == "text_section":
        return [
            "Backend developer specialized in FastAPI and PostgreSQL.",
            "I build PDF tools, Streamlit interfaces, and contribute to open-source projects."
        ]
    if block_id == "projects":
        return [
            ["NeuroServe", "AI inference server using FastAPI", "https://github.com/..."],
            ["RepoSmith", "Project and environment template generator", "https://github.com/..."]
        ]
    if block_id == "education":
        return [
            "2018–2022 — BSc in Computer Science",
            "2023 — Advanced courses in FastAPI and DevOps"
        ]
    return None

def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to read {path}: {e}")

def prefer_fixed(p: Path) -> Path:
    fixed = p.with_suffix(p.suffix + ".fixed")
    return fixed if fixed.exists() else p

def fix_block_id(raw: str) -> str | None:
    bid = (raw or "").strip()
    if not bid:
        return None
    if bid in ALIASES:
        return ALIASES[bid]
    if bid in REGISTERED:
        return bid
    close = difflib.get_close_matches(bid, REGISTERED, n=1, cutoff=0.8)
    return close[0] if close else None

def normalize_layout_list(layout: List[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for it in (layout or []):
        if isinstance(it, str):
            bid = fix_block_id(it)
            if bid:
                out.append({"block_id": bid})
        elif isinstance(it, dict) and it.get("block_id"):
            bid = fix_block_id(it["block_id"])
            if bid:
                it["block_id"] = bid
                out.append(it)
    seen = set()
    uniq = []
    for it in out:
        b = it["block_id"]
        if b in seen:
            continue
        seen.add(b)
        uniq.append(it)
    return uniq

def build_clean_layout(theme_name: str, layout_name: str | None) -> dict:
    theme_path = prefer_fixed(THEMES / f"{theme_name}.theme.json")
    theme = read_json(theme_path) if theme_path.exists() else {}
    theme_inline = {
        "page": theme.get("page") or {},
        "frames": theme.get("frames") or {},
        "layout": normalize_layout_list(theme.get("layout") or [])
    }
    layout_inline = {}
    if layout_name:
        layout_path = prefer_fixed(LAYOUTS / f"{layout_name}.layout.json")
        if layout_path.exists():
            raw = read_json(layout_path)
            layout_inline = {
                "page": raw.get("page") or {},
                "frames": raw.get("frames") or {},
                "layout": normalize_layout_list(raw.get("layout") or [])
            }
    merged = dict(theme_inline)
    for k in ("page", "frames", "layout"):
        if layout_inline.get(k):
            merged[k] = layout_inline[k]
    merged["layout"] = [b for b in merged["layout"] if b["block_id"] not in DECORATIVE]
    return merged

def build_profile_from_layout(merged_layout: dict) -> dict:
    profile: Dict[str, Any] = {}
    key_map = {
        "header_name": "header",
        "contact_info": "contact",
        "social_links": "social_links",
        "key_skills": "skills",
        "languages": "languages",
        "text_section": "summary",
        "projects": "projects",
        "education": "education",
    }
    for item in (merged_layout.get("layout") or []):
        bid = item["block_id"]
        key = key_map.get(bid)
        data = default_data_for_block(bid)
        if key and data is not None:
            profile[key] = data
    return profile

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Clean layout & generate a valid profile.json")
    parser.add_argument("--theme", default="default")
    parser.add_argument("--layout", default=None, help="layout name (without extension)")
    parser.add_argument("--ui-lang", default="ar")
    parser.add_argument("--rtl", action="store_true", default=True)
    parser.add_argument("--outfile-profile", default=str(OUTPUTS / "profile.generated.json"))
    parser.add_argument("--outfile-layout", default=str(OUTPUTS / "layout.cleaned.json"))
    args = parser.parse_args()

    OUTPUTS.mkdir(exist_ok=True)
    merged = build_clean_layout(args.theme, args.layout)
    profile = build_profile_from_layout(merged)

    Path(args.outfile_layout).write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    payload = {
        "theme_name": args.theme,
        "layout_name": args.layout,
        "ui_lang": args.ui_lang,
        "rtl_mode": bool(args.rtl),
        "profile": profile,
        "layout_inline": merged
    }
    Path(args.outfile_profile).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    blocks = [b["block_id"] for b in merged.get("layout", [])]
    print("✅ Clean layout & profile generated.")
    print(f"   blocks: {blocks}")
    print(f"   profile keys: {list(profile.keys())}")
    print(f"   saved: {args.outfile_layout}")
    print(f"   saved: {args.outfile_profile}")

if __name__ == "__main__":
    main()
