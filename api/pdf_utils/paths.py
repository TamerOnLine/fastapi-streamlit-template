"""
Utility functions and constants for resolving asset paths in the PDF utility package.
Supports environment variable overrides for flexibility.
"""

from __future__ import annotations

import os
from pathlib import Path


def get_assets_root() -> Path:
    """
    Detects the root directory for assets. Supports environment override.

    Returns:
        Path: Path to the assets directory.

    Environment Variable:
        PDF_UTILS_ASSETS: If set, overrides the default path.
    """
    env = os.getenv("PDF_UTILS_ASSETS")
    if env:
        p = Path(env).expanduser().resolve()
        if p.exists():
            return p

    here = Path(__file__).resolve().parent
    cand = here / "assets"
    return cand if cand.exists() else here  # Fallback: package directory itself


ASSETS = get_assets_root()
ICONS_DIR = ASSETS / "icons"
