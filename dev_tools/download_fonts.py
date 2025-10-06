from __future__ import annotations

import requests
from pathlib import Path

# ------------------------------------------------------------
# Setup internal path for font assets directory
# ------------------------------------------------------------
ASSETS_DIR = Path(__file__).resolve().parents[1] / "api" / "pdf_utils" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Official font URLs (Noto Naskh + Amiri Quran fallback)
# ------------------------------------------------------------
FONTS = {
    "NotoNaskhArabic-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Regular.ttf",

    "Amiri-Regular.ttf":
        "https://github.com/google/fonts/raw/main/ofl/amiriquran/AmiriQuran-Regular.ttf",
}

# ------------------------------------------------------------
# Main font download function
# ------------------------------------------------------------
def download_fonts() -> None:
    """
    Downloads required font files into the assets directory.
    """
    print(f"Saving fonts to: {ASSETS_DIR}")
    for name, url in FONTS.items():
        dest = ASSETS_DIR / name
        print(f"Downloading {name} ...")
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            dest.write_bytes(r.content)
            size_kb = dest.stat().st_size // 1024
            print(f"Saved to {dest} ({size_kb} KB)")
        except Exception as e:
            print(f"Failed to download {name}: {e}")
    print("\nAll downloads attempted.\n")

# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    download_fonts()
