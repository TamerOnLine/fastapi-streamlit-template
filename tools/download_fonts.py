from __future__ import annotations
import requests
from pathlib import Path

# ============================================================
# 📦 إعداد المسار الداخلي لمجلد الخطوط داخل مشروعك
# ============================================================
ASSETS_DIR = Path(__file__).resolve().parents[1] / "api" / "pdf_utils" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 🌐 روابط الخطوط الرسمية (Noto + Amiri Quran fallback)
# ============================================================
FONTS = {
    # ✅ خط Noto Naskh Arabic (Google Fonts)
    "NotoNaskhArabic-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Regular.ttf",

    # ✅ بديل موثوق للـ Amiri الأصلي (Amiri Quran)
    "Amiri-Regular.ttf":
        "https://github.com/google/fonts/raw/main/ofl/amiriquran/AmiriQuran-Regular.ttf",
}

# ============================================================
# 🧠 الدالة الرئيسية لتحميل الملفات
# ============================================================
def download_fonts() -> None:
    print(f"📂 حفظ الخطوط في: {ASSETS_DIR}")
    for name, url in FONTS.items():
        dest = ASSETS_DIR / name
        print(f"📥 Downloading {name} ...")
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            dest.write_bytes(r.content)
            size_kb = dest.stat().st_size // 1024
            print(f"✅ Saved to {dest} ({size_kb} KB)")
        except Exception as e:
            print(f"❌ Failed to download {name}: {e}")
    print("\n🎉 All downloads attempted.\n")

# ============================================================
# ⚙️ نقطة التشغيل
# ============================================================
if __name__ == "__main__":
    download_fonts()
