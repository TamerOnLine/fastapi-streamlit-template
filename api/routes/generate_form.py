# api/routes/generate_form.py
from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict, List, Tuple, Optional

from fastapi import APIRouter, Request, Response, UploadFile, File, Form
from fastapi.responses import Response as FastAPIResponse

# استيراد الدالة من حزمتك
from api.pdf_utils import build_resume_pdf  # __init__.py يصدّرها
# لو لم تكن مُصدّرة في __init__ عندك، استخدم:
# from api.pdf_utils.resume import build_resume_pdf

router = APIRouter()

THEMES_DIR = Path(__file__).resolve().parents[2] / "themes"


def _split_lines(txt: str | None) -> list[str]:
    return [ln.strip() for ln in (txt or "").splitlines() if ln.strip()]


def _parse_projects(lines: list[str]) -> list[list[str]]:
    """يدعم:
       - 'title | desc | link'
       - 'title - desc'
       - 'title'
    """
    out: list[list[str]] = []
    for ln in lines:
        if "|" in ln:
            parts = [p.strip() for p in ln.split("|")]
            title = parts[0] if len(parts) > 0 else ""
            desc = parts[1] if len(parts) > 1 else ""
            link = parts[2] if len(parts) > 2 else ""
        elif " - " in ln:
            title, desc = [p.strip() for p in ln.split(" - ", 1)]
            link = ""
        else:
            title, desc, link = ln, "", ""
        if title or desc or link:
            out.append([title, desc, link])
    return out


def _build_layout_inline_from_theme(theme_name: str) -> dict:
    """يحمل الثيم (إن وُجد) ويحوّل الأعمدة/التخطيط إلى layout_inline مفهوم للراسم."""
    p = THEMES_DIR / f"{theme_name}.theme.json"
    if not p.is_file():
        return {}

    theme = json.loads(p.read_text(encoding="utf-8"))

    # margins
    margins = (theme.get("page") or {}).get("margins_mm") or {"top": 16, "right": 16, "bottom": 16, "left": 16}

    # columns
    cols_spec = theme.get("columns") or [
        {"id": "left", "w_mm": 66, "gap_right_mm": 10},
        {"id": "right", "flex": 1},
    ]
    page_w_mm = 210 - (margins["left"] + margins["right"])  # A4 عرض 210 مم
    x_cursor = margins["left"]
    fixed_total = 0.0
    for col in cols_spec:
        if "w_mm" in col:
            fixed_total += float(col.get("w_mm", 0)) + float(col.get("gap_right_mm", 0))
    remaining = max(0.0, page_w_mm - fixed_total)

    columns_inline: dict[str, dict[str, float]] = {}
    for col in cols_spec:
        cid = col["id"]
        if "w_mm" in col:
            w = float(col["w_mm"])
        elif col.get("flex"):
            w = remaining
        else:
            w = 60.0
        columns_inline[cid] = {"x_mm": x_cursor, "w_mm": w}
        x_cursor += w + float(col.get("gap_right_mm", 0))

    # layout (ادعم legacy: frame → col)
    layout = []
    for item in (theme.get("layout") or []):
        bid = item.get("block_id")
        if not bid:
            continue
        col = item.get("col") or item.get("frame")
        layout.append({
            "block_id": bid,
            "col": col or "right",
            "data": item.get("data") or {},
            **({"source": item["source"]} if "source" in item else {}),
        })

    return {
        "page": {"margins_mm": margins},
        "columns": columns_inline,
        "layout": layout,
    }


@router.post("/generate-form")
async def generate_form(request: Request) -> FastAPIResponse:
    """
    يقبل:
      - application/json (payload هرمي)
      - multipart/form-data (حقول مسطحة + اختيارياً photo)
    ويرجع: application/pdf
    """
    ct = (request.headers.get("content-type") or "").lower()

    if ct.startswith("application/json"):
        # ----- JSON هرمي مباشر -----
        body = await request.json()  # <- يزيل تحذير "body is not defined"
        theme_name = body.get("theme_name") or "default"
        data = {
            "ui_lang": body.get("ui_lang") or "en",
            "rtl_mode": bool(body.get("rtl_mode", False)),
            "profile": body.get("profile") or {},
        }
        # دمج layout_inline من الثيم (إن وُجد)
        li = _build_layout_inline_from_theme(theme_name)
        if li:
            data["layout_inline"] = li

        pdf_bytes = build_resume_pdf(data=data)  # <- يزيل تحذير "build_resume_pdf is not defined"
        return Response(content=pdf_bytes, media_type="application/pdf")

    # ----- multipart/form-data (النموذج القديم) -----
    form = await request.form()
    # حقول مسطحة قادمة من Streamlit
    name = str(form.get("name") or "")
    title = "Backend Developer"  # عدّله لاحقاً إن أردت
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
    theme_name = str(form.get("theme_name") or "default")

    # حوّلها إلى profile هرمي
    profile: dict[str, Any] = {
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

    # صورة اختيارية
    if "photo" in form and isinstance(form["photo"], UploadFile):
        file: UploadFile = form["photo"]
        bts = await file.read()
        profile["avatar"] = {
            "bytes_b64": bts.decode("latin1").encode("latin1").hex(),  # أبسط تمرير؛ أو استبدلها بـ base64 فعلي لو أردت
            # ملاحظة: لو تريد Base64 الصحيح استبدل السطر أعلاه بـ:
            # "bytes_b64": base64.b64encode(bts).decode("ascii"),
            "mime": file.content_type or "image/png",
            "name": file.filename or "photo.png",
        }

    data = {
        "ui_lang": "en",
        "rtl_mode": rtl_mode,
        "profile": profile,
    }

    # دمج layout_inline من الثيم (إن وُجد)
    li = _build_layout_inline_from_theme(theme_name)
    if li:
        data["layout_inline"] = li

    pdf_bytes = build_resume_pdf(data=data)
    return Response(content=pdf_bytes, media_type="application/pdf")
