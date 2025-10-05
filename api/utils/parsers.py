"""
Parsing utilities for structured user input.
Supports CSV lines, CEFR language levels, block sections, and more.
"""

from __future__ import annotations
from typing import Optional, List, Tuple
import re


def parse_csv_or_lines(txt: str) -> List[str]:
    """
    Splits a string by commas or line breaks into a list of items.

    Args:
        txt (str): Raw text input.

    Returns:
        List[str]: Cleaned list of values.
    """
    if not txt:
        return []
    parts: List[str] = []
    for line in txt.replace(",", "\n").splitlines():
        s = line.strip()
        if s:
            parts.append(s)
    return parts


def normalize_language_level(label: str) -> str:
    """
    Converts CEFR levels (A1..C2) into neutral German-style phrasing.

    Args:
        label (str): Input label like 'Deutsch - B1'.

    Returns:
        str: Reformatted string like 'Deutsch – Gute Kenntnisse'.
    """
    s = (label or "").strip()
    mapping = {
        "a1": "Grundkenntnisse",
        "a2": "Grundkenntnisse",
        "b1": "Gute Kenntnisse",
        "b2": "Gute Kenntnisse",
        "c1": "Sehr gute Kenntnisse",
        "c2": "Verhandlungssicher",
    }
    m = re.search(r"(?i)^(.+?)\s*[-\u2013:]\s*([abc][12])\b", s)
    if m:
        lang = m.group(1).strip()
        lvl = m.group(2).lower()
        return f"{lang} – {mapping.get(lvl, m.group(2))}"
    return s


def parse_sections(text: str) -> List[dict]:
    """
    Parses a sectioned block of text.

    Expected format:
        [Title]
        - line 1
        - line 2

    Args:
        text (str): Raw input text.

    Returns:
        List[dict]: List of sections with 'title' and 'lines'.
    """
    sections: List[dict] = []
    cur = {"title": "", "lines": []}
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            if cur["title"] and cur["lines"]:
                sections.append(cur)
            cur = {"title": "", "lines": []}
            continue
        if line.startswith("[") and line.endswith("]"):
            if cur["title"] and cur["lines"]:
                sections.append(cur)
            cur = {"title": line.strip("[]").strip(), "lines": []}
        elif line.startswith("-"):
            cur["lines"].append(line[1:].strip())
    if cur["title"] and cur["lines"]:
        sections.append(cur)
    return sections


def parse_simple_list(txt: str) -> List[str]:
    """
    Parses each line as a list item, skipping empty lines.

    Args:
        txt (str): Raw input.

    Returns:
        List[str]: Cleaned list.
    """
    out: List[str] = []
    for line in (txt or "").splitlines():
        s = line.strip()
        if s:
            out.append(s)
    return out


def parse_projects_blocks(txt: str) -> List[Tuple[str, str, Optional[str]]]:
    """
    Parses projects from text blocks. First line is title, rest is description.

    Returns:
        List[Tuple[str, str, Optional[str]]]: Title, description, and optional link.
    """
    blocks: List[Tuple[str, str, Optional[str]]] = []
    cur_title, cur_desc, cur_link = "", [], None

    def flush():
        nonlocal cur_title, cur_desc, cur_link
        if cur_title or cur_desc or cur_link:
            blocks.append((cur_title.strip(), "\n".join(cur_desc).strip(), cur_link))
        cur_title, cur_desc, cur_link = "", [], None

    for raw in (txt or "").splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if not cur_title:
            cur_title = line
        elif line.startswith("http://") or line.startswith("https://"):
            cur_link = line
        else:
            cur_desc.append(line)

    flush()
    return blocks


def parse_sections_text(txt: str) -> List[dict]:
    """
    Parses enhanced sections with optional bullets and free-text grouping.

    Returns:
        List[dict]: Sections with title and associated lines.
    """
    sections: List[dict] = []
    title: Optional[str] = None
    lines: List[str] = []

    def flush():
        nonlocal title, lines
        if title and lines:
            sections.append({"title": title, "lines": lines[:]})
        title, lines = None, []

    for raw in (txt or "").splitlines():
        s = raw.strip()
        if not s:
            flush()
            continue
        if s.startswith("[") and s.endswith("]"):
            flush()
            title = s[1:-1].strip()
        elif s[:1] in "-•–":
            lines.append(s[1:].strip())
        else:
            if lines:
                lines[-1] += " " + s
            else:
                title = title or s
    flush()
    return sections


def parse_education_blocks(txt: str) -> List[str]:
    """
    Splits education content into blocks separated by blank lines.

    Returns:
        List[str]: List of education blocks preserving internal lines.
    """
    blocks: List[str] = []
    cur: List[str] = []
    for raw in (txt or "").splitlines():
        ln = raw.rstrip()
        if not ln.strip():
            if cur:
                blocks.append("\n".join(cur))
                cur = []
        else:
            cur.append(ln)
    if cur:
        blocks.append("\n".join(cur))
    return blocks
