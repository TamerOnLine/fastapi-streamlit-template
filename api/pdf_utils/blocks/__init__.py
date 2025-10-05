from .base import Frame, RenderContext
from .registry import register, get, all_blocks
from . import left_panel_bg 
# استورد الكتل لتُسجِّل نفسها تلقائياً
from . import (
    avatar_circle,
    header_name,
    contact_info,
    key_skills,
    languages,
    projects,
    education,
    text_section,
    social_links,
)  # noqa: F401
