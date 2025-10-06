from __future__ import annotations

from typing import List, Tuple

def _split_lines(text: str) -> List[str]:
    """
    Split a multiline string into individual lines, trimming whitespace.

    Args:
        text (str): Multiline string.

    Returns:
        List[str]: List of cleaned, non-empty lines.
    """
    if not text:
        return []
    return [ln.strip() for ln in str(text).splitlines() if ln.strip()]

def _parse_projects(lines: List[str]) -> List[Tuple[str, str, str]]:
    """
    Convert project lines into a uniform structure of (title, description, URL).

    Supported formats:
      - 'Title | Description | URL'
      - 'Title | Description'
      - 'Title' (title only)

    Args:
        lines (List[str]): List of raw project lines.

    Returns:
        List[Tuple[str, str, str]]: List of project tuples.
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