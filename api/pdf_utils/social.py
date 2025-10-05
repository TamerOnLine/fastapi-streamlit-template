"""
Utility for extracting and normalizing GitHub and LinkedIn handles from raw input.
Supports direct handles or full URLs with optional prefixes.
"""

import re


def extract_social_handle(kind: str, value: str):
    """
    Extracts a clean social media handle and constructs the full profile URL.

    Supports:
    - Plain handles (with or without '@')
    - Full URLs (with or without https/www)
    - Prefixed entries like "GitHub: user"

    Args:
        kind (str): Platform type - either "GitHub" or "LinkedIn".
        value (str): Raw input from the user.

    Returns:
        tuple[str, str] | None: A tuple of (handle, full URL), or None if invalid.
    """
    v = (value or "").strip()
    if not v:
        return None

    # Strip general URL prefixes
    v = re.sub(r'^(https?:\/\/)?(www\.)?', '', v, flags=re.I).strip()
    v = re.sub(r'^\s*(GitHub|LinkedIn)\s*:\s*', '', v, flags=re.I).strip()

    def clean_handle(h: str) -> str:
        h = h.strip()
        h = re.sub(r'^@', '', h)
        return h

    if kind == "GitHub":
        m = re.search(r'^github\.com/([^/?#]+)', v, re.I)
        handle = clean_handle(m.group(1)) if m else clean_handle(v)
        handle = handle.split("/")[0] if "/" in handle else handle
        if handle:
            return handle, f"https://github.com/{handle}"
        return None

    if kind == "LinkedIn":
        m = re.search(r'^linkedin\.com/(?:in|pub)/([^/?#]+)', v, re.I)
        handle = clean_handle(m.group(1)) if m else clean_handle(v)
        handle = handle.split("/")[0] if "/" in handle else handle
        if handle:
            return handle, f"https://www.linkedin.com/in/{handle}"
        return None

    return None
