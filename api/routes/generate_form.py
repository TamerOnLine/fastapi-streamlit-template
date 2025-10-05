# api/routes/generate_form.py
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from io import BytesIO
from pathlib import Path
import json
import traceback

from ..pdf_utils.resume import build_resume_pdf

# للفحص المسبق (Preflight)
from ..pdf_utils.blocks.registry import get as get_block

router = APIRouter(prefix="", tags=["generate"])

# --------------------------------------------------------------------
# مسارات المشروع
PROJECT_ROOT = Path(__file__).resolve().parents[2]
THEMES_DIR = PROJECT_ROOT / "themes"
LAYOUTS_DIR = PROJECT_ROOT / "layouts"

# --------------------------------------------------------------------
# أدوات قراءة وتطبيع
def _prefer_fixed(path: Path) -> Path:
    """
    لو هناك نسخة .fixed لنفس الملف نستخدمها، وإلا نرجع المسار الأصلي.
    """
    fixed = path.with_suffix(path.suffix + ".fixed")
    return fixed if fixed.exists() else path

def _safe_json_read(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[⚠️] Failed to read JSON: {path} -> {e}")
        return {}

def _normalize_layout_list(items: List[Any]) -> List[Dict[str, Any]]:
    """
    حوّل عناصر layout إلى قائمة قواميس {block_id: ...}
    يقبل عناصر نصية أو قواميس جاهزة.
    يتجاهل العناصر غير الصالحة مع لوج تحذيري.
    """
    out: List[Dict[str, Any]] = []
    for it in (items or []):
        if isinstance(it, str) and it.strip():
            out.append({"block_id": it.strip()})
        elif isinstance(it, dict) and it.get("block_id"):
            out.append(it)
        else:
            print(f"[⚠️] Skipping invalid layout item: {it!r}")
    return out

def _normalize_layout_value(layout_value: Any) -> Dict[str, Any]:
    """
    يقبل:
      - dict يحتوي "layout"
      - list مباشرة
    ويُعيد دائمًا dict بشكل {"layout": [ {block_id:...}, ... ]}
    """
    if isinstance(layout_value, dict):
        return {"layout": _normalize_layout_list(layout_value.get("layout") or [])}
    if isinstance(layout_value, list):
        return {"layout": _normalize_layout_list(layout_value)}
    return {"layout": []}

def _build_layout_inline_from_theme(theme_name: str) -> Dict[str, Any]:
    """
    تحميل التخطيط المضمّن من ملف الثيم.
    يدعم وجوده تحت المفتاح "layout_inline" أو "layout".
    يفضّل ملف .fixed إن وُجد.
    """
    base = THEMES_DIR / f"{theme_name}.theme.json"
    path = _prefer_fixed(base)
    print(f"[THEME DEBUG] Loading theme file from: {path}")
    if not path.exists():
        print(f"[⚠️] Theme '{theme_name}' not found in {THEMES_DIR}")
        return {"layout": []}

    data = _safe_json_read(path)
    layout_value = data.get("layout_inline") or data.get("layout")
    return _normalize_layout_value(layout_value)

def _load_layout_inline(layout_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    تحميل تخطيط خارجي من مجلد /layouts.
    يدعم "layout" أو "layout_blocks" ويحتفظ بـ frames/page إن وُجدا.
    يفضّل ملف .fixed إن وُجد.
    """
    if not layout_name:
        return None

    base = LAYOUTS_DIR / f"{layout_name}.layout.json"
    path = _prefer_fixed(base)
    print(f"[LAYOUT DEBUG] Loading layout file from: {path}")
    if not path.exists():
        print(f"[⚠️] Layout '{layout_name}' not found in {LAYOUTS_DIR}")
        return None

    data = _safe_json_read(path)
    # تطبيع مفتاح بديل
    if "layout_blocks" in data and "layout" not in data:
        data["layout"] = data.get("layout_blocks") or []

    normalized_layout = _normalize_layout_value(data.get("layout"))
    out: Dict[str, Any] = {"layout": normalized_layout.get("layout", [])}

    # احتفظ بـ frames/page إن وُجدا وبنية صحيحة
    if isinstance(data.get("frames"), dict):
        out["frames"] = data["frames"]
    if isinstance(data.get("page"), dict):
        out["page"] = data["page"]

    return out

def _merge_layouts(theme_inline: Dict[str, Any], layout_inline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    دمج تخطيط الثيم المضمّن مع تخطيط خارجي.
    التخطيط الخارجي يتفوّق على مفاتيح ("frames", "layout", "page") إن وُجدت.
    """
    merged = dict(theme_inline or {"layout": []})
    if layout_inline:
        for key in ("frames", "layout", "page"):
            if key in layout_inline:
                merged[key] = layout_inline[key]
    # تأكد من التطبيع النهائي
    return _normalize_layout_value(merged)

def _log_layout_blocks(layout_inline: Dict[str, Any]) -> None:
    blocks = []
    for b in (layout_inline.get("layout") or []):
        if isinstance(b, dict):
            blocks.append(b.get("block_id"))
        elif isinstance(b, str):
            blocks.append(b)
    print(f">> 🗺️  Layout blocks: {blocks}")

def _preflight(layout_inline: dict, profile: dict):
    """
    فحص مبكر: يطبع قائمة البلوكات، وما هو غير مسجّل، وما لا توجد له بيانات في profile.
    """
    wanted = [b.get("block_id") for b in (layout_inline.get("layout") or []) if isinstance(b, dict)]
    not_registered = []
    for b in wanted:
        try:
            get_block(b)
        except Exception:
            not_registered.append(b)
    missing_data = [b for b in wanted if b not in (profile or {})]
    print(f"[PREFLIGHT] blocks: {wanted}")
    if not_registered:
        print(f"[PREFLIGHT] ⚠️ not registered: {not_registered}")
    if missing_data:
        print(f"[PREFLIGHT] ℹ️ no profile data for: {missing_data}")

# --------------------------------------------------------------------
# نموذج الطلب للمسار البسيط (JSON)
class GenerateFormRequest(BaseModel):
    theme_name: str = "default"
    layout_name: Optional[str] = None
    ui_lang: str = "ar"
    rtl_mode: bool = True
    profile: Dict[str, Any] = {}

# --------------------------------------------------------------------
# Advanced: form/multipart (توافق)
@router.post("/generate-form")
async def generate_form(
    theme_name: str = Form("default"),
    layout_name: Optional[str] = Form(None),
    ui_lang: str = Form("ar"),
    rtl_mode: bool = Form(True),
    profile_json: Optional[str] = Form(None),
    profile_file: Optional[UploadFile] = File(None),
):
    try:
        if profile_file:
            profile_data = json.loads(profile_file.file.read().decode("utf-8"))
        elif profile_json:
            profile_data = json.loads(profile_json)
        else:
            raise HTTPException(status_code=400, detail="Profile data is required")

        data: Dict[str, Any] = {
            "ui_lang": ui_lang or "ar",
            "rtl_mode": bool(rtl_mode),
            "profile": profile_data or {},
            "theme_name": theme_name or "default",
        }

        theme_inline = _build_layout_inline_from_theme(theme_name)
        extra_layout = _load_layout_inline(layout_name) if layout_name else None
        merged_inline = _merge_layouts(theme_inline, extra_layout)

        _log_layout_blocks(merged_inline)
        _preflight(merged_inline, data["profile"])  # فحص مبكر مفيد

        data["layout_inline"] = merged_inline

        pdf_bytes = build_resume_pdf(data=data)
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="resume-{theme_name}.pdf"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        print("=== /generate-form ERROR ===")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {e}")

# --------------------------------------------------------------------
# Simple: JSON (مُفضّل لـ Streamlit)
@router.post("/generate-form-simple")
async def generate_form_simple(req: GenerateFormRequest):
    try:
        data: Dict[str, Any] = {
            "ui_lang": req.ui_lang or "ar",
            "rtl_mode": bool(req.rtl_mode),
            "profile": req.profile or {},
            "theme_name": req.theme_name or "default",
        }

        theme_inline = _build_layout_inline_from_theme(req.theme_name)
        extra_layout = _load_layout_inline(req.layout_name) if req.layout_name else None
        merged_inline = _merge_layouts(theme_inline, extra_layout)

        _log_layout_blocks(merged_inline)
        _preflight(merged_inline, data["profile"])  # فحص مبكر مفيد

        data["layout_inline"] = merged_inline

        pdf_bytes = build_resume_pdf(data=data)
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="resume-{req.theme_name}.pdf"'},
        )
    except Exception as e:
        print("=== /generate-form-simple ERROR ===")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {e}")

# --------------------------------------------------------------------
# Health check (اختياري)
@router.get("/healthz")
def healthz():
    return {
        "ok": True,
        "themes_dir": str(THEMES_DIR),
        "layouts_dir": str(LAYOUTS_DIR),
    }
