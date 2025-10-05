# frontend/tabs/generate.py
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
import base64
import streamlit as st

from api_client import get_api_base, post_generate_form


def _request_reset():
    st.session_state["_reset_requested"] = True


# 🔹 جلب قائمة الثيمات من مجلد themes/
def list_themes() -> list[str]:
    themes_dir = Path.cwd() / "themes"
    if themes_dir.is_dir():
        names = [p.stem for p in themes_dir.glob("*.theme.json")]
        if names:
            return sorted(set(names))
    return ["default", "modern"]


# -------- Helpers to parse multiline text into structured lists --------
def _split_nonempty_lines(text: str) -> List[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

def _parse_projects(lines: List[str]) -> List[Tuple[str, str, str]]:
    """
    يحاول قراءة كل سطر كمشروع:
      1) "title | desc | link"
      2) "title - desc"        (بدون link)
      3) "title"               (عنوان فقط)
    ويعيد [ [title, desc, link], ... ]
    """
    out: List[Tuple[str, str, str]] = []
    for ln in lines:
        if "|" in ln:
            parts = [p.strip() for p in ln.split("|")]
            title = parts[0] if len(parts) > 0 else ""
            desc  = parts[1] if len(parts) > 1 else ""
            link  = parts[2] if len(parts) > 2 else ""
        elif " - " in ln:
            title, desc = [p.strip() for p in ln.split(" - ", 1)]
            link = ""
        else:
            title, desc, link = ln, "", ""
        if title or desc or link:
            out.append((title, desc, link))
    return out


def render_generate_actions(outputs_dir: Path) -> None:
    st.header("Generate & Download")

    # --- قائمة الثيمات ---
    themes = list_themes()
    default_idx = themes.index(st.session_state.get("theme_name", themes[0])) if st.session_state.get("theme_name") in themes else 0
    theme_name = st.selectbox("🎨 اختر تنسيق السيرة (Theme)", themes, index=default_idx, key="theme_name")

    # --- الأزرار ---
    colg1, colg2, colg3 = st.columns(3)

    # ===== توليد PDF =====
    with colg1:
        if st.button("Generate PDF", type="primary"):
            try:
                # ----- جمع الحقول من الحالة -----
                name      = st.session_state.get("name", "").strip()
                title     = "Backend Developer"  # يمكنك ربطه بحقل من التبويب الأساسي لاحقًا
                email     = st.session_state.get("email", "").strip()
                phone     = st.session_state.get("phone", "").strip()
                github    = st.session_state.get("github", "").strip()
                linkedin  = st.session_state.get("linkedin", "").strip()
                location  = st.session_state.get("location", "").strip()
                rtl_mode  = bool(st.session_state.get("rtl_mode", False))

                skills    = _split_nonempty_lines(st.session_state.get("skills_text", ""))
                languages = _split_nonempty_lines(st.session_state.get("languages_text", ""))
                projects  = _parse_projects(_split_nonempty_lines(st.session_state.get("projects_text", "")))

                # ملخص (summary) — إمّا من sections_right_text أو نضع عبارات افتراضية
                summary_lines = _split_nonempty_lines(st.session_state.get("sections_right_text", "")) or [
                    "Backend Developer with expertise in FastAPI and PostgreSQL.",
                    "Contributor to open-source projects like NeuroServe and RepoSmith."
                ]

                # ----- صورة شخصية (تشفير داخل JSON) -----
                avatar = None
                if st.session_state.get("photo_bytes"):
                    b64 = base64.b64encode(st.session_state.photo_bytes).decode("ascii")
                    avatar = {
                        "bytes_b64": b64,
                        "mime": st.session_state.get("photo_mime") or "image/png",
                        "name": st.session_state.get("photo_name") or "photo.png",
                    }

                # ----- JSON النهائي الذي يتوقعه الباكند -----
                payload = {
                    "theme_name": theme_name,
                    "ui_lang": "en",          # اضبطها إلى "ar" عند الحاجة
                    "rtl_mode": rtl_mode,
                    "profile": {
                        "header": {"name": name, "title": title},
                        "contact": {
                            "email": email,
                            "phone": phone,
                            "github": github,
                            "linkedin": linkedin,
                            "location": location,
                        },
                        "skills": skills,
                        "languages": languages,
                        "projects": projects,      # [[title, desc, link], ...]
                        "summary": summary_lines,  # [ ... ]
                        "avatar": avatar,          # اختياري؛ قد يتجاهله الباكند إن لم يدعمه
                    },
                }

                # ----- استدعاء الـ API (application/json) -----
                pdf_bytes = post_generate_form(
                    api_base=(st.session_state.api_base or get_api_base()),
                    payload=payload,
                )

                # ----- حفظ النتيجة في الحالة -----
                st.session_state.pdf_bytes = pdf_bytes
                ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                st.session_state.pdf_name = f"resume-{theme_name}-{ts}.pdf"

                st.success(f"✅ PDF generated successfully using '{theme_name}' theme.")

            except Exception as e:
                st.error(f"Generation failed: {e}")

    # ===== مسح الحقول =====
    with colg2:
        st.button("Clear form", on_click=_request_reset)

    # ===== تحميل الملف =====
    with colg3:
        if st.session_state.pdf_bytes:
            out_path = outputs_dir / st.session_state.pdf_name
            try:
                out_path.write_bytes(st.session_state.pdf_bytes)
            except Exception:
                pass
            st.download_button(
                "Download PDF",
                data=st.session_state.pdf_bytes,
                file_name=st.session_state.pdf_name,
                mime="application/pdf",
            )
        else:
            st.caption("The download button appears after generating a PDF.")

    st.caption("Tip: Adjust the API base URL from the sidebar if your FastAPI runs on another address/port.")
