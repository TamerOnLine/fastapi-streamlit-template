# api/routes/generate_form.py
from __future__ import annotations

from typing import Optional, Any, Dict, List, Tuple
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.pdf_utils import build_resume_pdf
from api.utils.parsers import (
    parse_csv_or_lines,
    normalize_language_level,
    parse_projects_blocks,
    parse_education_blocks,
    parse_sections_text,
)

# الثيمات الديناميكية
from api.pdf_utils.theme_loader import load_theme, apply_style_overrides

router = APIRouter()


@router.post("/generate-form")
async def generate_form(
    request: Request,
    # --- Basic info (Form fields) ---
    name: str = Form(""),
    location: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    github: str = Form(""),
    linkedin: str = Form(""),
    birthdate: str = Form(""),
    projects_text: str = Form(""),
    education_text: str = Form(""),
    sections_left_text: str = Form(""),
    sections_right_text: str = Form(""),
    skills_text: str = Form(""),
    languages_text: str = Form(""),
    rtl_mode: str = Form("false"),
    theme_name: str = Form("default"),
    # --- Optional image upload ---
    photo: Optional[UploadFile] = File(None),
):
    """
    يستقبل بيانات الـ Form من Streamlit ويحوّلها إلى layout_plan
    بناءً على ملف الثيم (themes/*.theme.json)
    ثم يولّد PDF عبر نظام الكتل الجديد.
    """

    # -------- قراءة الصورة --------
    photo_bytes: Optional[bytes] = await photo.read() if photo else None

    # -------- تحليل الحقول النصية --------
    skills = parse_csv_or_lines(skills_text)
    languages = [normalize_language_level(x) for x in parse_csv_or_lines(languages_text)]
    projects_tuples: List[Tuple[str, str, str | None]] = parse_projects_blocks(projects_text)
    education_items: List[str] = parse_education_blocks(education_text)
    sections_left = parse_sections_text(sections_left_text)
    sections_right = parse_sections_text(sections_right_text)

    # -------- تحميل الثيم وتطبيق الستايل --------
    theme = load_theme(theme_name)
    apply_style_overrides(theme.get("style") or {})

    # -------- إعداد البيانات الجاهزة لكل Block --------
    contact_items: Dict[str, str] = {}
    if location.strip():
        contact_items["location"] = location.strip()
    if phone.strip():
        contact_items["phone"] = phone.strip()
    if email.strip():
        contact_items["email"] = email.strip()
    if birthdate.strip():
        contact_items["birthdate"] = birthdate.strip()
    if github.strip():
        contact_items["github"] = github.strip()
    if linkedin.strip():
        contact_items["linkedin"] = linkedin.strip()

    social: Dict[str, str] = {}
    if github.strip():
        social["github"] = github.strip()
    if linkedin.strip():
        social["linkedin"] = linkedin.strip()

    ready: dict[str, Any] = {
        "header_name": {"name": name.strip()},
        "avatar_circle": {"photo_bytes": photo_bytes, "max_d_mm": 42},
        "contact_info": {"items": contact_items},
        "key_skills": {"skills": skills},
        "languages": {"languages": languages},
        "social_links": {**social},
        "projects": {"items": projects_tuples, "title": None},
        "education": {"items": education_items, "title": None},
        # summary أو النصوص الحرة من العمود الأيمن
        "text_section:summary": {
            "title": "",
            "lines": [ln for sec in sections_right for ln in (sec.get("lines") or [])],
        },
    }

    # -------- إنشاء layout_plan من ملف الثيم --------
    layout_plan: List[Dict[str, Any]] = []

    for item in (theme.get("layout") or []):
        bid = item.get("block_id")
        frame = item.get("frame", "right")
        src = item.get("source")
        data_override = item.get("data") or {}

        if not bid:
            continue

        data_key = f"{bid}:{src}" if src else bid
        data = ready.get(data_key) or ready.get(bid) or {}
        merged = {**data, **data_override} if data_override else data

        # تخطي البلوكات الفارغة (باستثناء الاسم)
        if bid != "header_name":
            if not any(bool(v) for v in merged.values()):
                continue

        layout_plan.append({"block_id": bid, "frame": frame, "data": merged})

    if not layout_plan:
        raise HTTPException(status_code=400, detail=f"No content to render for theme='{theme_name}'")

    # -------- إعدادات اللغة والاتجاه --------
    rtl = (rtl_mode or "").strip().lower() == "true" or bool(theme.get("defaults", {}).get("rtl_mode"))
    ui_lang = (theme.get("defaults", {}).get("ui_lang") or ("ar" if rtl else "en")).lower()

    # -------- توليد ملف الـ PDF --------
    try:
        pdf_bytes = build_resume_pdf(layout_plan=layout_plan, ui_lang=ui_lang, rtl_mode=rtl, theme=theme)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # -------- إعادة النتيجة --------
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="resume.pdf"'},
    )
