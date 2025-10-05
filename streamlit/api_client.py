# streamlit/api_client.py
import requests

API_BASE = "http://127.0.0.1:8000"

def generate_pdf(profile: dict, theme_name: str, layout_name: str | None, ui_lang: str, rtl_mode: bool, use_simple_json: bool = True) -> bytes:
    payload = {
        "theme_name": theme_name,
        "layout_name": layout_name,
        "ui_lang": ui_lang,
        "rtl_mode": rtl_mode,
        "profile": profile or {},  # مهم
    }

    if use_simple_json:
        # ✅ أرسل JSON إلى /generate-form-simple
        r = requests.post(f"{API_BASE}/generate-form-simple", json=payload, timeout=60)
    else:
        # (توافق قديم) multipart إلى /generate-form
        files = {}
        data = {
            "theme_name": theme_name,
            "layout_name": layout_name or "",
            "ui_lang": ui_lang,
            "rtl_mode": str(bool(rtl_mode)).lower(),
            "profile_json": __import__("json").dumps(profile or {}),
        }
        r = requests.post(f"{API_BASE}/generate-form", data=data, files=files, timeout=60)

    r.raise_for_status()
    return r.content
