from __future__ import annotations

import shutil
import tempfile
from importlib.resources import files
from pathlib import Path

PKG = "api.pdf_utils.assets"

def open_asset_bytes(rel_path: str) -> bytes:
    """
    Read asset bytes from the bundled package.

    Args:
        rel_path (str): Relative path to the asset within the package.

    Returns:
        bytes: The raw byte content of the asset.
    """
    return (files(PKG) / rel_path).read_bytes()

def asset_path(rel_path: str) -> str:
    """
    Return a path-like string to the asset. Suitable for most use cases.

    Args:
        rel_path (str): Relative path to the asset within the package.

    Returns:
        str: A string representing the path to the asset.

    Note:
        If a real file on disk is required, use `extract_resource` instead.
    """
    return str(files(PKG) / rel_path)

def extract_resource(rel_path: str) -> Path:
    """
    Copy the packaged asset to a real temporary file and return its filesystem path.

    Args:
        rel_path (str): Relative path to the asset within the package.

    Returns:
        Path: Path to the extracted temporary file on disk.

    Note:
        Use this only if a real file is required by a third-party library (e.g., TTFont).
    """
    src = (files(PKG) / rel_path).open("rb")
    try:
        tmpdir = Path(tempfile.mkdtemp(prefix="pdf_assets_"))
        out = tmpdir / Path(rel_path).name
        with out.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        return out
    finally:
        src.close()
