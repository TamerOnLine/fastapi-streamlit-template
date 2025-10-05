from __future__ import annotations
from typing import Dict
import json
import requests

def get_api_base() -> str:
    # يمكنك تغيير القيمة الافتراضية من الشريط الجانبي أيضاً
    return "http://127.0.0.1:8000"

def post_generate_form(api_base: str, payload: Dict) -> bytes:
    """
    يرسل application/json إلى FastAPI عند /generate-form
    payload: قاموس JSON مطابق لما يتوقعه الباكند:
      {
        "theme_name": "...",
        "ui_lang": "en" | "ar" | "de",
        "rtl_mode": bool,
        "profile": { ... }
      }
    """
    url = f"{api_base.rstrip('/')}/generate-form"
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, data=json.dumps(payload, ensure_ascii=False), headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.content
