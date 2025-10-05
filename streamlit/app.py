# streamlit/app.py
from __future__ import annotations
import os
from pathlib import Path
import streamlit as st

# استيراد الوظائف الفرعية من المشروع الحالي
from sidebar import render_sidebar
from tabs.basic_info import render_basic_info
from tabs.headshot import render_headshot
from tabs.blocks import render_blocks
from tabs.skills_lang import render_skills_languages
from tabs.generate import render_generate_actions
from utils import init_defaults, DEFAULTS

# -------------------------------------------------------------------
# 📄 إعداد الصفحة العامة
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Resume PDF Builder",
    page_icon="🧾",
    layout="centered",
)

st.title("🧾 Resume PDF Builder")
st.caption(
    "Fill in your info, select a theme and layout, then click **Generate PDF**.\n"
    "You can save/load profiles (JSON) and include a photo for the header."
)

# -------------------------------------------------------------------
# 📂 تهيئة المسارات الأساسية (للتخزين)
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
PROFILES_DIR = BASE_DIR / "profiles"
OUTPUTS_DIR = BASE_DIR / "outputs"
PROFILES_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------------------
# ⚙️ إعداد القيم الافتراضية للجلسة
# -------------------------------------------------------------------
init_defaults()

# عند الضغط على زر Reset من الشريط الجانبي
if st.session_state.get("_reset_requested", False):
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.pop("_reset_requested", None)
    st.toast("Form cleared successfully 🧹", icon="🧼")

# -------------------------------------------------------------------
# 🧭 الشريط الجانبي (Sidebar)
# -------------------------------------------------------------------
render_sidebar(PROFILES_DIR)

# -------------------------------------------------------------------
# 🧩 التبويبات الرئيسية
# -------------------------------------------------------------------
tab_titles = [
    "Basic Info",
    "Headshot",
    "Blocks",
    "Skills & Languages",
    "Generate / Download",
]
t1, t2, t3, t4, t5 = st.tabs(tab_titles)

# --------------------------------------------------
# 🧱 التبويب 1: المعلومات الأساسية
# --------------------------------------------------
with t1:
    render_basic_info()

# --------------------------------------------------
# 🖼️ التبويب 2: الصورة الشخصية
# --------------------------------------------------
with t2:
    render_headshot()

# --------------------------------------------------
# 📦 التبويب 3: الكتل (Projects, Education, etc.)
# --------------------------------------------------
with t3:
    render_blocks()

# --------------------------------------------------
# 🗣️ التبويب 4: المهارات واللغات
# --------------------------------------------------
with t4:
    render_skills_languages()

# --------------------------------------------------
# 🧾 التبويب 5: توليد وتحميل السيرة الذاتية
# --------------------------------------------------
with t5:
    render_generate_actions(OUTPUTS_DIR)

# -------------------------------------------------------------------
# 🪶 فاصل سفلي وملاحظات
# -------------------------------------------------------------------
st.divider()
st.caption(
    "💡 Tip: You can adjust the FastAPI base URL from the sidebar if your server runs on another address/port.\n"
    "Dynamic themes and layouts are now supported — experiment freely!"
)
