from __future__ import annotations
import os
from pathlib import Path
import streamlit as st

from sidebar import render_sidebar
from tabs.basic_info import render_basic_info
from tabs.headshot import render_headshot
from tabs.blocks import render_blocks
from tabs.skills_lang import render_skills_languages
from tabs.generate import render_generate_actions
from utils import init_defaults, DEFAULTS

# Page setup
st.set_page_config(page_title="Resume PDF Builder", page_icon="🧾", layout="centered")
st.title("🧾 Resume PDF Builder")
st.caption(
    "Fill in any fields (all optional) then click Generate PDF. "
    "You can save/load a JSON profile and attach a headshot to embed into the PDF."
)

# Paths for saving profiles and outputs
BASE_DIR = Path(__file__).resolve().parents[1]
PROFILES_DIR = BASE_DIR / "profiles"
OUTPUTS_DIR = BASE_DIR / "outputs"
PROFILES_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# Session defaults
init_defaults()

# Handle deferred reset BEFORE widgets (no st.rerun inside callbacks)
if st.session_state.get("_reset_requested", False):
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.pop("_reset_requested", None)
    st.toast("Form cleared.", icon="🧹")

# Sidebar (API & JSON load/save)
render_sidebar(PROFILES_DIR)

# Tabs
tab_titles = [
    "Basic Info",
    "Headshot",
    "Blocks",
    "Skills & Languages",
    "Generate / Download",
]
t1, t2, t3, t4, t5 = st.tabs(tab_titles)

with t1:
    render_basic_info()

with t2:
    render_headshot()

with t3:
    render_blocks()

with t4:
    render_skills_languages()

with t5:
    render_generate_actions(OUTPUTS_DIR)

st.divider()
st.caption("Tip: Adjust the API base URL from the sidebar if your FastAPI runs on another address/port.")
