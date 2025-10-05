# api/routes/generate_form.py
from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, Request, Response
from charset_normalizer import from_bytes

# واجهة البناء الرئيسية (مصدّرة من api/pdf_utils/__init__.py)
from api.pdf_utils import build_resume_pdf

# لودر الثيم (يرجع dict فيه layout/columns/page/defaults)
from api.pdf_utils.themes import _build_layout_inline_from_theme

# أدوات تفكيك النصوص والمشاريع لفرع multipart
from api.pdf_utils.utils import _split_lines, _parse_projects


router = APIRouter()


def _normalize_json_body(raw: bytes) -> Dict[str, Any]:
    """
    يحاول قراءة JSON من raw bytes:
      - أولاً UTF-8
      - ثم auto-detect عبر charset-normalizer
    """
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        print("⚠️ Non-UTF8 JSON detected; attempting auto-detect...")
        best = from_bytes(raw).best()
        if not best:
            raise ValueError("Unable to decode request body to JSON.")
        # best.strike() أو str(best) يعيد النص بعد التصحيح
        return json.loads(str(best))


@router.post("/generate-form")
async def generate_form(request: Request) -> Response:
    """
    نقطة إنشاء ملف PDF من بيانات JSON (أو نموذج form).
    - تدعم application/json (بأي ترميز شائع، مع auto-detect)
    - وتدعم multipart/form-data
    ترجع: application/pdf
    """
    ct = (request.headers.get("content-type") or "").lower()

    # ==============================
    # 1) application/json
    # ==============================
    if "application/json" in ct:
        raw = await request.body()
        body = _normalize_json_body(raw)

        theme_name = (body.get("theme_name") or "default").strip()

        data: Dict[str, Any] = {
            "ui_lang": body.get("ui_lang") or "en",
            "rtl_mode": bool(body.get("rtl_mode", False)),
            "profile": body.get("profile") or {},
            "theme_name": theme_name,
        }

        # حمّل الثيم كـ inline plan (layout/columns/page/defaults)
        theme_inline = _build_layout_inline_from_theme(theme_name)
        if theme_inline:
            data["layout_inline"] = theme_inline

        # لوج للتشخيص
        blocks = [b.get("block_id") for b in (theme_inline.get("layout") or [])]
        print(f">> 🧩 Using theme: {theme_name}")
        print(f">> Layout blocks: {blocks}")

        pdf_bytes = build_resume_pdf(data=data)
        return Response(content=pdf_bytes, media_type="application/pdf")

    # ==============================
    # 2) multipart/form-data
    # ==============================
    form = await request.form()

    name = str(form.get("name") or "")
    title = str(form.get("title") or "Backend Developer")
    email = str(form.get("email") or "")
    phone = str(form.get("phone") or "")
    github = str(form.get("github") or "")
    linkedin = str(form.get("linkedin") or "")
    location = str(form.get("location") or "")
    skills_text = str(form.get("skills_text") or "")
    languages_text = str(form.get("languages_text") or "")
    projects_text = str(form.get("projects_text") or "")
    sections_right_text = str(form.get("sections_right_text") or "")
    rtl_mode = str(form.get("rtl_mode") or "false").lower() == "true"
    theme_name = (str(form.get("theme_name") or "default")).strip()

    profile: Dict[str, Any] = {
        "header": {"name": name, "title": title},
        "contact": {
            "email": email,
            "phone": phone,
            "github": github,
            "linkedin": linkedin,
            "location": location,
        },
        "skills": _split_lines(skills_text),
        "languages": _split_lines(languages_text),
        "projects": _parse_projects(_split_lines(projects_text)),
        "summary": _split_lines(sections_right_text),
    }

    data: Dict[str, Any] = {
        "ui_lang": "en",
        "rtl_mode": rtl_mode,
        "profile": profile,
        "theme_name": theme_name,
    }

    theme_inline = _build_layout_inline_from_theme(theme_name)
    if theme_inline:
        data["layout_inline"] = theme_inline

    blocks = [b.get("block_id") for b in (theme_inline.get("layout") or [])]
    print(f">> 🧩 Using theme: {theme_name}")
    print(f">> Layout blocks: {blocks}")

    pdf_bytes = build_resume_pdf(data=data)
    return Response(content=pdf_bytes, media_type="application/pdf")
