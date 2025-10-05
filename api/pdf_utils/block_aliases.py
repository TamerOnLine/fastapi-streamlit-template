# api/pdf_utils/block_aliases.py
CANONICAL_BLOCKS = {
    # حدّث القائمة حسب ما هو مسجّل فعلاً في registry
    "header_name", "projects", "education", "contact_info",
    "languages", "key_skills", "social_links", "avatar_circle",
    "text_section", "left_panel_bg", "decor_curve",
    # أضف الموجود لديك...
}

ALIASES = {
    "pprojects": "projects",
    "experiencce": "experience",  # إن كان لديك بلوك experience
    "educatioon": "education",
    "educattion": "education",
    "header_bar": "header_name",  # إن لم يكن لديك header_bar كبلوك مستقل
    # بلوكات عامة غير موجودة: وجّهها لبديل منطقي
    "objective": "text_section",
    "activities": "text_section",
    "rule": "text_section",  # أو أنشئ بلوك Rule بسيط لاحقاً
}

def canonicalize(block_id: str) -> str:
    bid = block_id.strip()
    bid = ALIASES.get(bid, bid)
    return bid
