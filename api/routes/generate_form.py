# api/routes/generate_form.py
from __future__ import annotations

from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from json import JSONDecodeError
import json

from api.pdf_utils.theme_loader import load_theme, apply_style_overrides
from api.pdf_utils.resume import build_resume_pdf
from api.pdf_utils.layout_utils import merge_layout
from api.pdf_utils.data_utils import build_ready_from_profile
from api.utils.parsers import (
    parse_csv_or_lines, normalize_language_level,
    parse_projects_blocks, parse_education_blocks, parse_sections_text
)

PROFILES_DIR = Path("profiles")
LAYOUTS_DIR  = Path("layouts")
router = APIRouter()

@router.post("/generate-form")
async def generate_form(
    request: Request,
    # ---- form fallback (تبقى تعمل إن ما توفر JSON/ملفات) ----
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
    theme_name: str = Form("modern"),
    # ---- وضع الملفات الجاهزة ----
    profile_name: str = Form("tamer.profile"),
    layout_name: str = Form("left-panel.layout"),
    # صورة اختيارية
    photo: UploadFile | None = File(None),
):
    """
    ترتيب المعالجة:
      1) JSON مباشر (payload.profile / payload.layout_inline / payload.layout_name / payload.theme_name)
      2) ملفات جاهزة من profiles/ و layouts/
      3) Fallback للـ form النصي
    """
    content_type = (request.headers.get("content-type") or "").lower()

    # ======================
    # 1) وضع JSON المباشر
    # ======================
    if content_type.startswith("application/json"):
        # حارس: امنع 500 عند جسم فاضي أو JSON غير صالح
        raw = await request.body()
        if not raw or not raw.strip():
            raise HTTPException(status_code=400, detail="Empty JSON body")
        try:
            payload = json.loads(raw)
        except JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        profile = payload.get("profile") or {}
        if not isinstance(profile, dict) or not profile:
            raise HTTPException(status_code=400, detail="JSON must include a non-empty `profile` object")

        # إعداد الثيم + تخصيصات
        theme = load_theme(payload.get("theme_name") or theme_name)
        apply_style_overrides(theme.get("style") or {})  # يطبّق تغييرات الألوان والأحجام على config

        # تحويل الـ profile إلى ready dict للبلوكات
        ready = build_ready_from_profile(profile)

        # اختيار الـ layout
        layout_plan: list[dict] = []
        layout_inline = payload.get("layout_inline")
        if layout_inline and isinstance(layout_inline, dict):
            layout_plan = merge_layout((layout_inline or {}).get("layout") or [], ready)

        if not layout_plan:
            # اسم ملف layout (بدون .json)
            ln = payload.get("layout_name", layout_name)
            layout_path = LAYOUTS_DIR / f"{ln}.json"
            if layout_path.exists():
                layout = json.loads(layout_path.read_text(encoding="utf-8"))
                layout_plan = merge_layout(layout.get("layout") or [], ready)
                # دمج إعدادات الصفحة/الأعمدة من ملف الـ layout إن وجدت
                theme["page"]    = layout.get("page")    or theme.get("page")    or {}
                theme["columns"] = layout.get("columns") or theme.get("columns") or {}
            else:
                # fallback: استخدم layout من الـ theme نفسه
                layout_plan = merge_layout(theme.get("layout") or [], ready)

        ui  = (payload.get("ui_lang") or theme.get("defaults", {}).get("ui_lang") or "en").lower()
        rtl = bool(payload.get("rtl_mode", False)) or bool(theme.get("defaults", {}).get("rtl_mode"))

        # توليد الPDF كبايتات
        pdf_bytes = build_resume_pdf(layout_plan=layout_plan, ui_lang=ui, rtl_mode=rtl, theme=theme)
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename=resume.pdf'}
        )

    # ===========================================
    # 2) وضع الملفات بالأسماء: profile + layout
    # ===========================================
    profile_path = PROFILES_DIR / f"{profile_name}.json"
    layout_path  = LAYOUTS_DIR  / f"{layout_name}.json"

    ready: dict | None = None
    if profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            ready = build_ready_from_profile(profile or {})
        except Exception:
            # لا تُفشل الطلب؛ اسمح بالانتقال للـ fallback
            ready = None

    theme = load_theme(theme_name)
    apply_style_overrides(theme.get("style") or {})

    layout_plan: list[dict] = []
    if layout_path.exists():
        try:
            layout = json.loads(layout_path.read_text(encoding="utf-8"))
            layout_plan = merge_layout(layout.get("layout") or [], ready or {})
            theme["page"]    = layout.get("page")    or theme.get("page")    or {}
            theme["columns"] = layout.get("columns") or theme.get("columns") or {}
        except Exception:
            # لا تُفشل الطلب؛ اسمح بالانتقال للـ fallback
            layout_plan = []

    # =========================
    # 3) Fallback: form بسيط
    # =========================
    if not ready:
        photo_bytes = await photo.read() if photo else None
        skills = parse_csv_or_lines(skills_text)
        languages = [normalize_language_level(x) for x in parse_csv_or_lines(languages_text)]
        projects = parse_projects_blocks(projects_text)
        education = parse_education_blocks(education_text)
        left_sections = parse_sections_text(sections_left_text)
        right_sections = parse_sections_text(sections_right_text)

        contact: dict[str, str] = {}
        if location.strip(): contact["location"] = location.strip()
        if phone.strip():    contact["phone"] = phone.strip()
        if email.strip():    contact["email"] = email.strip()
        if github.strip():   contact["github"] = github.strip()
        if linkedin.strip(): contact["linkedin"] = linkedin.strip()
        if birthdate.strip():contact["birthdate"] = birthdate.strip()

        ready = {
            "header_name": {"name": name.strip()},
            "avatar_circle": {"photo_bytes": photo_bytes, "max_d_mm": 42},
            "contact_info": {"items": contact},
            "key_skills": {"skills": skills},
            "languages": {"languages": languages},
            "social_links": {k: v for k, v in contact.items() if k in {"github","linkedin","website","site","url","twitter","x"}},
            "projects": {"items": projects, "title": None},
            "education": {"items": education, "title": None},
            "text_section:summary": {
                "title": "",
                "lines": [ln for sec in right_sections for ln in (sec.get("lines") or [])],
            },
        }

        if not layout_plan:
            layout_plan = merge_layout(theme.get("layout") or [], ready)

    # تحديد RTL/UI
    rtl = (rtl_mode.strip().lower() == "true") or bool(theme.get("defaults", {}).get("rtl_mode"))
    ui  = (theme.get("defaults", {}).get("ui_lang") or ("ar" if rtl else "en")).lower()

    if not layout_plan:
        # fallback نهائي: Layout بسيط مُفصّل
        layout_plan = [
            {"block_id": "header_name", "frame": "right", "data": ready.get("header_name", {})},
            {"block_id": "avatar_circle", "frame": "right", "data": ready.get("avatar_circle", {})},
            {"block_id": "contact_info", "frame": "left",  "data": ready.get("contact_info", {})},
            {"block_id": "key_skills",   "frame": "left",  "data": ready.get("key_skills", {})},
            {"block_id": "languages",    "frame": "left",  "data": ready.get("languages", {})},
            # ملاحظة: block_id هو "text_section" بينما الداتا محفوظة تحت "text_section:summary"
            {"block_id": "text_section", "frame": "right", "data": ready.get("text_section:summary", {})},
            {"block_id": "projects",     "frame": "right", "data": ready.get("projects", {})},
            {"block_id": "education",    "frame": "right", "data": ready.get("education", {})},
        ]

    # Debugات خفيفة (تساعد أثناء التطوير)
    print("DEBUG LAYOUT PLAN:", layout_plan)
    print("DEBUG READY KEYS:", list(ready.keys()) if ready else None)

    pdf_bytes = build_resume_pdf(layout_plan=layout_plan, ui_lang=ui, rtl_mode=rtl, theme=theme)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename=resume.pdf'}
    )
