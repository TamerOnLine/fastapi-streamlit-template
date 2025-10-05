# api/pdf_utils/utils.py
from __future__ import annotations
from typing import List, Tuple

def _split_lines(text: str) -> List[str]:
    """تفكيك نص متعدد الأسطر إلى قائمة، مع تنظيف المسافات الفارغة."""
    if not text:
        return []
    return [ln.strip() for ln in str(text).splitlines() if ln.strip()]

def _parse_projects(lines: List[str]) -> List[Tuple[str, str, str]]:
    """
    يحوّل قائمة أسطر مشاريع إلى شكل موحّد: [(title, desc, url), ...]
    يقبل صيغتين:
      - سطر مفصول بـ ' | '  -> Title | Description | URL
      - أو سطر واحد بدون |  -> يعامل كعنوان فقط.
    """
    projects: List[Tuple[str, str, str]] = []
    for raw in lines or []:
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) >= 3:
            title, desc, url = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            title, desc = parts[0], parts[1]
            url = ""
        else:
            title, desc, url = raw.strip(), "", ""
        if title:
            projects.append((title, desc, url))
    return projects
