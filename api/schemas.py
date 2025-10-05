# api/schemas.py
from pydantic import BaseModel
from typing import Any, Dict, Optional


class GeneratePayload(BaseModel):
    """
    مخطط الطلب الرئيسي لتوليد PDF
    """
    theme_name: str
    layout_name: Optional[str] = None
    ui_lang: Optional[str] = "en"
    rtl_mode: Optional[bool] = False
    profile: Dict[str, Any]
