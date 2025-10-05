# api/routes/generate_form.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, Request, Response, UploadFile, File, Form, HTTPException

from ..schemas import GeneratePayload
from ..pdf_utils.resume import build_resume_pdf

router = APIRouter()

# ─────────────────────────────
# إعداد المسارات
# ─────────────────────────────
THEMES_DIR = Path("themes")
LAYOUTS_DIR = Path("layouts")

# ─────────────────────────────
# دوال مساعدة
# ─────────────────────────────
def _normalize_json_body(raw: bytes) -> dict:
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}

def _load_layout_inline(layout_name: str) -> dict | None:
    """تحميل layouts/<layout>.json وإرجاع frames + layout_blocks في صيغة inline."""
    if not layout_name:
        return None
    path = LAYOUTS_DIR / f"{layout_name}.json"
    if not path.exists():
        print(f"⚠️ layout not found: {path}")
        return None

    try:
        j = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ failed to parse layout {path}: {e}")
        return None

    frames = j.get("frames") or {}
    blocks = j.get("layout_blocks") or []

    # تطبيع الكتل إلى قائمة كائنات {block_id, frame?, data?}
    norm = []
    for b in blocks:
        if isinstance(b, str):
            norm.append({"block_id": b})
        elif isinstance(b, dict):
            item = {"block_id": b.get("block_id")}
            if "frame" in b:
                item["frame"] = b["frame"]
            if "data" in b:
                item["data"] = b["data"]
            norm.append(item)

    inline = {"frames": frames, "layout": norm}
    if "page" in j:
        inline["page"] = j["page"]
    return inline


def _build_layout_inline_from_theme(theme_name: str) -> dict:
    """
    تحميل الثيم theme.json وإرجاع التخطيط inline الافتراضي الموجود داخله.
    """
    path = THEMES_DIR / f"{theme_name}.json"
    if not path.exists():
        print(f"⚠️ theme not found: {path}")
        return {}
    try:
        theme = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ failed to parse theme {path}: {e}")
        return {}

    frames = theme.get("frames") or {}
    layout = theme.get("layout_blocks") or []
    norm = []
    for b in layout:
        if isinstance(b, str):
            norm.append({"block_id": b})
        elif isinstance(b, dict):
            norm.append(b)
    inline = {"frames": frames, "layout": norm, "page": theme.get("page")}
    return inline


# ─────────────────────────────
# المسار الرئيسي
# ─────────────────────────────
@router.post("/generate-form")
async def generate_form(request: Request):
    """
    نقطة النهاية لتوليد PDF.
    تدعم application/json و multipart/form-data.
    """
    ct = request.headers.get("content-type", "")
    if "application/json" in ct:
        raw = await request.body()
        body = _normalize_json_body(raw)

        theme_name = (body.get("theme_name") or "default").strip()
        layout_name = (body.get("layout_name") or "").strip()

        data: Dict[str, Any] = {
            "ui_lang": body.get("ui_lang") or "en",
            "rtl_mode": bool(body.get("rtl_mode", False)),
            "profile": body.get("profile") or {},
            "theme_name": theme_name,
        }

        # تحميل الثيم
        theme_inline = _build_layout_inline_from_theme(theme_name)

        # دمج اللاياوت إن وُجد
        layout_inline = _load_layout_inline(layout_name) if layout_name else None
        if layout_inline:
            print(f">> [layouts] loaded: {layout_name}.json")
            merged_inline = dict(theme_inline)
            if layout_inline.get("frames"):
                merged_inline["frames"] = layout_inline["frames"]
            if layout_inline.get("layout"):
                merged_inline["layout"] = layout_inline["layout"]
            if layout_inline.get("page"):
                merged_inline["page"] = layout_inline["page"]
            data["layout_inline"] = merged_inline
        else:
            data["layout_inline"] = theme_inline

        # لوج واضح
        blocks = [
            (b if isinstance(b, str) else b.get("block_id"))
            for b in (data["layout_inline"].get("layout") or [])
        ]
        print(f">> [themes] loaded: {theme_name}.json")
        print(f">> 🧩 Using theme: {theme_name}")
        if layout_name:
            print(f">> [layouts] active: {layout_name}.json")
        print(f">> Layout blocks: {blocks}")

        pdf_bytes = build_resume_pdf(data=data)
        return Response(content=pdf_bytes, media_type="application/pdf")

    # ───────────── دعم multipart ─────────────
    form = await request.form()
    profile_json = form.get("profile")
    if not profile_json:
        raise HTTPException(status_code=400, detail="Missing 'profile' field in form data.")

    try:
        profile = json.loads(profile_json)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid 'profile' JSON.")

    theme_name = (form.get("theme_name") or "default").strip()
    layout_name = (form.get("layout_name") or "").strip()
    ui_lang = form.get("ui_lang") or "en"
    rtl_mode = form.get("rtl_mode", "false").lower() in ("true", "1", "yes")

    data: Dict[str, Any] = {
        "ui_lang": ui_lang,
        "rtl_mode": rtl_mode,
        "profile": profile,
        "theme_name": theme_name,
    }

    # تحميل الثيم + اللاياوت
    theme_inline = _build_layout_inline_from_theme(theme_name)
    layout_inline = _load_layout_inline(layout_name) if layout_name else None
    if layout_inline:
        print(f">> [layouts] loaded: {layout_name}.json")
        merged_inline = dict(theme_inline)
        if layout_inline.get("frames"):
            merged_inline["frames"] = layout_inline["frames"]
        if layout_inline.get("layout"):
            merged_inline["layout"] = layout_inline["layout"]
        if layout_inline.get("page"):
            merged_inline["page"] = layout_inline["page"]
        data["layout_inline"] = merged_inline
    else:
        data["layout_inline"] = theme_inline

    blocks = [
        (b if isinstance(b, str) else b.get("block_id"))
        for b in (data["layout_inline"].get("layout") or [])
    ]
    print(f">> [themes] loaded: {theme_name}.json")
    print(f">> 🧩 Using theme: {theme_name}")
    if layout_name:
        print(f">> [layouts] active: {layout_name}.json")
    print(f">> Layout blocks: {blocks}")

    pdf_bytes = build_resume_pdf(data=data)
    return Response(content=pdf_bytes, media_type="application/pdf")
