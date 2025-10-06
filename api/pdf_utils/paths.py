from __future__ import annotations

import os
from pathlib import Path

def get_assets_root() -> Path:
    """
    Detect the root directory for assets, with optional environment variable override.

    Returns:
        Path: Path to the resolved assets directory.

    Environment Variable:
        PDF_UTILS_ASSETS: Overrides the default asset directory if set and valid.
    """
    env = os.getenv("PDF_UTILS_ASSETS")
    if env:
        p = Path(env).expanduser().resolve()
        if p.exists():
            return p

    here = Path(__file__).resolve().parent
    cand = here / "assets"
    return cand if cand.exists() else here

ASSETS = get_assets_root()
ICONS_DIR = ASSETS / "icons"