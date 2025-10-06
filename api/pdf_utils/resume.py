from __future__ import annotations

from io import BytesIO
from typing import Dict, Any, List, Tuple, Optional

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from .blocks.base import Frame, RenderContext
from .blocks.registry import get as get_block
from .data_utils import build_ready_from_profile
from .config import UI_LANG
from .theme_loader import load_and_apply
from .block_aliases import canonicalize

PAGE_W, PAGE_H = A4
LEFT_MARGIN = 18 * mm
RIGHT_MARGIN = 18 * mm
TOP_MARGIN = 22 * mm
BOTTOM_MARGIN = 18 * mm

def build_resume_pdf(
    data: Optional[Dict[str, Any]] = None,
    *,
    layout_plan: Optional[List[Dict[str, Any]]] = None,
    ready: Optional[Dict[str, Any]] = None,
    ui_lang: Optional[str] = None,
    rtl_mode: Optional[bool] = None,
    theme_name: Optional[str] = None,
    theme: Optional[str] = None,
) -> bytes:
    """
    Build a resume PDF and return it as byte content.

    Can be used in two modes:
        1. New interface: pass `data` with profile, layout, and settings.
        2. Legacy mode: directly pass `layout_plan` and `ready`.

    Args:
        data (Optional[Dict[str, Any]]): Input dictionary containing resume profile and layout.
        layout_plan (Optional[List[Dict[str, Any]]]): Legacy layout configuration.
        ready (Optional[Dict[str, Any]]): Preprocessed data ready for block rendering.
        ui_lang (Optional[str]): UI language code.
        rtl_mode (Optional[bool]): Whether the text is right-to-left.
        theme_name (Optional[str]): Name of the theme to use.
        theme (Optional[str]): Legacy theme name for compatibility.

    Returns:
        bytes: Rendered PDF content as bytes.
    """
    if theme and not theme_name:
        theme_name = theme

    if data is not None:
        ui = (data.get("ui_lang") or UI_LANG)
        rtl = bool(data.get("rtl_mode"))
        profile = data.get("profile") or {}
        tn = theme_name or data.get("theme_name") or "default"
        theme_dict = load_and_apply(tn)
        rd = build_ready_from_profile(profile)
        plan, cols = _resolve_layout_and_columns_from_inline(data)

        return _render_pdf(
            plan,
            rd,
            ui_lang=ui,
            rtl_mode=rtl,
            columns=cols,
            theme=theme_dict,
        )

    ui = ui_lang or UI_LANG
    rtl = bool(rtl_mode)
    rd = ready or {}
    plan = layout_plan or _fallback_layout()
    cols = _fallback_columns()
    tn = theme_name or "default"
    theme_dict = load_and_apply(tn)

    return _render_pdf(
        plan,
        rd,
        ui_lang=ui,
        rtl_mode=rtl,
        columns=cols,
        theme=theme_dict,
    )

