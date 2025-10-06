from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _norm_projects(projects_list: List[Any]) -> List[Tuple[str, str, Optional[str]]]:
    """
    Normalize various forms of project entries into a consistent tuple format:
    (title, description, optional link).
    """
    out: List[Tuple[str, str, Optional[str]]] = []
    for it in projects_list or []:
        if isinstance(it, (list, tuple)) and it:
            title = (it[0] or "").strip() if len(it) > 0 else ""
            desc = (it[1] or "").strip() if len(it) > 1 else ""
            link = (it[2] or "").strip() if len(it) > 2 else None
        elif isinstance(it, dict):
            title = (it.get("title") or "").strip()
            desc = (it.get("desc") or it.get("description") or "").strip()
            link = (it.get("link") or "").strip() or None
        else:
            title, desc, link = "", "", None
        if title or desc or link:
            out.append((title, desc, link))
    return out


def _read_bytes_if_exists(pathlike: str | Path | None) -> bytes | None:
    """
    Safely read bytes from a file if it exists and is a file.
    """
    if not pathlike:
        return None
    p = Path(pathlike)
    if p.exists() and p.is_file():
        try:
            return p.read_bytes()
        except Exception:
            return None
    return None


def build_ready_from_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a data-ready dictionary from a standardized profile structure.

    Recognized profile keys include:
    - header: {name, title}
    - avatar: {path}
    - contact: {email, phone, location, github, linkedin, ...}
    - skills: list of skills
    - languages: list of language strings
    - projects: list of tuples or dicts (title, desc, link)
    - education: list of educational entries
    - summary: list of summary lines

    Additional optional sections supported:
    - experience, objective, activities, volunteer, achievements, publications
    """
    header = profile.get("header") or {}
    name = (header.get("name") or "").strip()
    title = (header.get("title") or "").strip()

    avatar = profile.get("avatar") or {}
    photo_bytes = _read_bytes_if_exists(avatar.get("path"))

    contact = dict(profile.get("contact") or {})
    skills = list(profile.get("skills") or [])
    languages = list(profile.get("languages") or [])
    projects_list = list(profile.get("projects") or [])
    education_items = list(profile.get("education") or [])
    summary_lines = list(profile.get("summary") or [])

    norm_projects = _norm_projects(projects_list)

    # Extract known social links from contact section
    social: Dict[str, str] = {}
    for k, v in (contact or {}).items():
        kl = str(k).lower()
        if kl in {"github", "linkedin", "website", "site", "url", "twitter", "x"}:
            social[k] = str(v)

    ready: Dict[str, Any] = {
        "header_name": {"name": name, "title": title},
        "avatar_circle": {"photo_bytes": photo_bytes, "max_d_mm": 42},
        "contact_info": {"items": contact},
        "key_skills": {"skills": skills},
        "languages": {"languages": languages},
        "social_links": social,
        "projects": {"items": norm_projects, "title": None},
        "education": {"items": education_items, "title": None},
        "text_section:summary": {"title": "", "lines": summary_lines},
        "experience": {"items": profile.get("experience") or []},
        "objective": {"lines": profile.get("objective") or []},
        "activities": {"lines": profile.get("activities") or []},
        "rule": {},
        "header_bar": {},
        "links_inline": {},
        "decor_curve": {},
        "skills_grid": {},
        "volunteer": {"items": profile.get("volunteer") or []},
        "achievements": {"items": profile.get("achievements") or []},
        "publications": {"items": profile.get("publications") or []},
    }
    return ready