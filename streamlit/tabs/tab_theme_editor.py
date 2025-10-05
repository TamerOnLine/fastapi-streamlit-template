# streamlit/tabs/tab_theme_editor.py
from __future__ import annotations
from pathlib import Path
import streamlit as st

def _list_theme_names(base_dir: Path) -> list[str]:
    themes_dir = base_dir / "themes"
    if not themes_dir.exists():
        return ["default"]
    items = []
    for p in themes_dir.glob("*.theme.json"):
        name = p.name.replace(".theme.json", "")
        items.append(name)
    # fallback آمن
    return items or ["default"]

def _list_layout_names(base_dir: Path) -> list[str]:
    layouts_dir = base_dir / "layouts"
    if not layouts_dir.exists():
        return [""]
    items = [p.name.replace(".layout.json", "") for p in layouts_dir.glob("*.layout.json")]
    # اسم فارغ يعني "بدون تخطيط إضافي"
    return [""] + sorted(items)

def theme_selector():
    """
    واجهة اختيار الثيم والتخطيط.
    تُعيد (theme_name, layout_name)
    """
    # نحاول تحديد جذر المشروع عبر موقع هذا الملف: streamlit/tabs/.. -> project root
    base_dir = Path(__file__).resolve().parents[2]

    st.subheader("🎨 Theme & Layout")
    themes = _list_theme_names(base_dir)
    layouts = _list_layout_names(base_dir)

    # اختيار الثيم
    theme_name = st.selectbox(
        "Theme",
        options=sorted(themes),
        index=min(0, len(themes)-1),
        help="Choose a theme JSON from the /themes folder.",
    )

    # اختيار التخطيط (اختياري)
    layout_name = st.selectbox(
        "Layout (optional)",
        options=layouts,
        index=0,  # أول عنصر فارغ = بدون تخطيط إضافي
        help="Pick a layout JSON from the /layouts folder, or leave empty to use the theme’s built-in layout.",
    )

    # نعيد القيم (الاسم الفارغ يعامل كـ None لاحقًا في generate.py عند الإرسال)
    layout_name = layout_name or None
    return theme_name, layout_name
