from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import traceback

from api.schemas import GenerateFormRequest
from ..pdf_utils.resume import build_resume_pdf

try:
    from ..pdf_utils.blocks.registry import get as get_block
except Exception:
    def get_block(_: str):
        return None

router = APIRouter(prefix="", tags=["generate"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
THEMES_DIR = PROJECT_ROOT / "themes"
LAYOUTS_DIR = PROJECT_ROOT / "layouts"

def _prefer_fixed(path: Path) -> Path:
    """
    If a .fixed version of the file exists, return it; otherwise, return the original path.
    """
    fixed = path.with_suffix(path.suffix + ".fixed")
    return fixed if fixed.exists() else path

def _safe_json_read(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Warning] Failed to read JSON: {path} -> {e}")
        return {}

def _normalize_layout_list(items: List[Any]) -> List[Dict[str, Any]]:
    """
    Converts layout items into a list of dictionaries with block_id.
    Accepts strings or dictionaries. Skips invalid items.
    """
    out: List[Dict[str, Any]] = []
    for it in (items or []):
        if isinstance(it, str) and it.strip():
            out.append({"block_id": it.strip()})
        elif isinstance(it, dict) and it.get("block_id"):
            out.append(it)
        else:
            print(f"[Warning] Skipping invalid layout item: {it!r}")
    return out

def _normalize_layout_value(layout_value: Any) -> Dict[str, Any]:
    """
    Returns a unified layout dictionary format with page, frames, and layout keys.
    """
    layout_value = layout_value or {}
    page = layout_value.get("page") or {}
    frames = layout_value.get("frames") or {}
    layout_list = _normalize_layout_list(layout_value.get("layout") or [])
    return {"page": page, "frames": frames, "layout": layout_list}

def _build_layout_inline_from_theme(theme_name: Optional[str]) -> Dict[str, Any]:
    """
    Reads a theme JSON file and extracts inline layout if available.
    """
    theme_name = theme_name or "default"
    theme_path = _prefer_fixed(THEMES_DIR / f"{theme_name}.theme.json")
    theme = _safe_json_read(theme_path)
    if any(k in theme for k in ("layout", "frames", "page")):
        return _normalize_layout_value(theme)
    return {"page": {}, "frames": {}, "layout": []}

def _load_layout_inline(layout_name: Optional[str]) -> Dict[str, Any]:
    """
    Loads and normalizes an external layout file.
    """
    if not layout_name:
        return {}
    p = _prefer_fixed(LAYOUTS_DIR / f"{layout_name}.layout.json")
    return _normalize_layout_value(_safe_json_read(p))

def _merge_layouts(theme_inline: Dict[str, Any], layout_inline: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges theme and layout, with layout taking precedence.
    """
    merged = dict(theme_inline or {"layout": []})
    if layout_inline:
        for key in ("frames", "layout", "page"):
            if key in layout_inline:
                merged[key] = layout_inline[key]
    return _normalize_layout_value(merged)

def _log_layout_blocks(layout_inline: Dict[str, Any]) -> None:
    blocks = []
    for b in (layout_inline.get("layout") or []):
        if isinstance(b, dict):
            blocks.append(b.get("block_id"))
        elif isinstance(b, str):
            blocks.append(b)
    print(f"[Info] Layout blocks: {blocks}")

def _preflight(layout_inline: dict, profile: dict):
    """
    Pre-check: logs expected blocks, unregistered blocks, and missing profile data.
    """
    wanted = [b.get("block_id") for b in (layout_inline.get("layout") or []) if isinstance(b, dict)]
    not_registered = []
    for b in wanted:
        try:
            get_block(b)
        except Exception:
            not_registered.append(b)

    expected_keys = {
        "header", "contact", "skills", "languages", "summary",
        "projects", "education", "social_links", "avatar"
    }
    missing_data = []
    for b in wanted:
        if b in {"decor_curve", "left_panel_bg"}:
            continue
        key_map = {
            "header_name": "header",
            "contact_info": "contact",
            "key_skills": "skills",
            "languages": "languages",
            "text_section": "summary",
            "projects": "projects",
            "education": "education",
            "social_links": "social_links",
            "avatar_circle": "avatar",
        }
        pk = key_map.get(b)
        if pk and pk not in (profile or {}):
            missing_data.append(b)

    print(f"[PREFLIGHT] blocks: {wanted}")
    if not_registered:
        print(f"[PREFLIGHT] Warning: not registered: {not_registered}")
    if missing_data:
        print(f"[PREFLIGHT] Info: no profile data for: {missing_data}")

@router.post("/generate-form-simple")
async def generate_form_simple(req: GenerateFormRequest):
    """
    Accepts payload matching GenerateFormRequest schema,
    merges layout, generates PDF, and returns it.
    """
    try:
        prof = req.profile.dict()
        print("[Debug] PROFILE keys:", list(prof.keys()))
        print("[Debug] header:", prof.get("header"))
        print("[Debug] counts -> summary:", len(prof.get("summary", [])),
              "skills:", len(prof.get("skills", [])),
              "projects:", len(prof.get("projects", [])),
              "education:", len(prof.get("education", [])))

        data: Dict[str, Any] = {
            "ui_lang": req.ui_lang,
            "rtl_mode": bool(req.rtl_mode),
            "profile": prof,
            "theme_name": req.theme_name,
        }

        theme_inline = _build_layout_inline_from_theme(req.theme_name)
        extra_layout = _load_layout_inline(req.layout_name) if req.layout_name else {}
        merged_inline = _merge_layouts(theme_inline, extra_layout)

        _log_layout_blocks(merged_inline)
        _preflight(merged_inline, data["profile"])

        data["layout_inline"] = merged_inline

        pdf_bytes = build_resume_pdf(data=data)
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="resume-{req.theme_name}.pdf"'},
        )
    except Exception as e:
        print("[Error] /generate-form-simple:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {e}")

@router.get("/healthz")
def healthz():
    """
    Health check endpoint.
    """
    return {
        "ok": True,
        "themes_dir": str(THEMES_DIR),
        "layouts_dir": str(LAYOUTS_DIR),
    }