def _render_pdf(
    layout_plan: List[Dict[str, Any]] | Dict[str, Any],
    ready: Dict[str, Any],
    *,
    ui_lang: str,
    rtl_mode: bool,
    columns: Dict[str, Tuple[float, float]],
    theme: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Render the resume PDF by drawing each block according to the layout plan.

    Args:
        layout_plan (List[Dict[str, Any]] | Dict[str, Any]): Block layout definition.
        ready (Dict[str, Any]): Data for each block.
        ui_lang (str): UI language code.
        rtl_mode (bool): Enable RTL layout.
        columns (Dict[str, Tuple[float, float]]): Layout column positions and widths.
        theme (Optional[Dict[str, Any]]): Theme settings.

    Returns:
        bytes: PDF binary content.
    """
    if isinstance(layout_plan, dict):
        layout_plan = layout_plan.get("layout", [])

    fixed_plan: List[Dict[str, Any]] = []
    for it in layout_plan or []:
        if isinstance(it, dict) and it.get("block_id"):
            fixed_plan.append(it)
        elif isinstance(it, str) and it.strip():
            fixed_plan.append({"block_id": it.strip()})
        else:
            print(f"[WARN] Skipping invalid layout item in _render: {it!r}")

    layout_plan = fixed_plan

    for it in layout_plan:
        it["block_id"] = canonicalize(it["block_id"])

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    ctx: RenderContext = {
        "ui_lang": ui_lang,
        "rtl_mode": rtl_mode,
        "page_top_y": PAGE_H - TOP_MARGIN,
        "page_h": PAGE_H,
        "theme": theme or {},
    }

    for block_conf in layout_plan:
        try:
            block_id = block_conf.get("block_id")
            block = get_block(block_id)

            frame_dict = block_conf.get("frame") or {}
            frame = Frame(
                x=float(frame_dict.get("x", LEFT_MARGIN)),
                y=float(frame_dict.get("y", PAGE_H - TOP_MARGIN)),
                w=float(frame_dict.get("w", PAGE_W - LEFT_MARGIN - RIGHT_MARGIN)),
            )

            block_data = ready.get(block_id) or block_conf.get("data") or {}
            new_y = block.render(c, frame, block_data, ctx)
            frame.y = new_y

        except Exception as e:
            print(f"[WARN] Block '{block_conf.get('block_id') if isinstance(block_conf, dict) else block_conf}' failed: {e}")
            continue

    c.showPage()
    c.save()
    return buf.getvalue()

def _resolve_layout_and_columns_from_inline(data: Dict[str, Any]):
    """
    Determine layout plan and columns from inline layout data.

    Args:
        data (Dict[str, Any]): Input dictionary possibly containing layout_inline.

    Returns:
        Tuple[List[Dict[str, Any]], Dict[str, Tuple[float, float]]]:
            Normalized layout plan and default columns.
    """
    li = data.get("layout_inline")
    if li is None:
        return _fallback_layout(), _fallback_columns()

    if isinstance(li, dict):
        plan = li.get("layout") or []
    elif isinstance(li, list):
        plan = li
    else:
        plan = _fallback_layout()

    norm_plan: List[Dict[str, Any]] = []
    for it in plan:
        if isinstance(it, dict) and it.get("block_id"):
            norm_plan.append(it)
        elif isinstance(it, str) and it.strip():
            norm_plan.append({"block_id": it.strip()})
        else:
            print(f"[WARN] Skipping invalid layout item in _resolve: {it!r}")

    for it in norm_plan:
        it["block_id"] = canonicalize(it["block_id"])

    return norm_plan, _fallback_columns()

def _fallback_layout() -> List[Dict[str, Any]]:
    """
    Provide a default layout in case no custom layout is defined.

    Returns:
        List[Dict[str, Any]]: Fallback layout definition.
    """
    return [
        {
            "block_id": "header_name",
            "frame": {
                "x": LEFT_MARGIN,
                "y": PAGE_H - TOP_MARGIN,
                "w": PAGE_W - LEFT_MARGIN - RIGHT_MARGIN,
            },
            "data": {"centered": True, "highlight_bg": "#E0F2FE", "box_h_mm": 30},
        },
        {"block_id": "key_skills", "frame": {"x": LEFT_MARGIN, "y": PAGE_H - 60 * mm, "w": 80 * mm}},
        {"block_id": "projects", "frame": {"x": 110 * mm, "y": PAGE_H - 60 * mm, "w": 85 * mm}},
    ]

def _fallback_columns() -> Dict[str, Tuple[float, float]]:
    """
    Provide fallback layout column widths.

    Returns:
        Dict[str, Tuple[float, float]]: Positions and widths of default left and right columns.
    """
    total_w = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN
    left_w = total_w * 0.4
    right_w = total_w * 0.55
    return {
        "left": (LEFT_MARGIN, left_w),
        "right": (LEFT_MARGIN + left_w + 5 * mm, right_w),
    }