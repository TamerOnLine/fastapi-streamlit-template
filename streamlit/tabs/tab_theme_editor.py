# streamlit/tabs/tab_theme_editor.py
from __future__ import annotations
import json
from pathlib import Path
import streamlit as st

THEMES_DIR = Path("themes")

DEFAULT_BLOCKS = [
    "header_name", "avatar_circle", "contact_info", "social_links",
    "languages", "key_skills", "text_section", "projects", "education"
]

def render_theme_editor(api_base_url: str):
    st.header("🎨 Theme Editor (Dynamic)")

    # === Basic Page Setup ===
    c1, c2, c3 = st.columns(3)
    with c1:
        page_size = st.selectbox("Page Size", ["A4"], index=0)
    with c2:
        m_left  = st.number_input("Margin Left (mm)",  min_value=8, value=16)
        m_right = st.number_input("Margin Right (mm)", min_value=8, value=16)
    with c3:
        m_top    = st.number_input("Margin Top (mm)",    min_value=8, value=16)
        m_bottom = st.number_input("Margin Bottom (mm)", min_value=8, value=16)

    # === Style ===
    st.subheader("Style")
    s1, s2, s3 = st.columns(3)
    with s1:
        heading_color = st.color_picker("HEADING_COLOR", "#0EA5B7")
    with s2:
        subhead_color = st.color_picker("SUBHEAD_COLOR", "#0B7285")
    with s3:
        rule_color    = st.color_picker("RULE_COLOR", "#CFE9EF")

    t1, t2, t3 = st.columns(3)
    with t1:
        name_size = st.number_input("NAME_SIZE", min_value=12, value=26)
    with t2:
        text_size = st.number_input("TEXT_SIZE", min_value=8, value=10)
    with t3:
        gap_rt = st.number_input("RIGHT_SEC_RULE_TO_TEXT_GAP", min_value=6, value=12)

    # === Columns (2 or 3) ===
    st.subheader("Columns")
    col_count = st.radio("Number of Columns", [2, 3], horizontal=True, index=1)

    if col_count == 2:
        l_w = st.number_input("Left Column Width (mm)", min_value=40, value=60)
        gap = st.number_input("Gap (mm)", min_value=4, value=8)
        columns_cfg = [
            {"id": "left", "w_mm": l_w, "gap_right_mm": gap},
            {"id": "right", "flex": 1}
        ]
    else:
        cA, cB, cC = st.columns(3)
        with cA:
            w_left = st.number_input("Left w_mm", min_value=40, value=58)
            gap_L  = st.number_input("Left gap_right_mm", min_value=0, value=8)
        with cB:
            w_mid = st.number_input("Middle w_mm", min_value=40, value=58)
            gap_M = st.number_input("Middle gap_right_mm", min_value=0, value=8)
        with cC:
            flex_right = st.checkbox("Right is FLEX (auto)", value=True)
        columns_cfg = [
            {"id": "left",   "w_mm": w_left, "gap_right_mm": gap_L, "bg_block": "left_panel_bg"},
            {"id": "middle", "w_mm": w_mid,  "gap_right_mm": gap_M},
            {"id": "right",  ("flex" if flex_right else "w_mm"):
                (1 if flex_right else 58)}
        ]

    # === Blocks ordering per column ===
    st.subheader("Blocks & Ordering")
    st.caption("Assign blocks to columns and order them (top → bottom).")

    default_left   = ["avatar_circle", "contact_info", "social_links", "languages"]
    default_middle = ["key_skills", "text_section"]
    default_right  = ["header_name", "projects", "education"]

    col_ids = [c["id"] for c in columns_cfg]
    col_tabs = st.tabs([f"Column: {cid}" for cid in col_ids])
    chosen = {}

    for tab, cid in zip(col_tabs, col_ids):
        with tab:
            initial = (
                default_left if cid == "left"
                else default_middle if cid == "middle"
                else default_right
            )
            blocks = st.multiselect("Blocks", DEFAULT_BLOCKS, default=initial, key=f"blocks_{cid}")
            # ترتيب بسيط: up/down
            order = blocks[:]  # يمكن لاحقًا دمج data_editor أو drag&drop
            st.write("Order:", " → ".join(order))
            chosen[cid] = order

    # === Defaults ===
    st.subheader("Defaults")
    ui_lang = st.selectbox("UI Language", ["en", "ar", "de"], index=0)
    rtl_mode = st.checkbox("RTL Mode", value=False)

    # Build theme dict
    theme = {
        "page": {
            "size": page_size,
            "margins_mm": {"top": m_top, "right": m_right, "bottom": m_bottom, "left": m_left}
        },
        "style": {
            "HEADING_COLOR": heading_color,
            "SUBHEAD_COLOR": subhead_color,
            "RULE_COLOR": rule_color,
            "NAME_SIZE": name_size,
            "TEXT_SIZE": text_size,
            "RIGHT_SEC_RULE_TO_TEXT_GAP": gap_rt
        },
        "columns": columns_cfg,
        "layout": [],
        "defaults": {"ui_lang": ui_lang, "rtl_mode": rtl_mode}
    }

    # Merge chosen blocks into layout
    for cid, blocks in chosen.items():
        for b in blocks:
            item = {"block_id": b, "col": cid}
            if b == "header_name":
                item["data"] = {"centered": True, "highlight_bg": "#E0F2FE", "box_h_mm": 28}
            theme["layout"].append(item)

    # Save / Preview
    save_name = st.text_input("Save as theme file", value="my-dynamic.theme.json")
    csave, cprev = st.columns([1, 1])

    with csave:
        if st.button("💾 Save Theme"):
            THEMES_DIR.mkdir(parents=True, exist_ok=True)
            path = THEMES_DIR / save_name
            path.write_text(json.dumps(theme, indent=2), encoding="utf-8")
            st.success(f"Saved: {path}")

    with cprev:
        if st.button("⚡ Generate PDF with this Theme"):
            # استدعاء مسار التوليد في FastAPI بنفس فورماتك الحالية
            import requests
            payload = {
                "theme_inline": theme,   # نرسل الثيم ضمن الطلب لتجربة فورية
                "profile": {
                    "name": "Tamer Hamad Faour",
                    "summary": ["Backend Developer (FastAPI, PostgreSQL)", "Open-source contributor"],
                    "projects": [
                        ["NeuroServe", "GPU-ready FastAPI AI inference server", "https://github.com/..."],
                        ["RepoSmith", "Project bootstrapper CLI", "https://github.com/..."]
                    ],
                    "education": [
                        "2020–2022 — CS Diploma — Example Institute"
                    ],
                    "skills": ["FastAPI", "PostgreSQL", "Streamlit", "ReportLab"],
                    "languages": ["Arabic — Native", "English — B1", "German — A2"],
                    "contacts": {
                        "email": "tamer@example.com",
                        "phone": "+49 123 456",
                        "location": "Berlin"
                    }
                }
            }
            try:
                r = requests.post(f"{api_base_url}/generate-form", json=payload, timeout=60)
                if r.ok:
                    st.success("PDF generated.")
                    st.download_button("⬇ Download PDF", r.content, file_name="resume-preview.pdf")
                else:
                    st.error(f"Failed: {r.status_code} {r.text[:200]}")
            except Exception as e:
                st.error(repr(e))
