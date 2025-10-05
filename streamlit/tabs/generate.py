# streamlit/tabs/generate.py
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
import base64
import json
import streamlit as st

from api_client import get_api_base, post_generate_form


# ======================= Utilities =======================

def list_themes() -> list[str]:
    """Scan themes/*.theme.json and return stems (e.g., 'aqua-card-3col.theme')."""
    p = Path.cwd() / "themes"
    if p.is_dir():
        names = [f.stem for f in p.glob("*.theme.json")]
        if names:
            return sorted(set(names))
    return []

def list_layouts() -> list[str]:
    """Scan layouts/*.layout.json and return stems (e.g., 'three-column.layout')."""
    p = Path.cwd() / "layouts"
    if p.is_dir():
        names = [f.stem for f in p.glob("*.layout.json")]
        if names:
            return sorted(set(names))
    return []

def _split_nonempty_lines(text: str) -> List[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

def _parse_projects(lines: List[str]) -> List[Tuple[str, str, str]]:
    """
    Parse each line into (title, desc, link):
      1) "title | desc | link"
      2) "title - desc"   (no link)
      3) "title"          (title only)
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

def _build_profile_from_state() -> dict:
    """Fallback profile builder if no JSON payload provided elsewhere."""
    name     = st.session_state.get("name", "").strip()
    title    = st.session_state.get("title", "").strip() if "title" in st.session_state else ""
    email    = st.session_state.get("email", "").strip()
    phone    = st.session_state.get("phone", "").strip()
    github   = st.session_state.get("github", "").strip()
    linkedin = st.session_state.get("linkedin", "").strip()
    location = st.session_state.get("location", "").strip()

    skills           = _split_nonempty_lines(st.session_state.get("skills_text", ""))
    languages        = _split_nonempty_lines(st.session_state.get("languages_text", ""))
    projects_blocks  = _split_nonempty_lines(st.session_state.get("projects_text", ""))
    education_blocks = _split_nonempty_lines(st.session_state.get("education_text", ""))

    projects = [[p, "", ""] for p in projects_blocks]  # simple mapping; improve later if needed

    # Optional avatar
    avatar = None
    if st.session_state.get("photo_bytes"):
        b64 = base64.b64encode(st.session_state.photo_bytes).decode("ascii")
        avatar = {
            "bytes_b64": b64,
            "mime": st.session_state.get("photo_mime") or "image/png",
            "name": st.session_state.get("photo_name") or "photo.png",
        }

    profile = {
        "header": {"name": name, "title": title},
        "contact": {"email": email, "phone": phone, "github": github, "linkedin": linkedin, "location": location},
        "skills": skills,
        "languages": languages,
        "projects": projects,
        "education": education_blocks,
        "avatar": avatar,
    }
    return profile

def _resolve_profile_payload() -> dict:
    """Prefer a ready JSON profile injected by other tabs; fallback to state."""
    pj = st.session_state.get("profile_json")
    if isinstance(pj, dict) and pj:
        return pj
    return _build_profile_from_state()

def _request_reset():
    st.session_state["_reset_requested"] = True


# ======================= Main Entry =======================

def render_generate_actions(outputs_dir: Path) -> None:
    st.header("Generate & Download")

    # ---- scan available themes/layouts ----
    themes = list_themes()
    layouts = list_layouts()

    if not themes:
        st.error("لم يتم العثور على أي ملفات Theme في مجلد themes/*.theme.json")
        return
    if not layouts:
        st.error("لم يتم العثور على أي ملفات Layout في مجلد layouts/*.layout.json")
        return

    # ---- unique keys for this tab to avoid collision with other widgets ----
    K_THEME  = "gen_theme_name"
    K_LAYOUT = "gen_layout_name"
    K_LANG   = "gen_ui_lang"
    K_RTL    = "gen_rtl_mode"

    # ---- one-time defaults (do NOT assign after widgets are created) ----
    default_theme = "aqua-card-3col.theme" if "aqua-card-3col.theme" in themes else themes[0]
    default_layout = "three-column.layout" if "three-column.layout" in layouts else layouts[0]
    st.session_state.setdefault(K_THEME, default_theme)
    st.session_state.setdefault(K_LAYOUT, default_layout)
    st.session_state.setdefault(K_LANG, "ar")
    st.session_state.setdefault(K_RTL, True)

    # ---- widgets with unique keys ----
    st.subheader("اختيار Theme و Layout")
    colA, colB = st.columns(2)
    with colA:
        st.selectbox(
            "🎨 Theme",
            themes,
            index=themes.index(st.session_state[K_THEME]) if st.session_state[K_THEME] in themes else 0,
            help="الثيم يحدد الألوان والخطوط والهوية البصرية.",
            key=K_THEME,
        )
    with colB:
        st.selectbox(
            "🧱 Layout",
            layouts,
            index=layouts.index(st.session_state[K_LAYOUT]) if st.session_state[K_LAYOUT] in layouts else 0,
            help="اللاياوت يحدد الأعمدة وترتيب البلوكات على الصفحة.",
            key=K_LAYOUT,
        )

    colL, colR = st.columns(2)
    with colL:
        st.selectbox(
            "UI language",
            ["ar", "en", "de"],
            index=["ar", "en", "de"].index(st.session_state[K_LANG]) if st.session_state[K_LANG] in ["ar", "en", "de"] else 0,
            key=K_LANG,
        )
    with colR:
        st.toggle(
            "RTL mode",
            value=st.session_state[K_RTL],
            help="فعّلها عند استخدام العربية.",
            key=K_RTL,
        )

    # Pull local copies
    theme_name  = st.session_state[K_THEME]
    layout_name = st.session_state[K_LAYOUT]
    ui_lang     = st.session_state[K_LANG]
    rtl_mode    = bool(st.session_state[K_RTL])

    # ---- preview payload (debug) ----
    with st.expander("Preview payload (debug)"):
        preview_payload = {
            "theme_name": theme_name,
            "layout_name": layout_name,
            "ui_lang": ui_lang,
            "rtl_mode": rtl_mode,
            "profile": _resolve_profile_payload(),
        }
        st.code(json.dumps(preview_payload, ensure_ascii=False, indent=2), language="json")

    # ---- action buttons ----
    colg1, colg2, colg3 = st.columns(3)

    # Generate
    with colg1:
        if st.button("Generate PDF", type="primary"):
            try:
                payload = {
                    "theme_name": theme_name,
                    "layout_name": layout_name,  # critical to enable columns
                    "ui_lang": ui_lang,
                    "rtl_mode": rtl_mode,
                    "profile": _resolve_profile_payload(),
                }

                pdf_bytes = post_generate_form(
                    api_base=(st.session_state.get("api_base") or get_api_base()),
                    payload=payload,
                )

                st.session_state["pdf_bytes"] = pdf_bytes
                ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                safe_theme = theme_name.replace("/", "_")
                st.session_state["pdf_name"] = f"resume-{safe_theme}-{ts}.pdf"

                st.success(
                    f"✅ PDF generated successfully using Theme='{theme_name}' & Layout='{layout_name}'."
                )
            except Exception as e:
                st.error(f"Generation failed: {e}")

    # Clear
    with colg2:
        st.button("Clear form", on_click=_request_reset)

    # Download
    with colg3:
        if st.session_state.get("pdf_bytes"):
            out_path = outputs_dir / st.session_state["pdf_name"]
            try:
                out_path.write_bytes(st.session_state["pdf_bytes"])
            except Exception:
                pass
            st.download_button(
                "Download PDF",
                data=st.session_state["pdf_bytes"],
                file_name=st.session_state["pdf_name"],
                mime="application/pdf",
            )
        else:
            st.caption("The download button appears after generating a PDF.")

    st.caption("Tip: Theme يضبط الشكل، Layout يوزّع الأعمدة. اضبط API base من الشريط الجانبي إذا لزم.")
