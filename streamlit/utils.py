from __future__ import annotations
import base64
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import streamlit as st

DEFAULTS: Dict[str, object] = {
    "name": "",
    "location": "",
    "phone": "",
    "email": "",
    "github": "",
    "linkedin": "",
    "birthdate": "",
    "skills_text": "",
    "languages_text": "",
    "projects_text": "",
    "education_text": "",
    "sections_left_text": "",
    "sections_right_text": "",
    "rtl_mode": False,
    "api_base": os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
    # photo
    "photo_bytes": None,
    "photo_mime": None,
    "photo_name": None,
    # pdf
    "pdf_bytes": None,
    "pdf_name": "resume.pdf",
}

def init_defaults() -> None:
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)

def atomic_write_json(path: Path, payload: Dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)

def guess_mime_from_name(name: str | None) -> str:
    if not name:
        return "image/png"
    n = name.lower()
    if n.endswith(".jpg") or n.endswith(".jpeg"):
        return "image/jpeg"
    if n.endswith(".webp"):
        return "image/webp"
    return "image/png"

def encode_photo_to_b64(
    photo_bytes: Optional[bytes],
    photo_mime: Optional[str],
    photo_name: Optional[str],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if not photo_bytes:
        return None, None, None
    return base64.b64encode(photo_bytes).decode("ascii"), (photo_mime or "image/png"), (photo_name or "photo.png")

def decode_photo_from_b64(photo_b64: str, photo_mime: Optional[str]) -> bytes:
    return base64.b64decode(photo_b64.encode("ascii"))
