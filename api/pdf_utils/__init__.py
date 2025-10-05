# api/pdf_utils/__init__.py
from . import blocks  # <-- مهم: استيراد جانبي لتسجيل كل الكتل
from .resume import build_resume_pdf

__all__ = ["build_resume_pdf"]
