# api/pdf_utils/labels.py
from __future__ import annotations

# اللغة الافتراضية
DEFAULT_LANG = "en"

LABELS: dict[str, dict[str, str]] = {
    "en": {
        "personal_info": "Personal Information",
        "key_skills": "Key Skills",
        "languages": "Languages",
        "selected_projects": "Selected Projects",
        "professional_training": "Professional Training",
    },
    "de": {
        "personal_info": "Persönliche Informationen",
        "key_skills": "Technische Fähigkeiten",
        "languages": "Sprachen",
        "selected_projects": "Ausgewählte Projekte",
        "professional_training": "Berufliche Weiterbildung",
    },
    "ar": {
        "personal_info": "المعلومات الشخصية",
        "key_skills": "المهارات الرئيسية",
        "languages": "اللغات",
        "selected_projects": "أبرز المشاريع",
        "professional_training": "التدريب المهني",
    },
}

def t(key: str, lang: str | None = None) -> str:
    """ترجع النص بحسب اللغة مع fallback آمن."""
    lang = (lang or DEFAULT_LANG).lower()
    return LABELS.get(lang, LABELS[DEFAULT_LANG]).get(key, key)
