from __future__ import annotations
from typing import Dict, Optional, Tuple
import requests

def get_api_base() -> str:
    return "http://127.0.0.1:8000"

def post_generate_form(
    api_base: str,
    data: Dict[str, str],
    photo_tuple: Optional[Tuple[bytes, str, str]] = None,
) -> bytes:
    """
    Sends multipart/form-data to FastAPI endpoint /generate-pdf
    data: flat dict of text fields
    photo_tuple: (bytes, mime, filename) or None
    """
    url = f"{api_base.rstrip('/')}/generate-form"
    files = {}
    if photo_tuple:
        content, mime, fname = photo_tuple
        files["photo"] = (fname, content, mime)

    resp = requests.post(url, data=data, files=files, timeout=120)
    resp.raise_for_status()
    return resp.content
