from __future__ import annotations
from pathlib import Path
import json
import streamlit as st
from utils import (
    atomic_write_json,
    encode_photo_to_b64,
    decode_photo_from_b64,
)

def render_sidebar(profiles_dir: Path) -> None:
    with st.sidebar:
        st.subheader("API")
        st.text_input("API Base URL", key="api_base", help="Example: http://127.0.0.1:8000")

        st.subheader("Profile JSON")
        uploaded_json = st.file_uploader("Browse JSON", type=["json"], key="json_uploader")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Load uploaded"):
                if uploaded_json:
                    try:
                        data = json.load(uploaded_json)
                        # simple fields
                        for k in [
                            "name","location","phone","email","github","linkedin","birthdate",
                            "skills_text","languages_text","projects_text","education_text",
                            "sections_left_text","sections_right_text","rtl_mode"
                        ]:
                            if k in data:
                                st.session_state[k] = data[k]

                        # photo
                        photo_b64 = data.get("photo_b64")
                        photo_mime = data.get("photo_mime")
                        photo_name = data.get("photo_name")
                        if photo_b64:
                            st.session_state.photo_bytes = decode_photo_from_b64(photo_b64, photo_mime)
                            st.session_state.photo_mime = photo_mime or "image/png"
                            st.session_state.photo_name = photo_name or "photo.png"
                        st.success("JSON loaded.")
                    except Exception as e:
                        st.error(f"Invalid JSON: {e}")
                else:
                    st.warning("No file selected.")

        with col2:
            if st.button("Save current"):
                b64, mime, name = encode_photo_to_b64(
                    st.session_state.photo_bytes,
                    st.session_state.photo_mime,
                    st.session_state.photo_name,
                )
                payload = {
                    "name": st.session_state.name,
                    "location": st.session_state.location,
                    "phone": st.session_state.phone,
                    "email": st.session_state.email,
                    "github": st.session_state.github,
                    "linkedin": st.session_state.linkedin,
                    "birthdate": st.session_state.birthdate,
                    "skills_text": st.session_state.skills_text,
                    "languages_text": st.session_state.languages_text,
                    "projects_text": st.session_state.projects_text,
                    "education_text": st.session_state.education_text,
                    "sections_left_text": st.session_state.sections_left_text,
                    "sections_right_text": st.session_state.sections_right_text,
                    "rtl_mode": bool(st.session_state.rtl_mode),
                    "photo_b64": b64,
                    "photo_mime": mime,
                    "photo_name": name,
                }
                from datetime import datetime
                ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                out = profiles_dir / f"profile-{ts}.json"
                atomic_write_json(out, payload)
                st.success(f"Saved: {out.name}")
