# streamlit/tabs/generate.py
from __future__ import annotations
import streamlit as st

# ✅ استيراد مباشر (بدون ..) لتفادي الخطأ عند تشغيل streamlit run
from api_client import generate_pdf
from .tab_theme_editor import theme_selector


def render_generate_actions(outputs_dir):
    """
    تبويب التوليد والتحمـيل (Generate / Download)
    يوفّر اختيار الثيم والتخطيط واللغة، ثم يرسل البيانات إلى FastAPI لتوليد PDF.
    """
    st.subheader("📄 Generate Resume PDF")

    # احصل على بيانات البروفايل من session_state (يُعبَّأ من التبويبات الأخرى)
    profile = st.session_state.get("profile_data") or {}

    # اختيار الثيم والتخطيط
    theme_name, layout_name = theme_selector()
    ui_lang = st.selectbox("🌐 UI Language", ["ar", "en", "de"], index=0)
    rtl_mode = (ui_lang == "ar") or st.checkbox("↔️ Force RTL", value=True)

    if not profile:
        st.info(
            "No profile data found yet — you can still generate a blank PDF.",
            icon="ℹ️",
        )

    # عرض الأزرار في صف واحد
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("🚀 Generate PDF", type="primary", use_container_width=True):
            try:
                pdf_bytes = generate_pdf(
                    profile,
                    theme_name=theme_name,
                    layout_name=layout_name,
                    ui_lang=ui_lang,
                    rtl_mode=rtl_mode,
                    use_simple_json=True,  # 🔹 يستخدم /generate-form-simple
                )
                st.success("✅ PDF generated successfully!")

                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"resume-{theme_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"❌ Failed to generate PDF: {e}")

    with col2:
        st.caption(
            "💡 Tip: Theme and layout can be changed instantly — "
            "no need to restart the server."
        )

    st.divider()
    st.caption(
        "Generated files are also stored in the 'outputs/' directory inside your project."
    )
