# api/pdf_utils/resume.py
"""
Main function for generating a resume PDF using ReportLab,
driven 100% by a Blocks registry + a themeable layout_plan.

Now supports:
- Dynamic multi-column layouts via theme["columns"].
- Backward-compatible 2-column mode (left/right) via theme.page.left_col_mm, gap_mm.
- Frames:
    * "left" | "right" (legacy lanes)
    * {"x": float|token, "y": float|token, "w": float|token}
    * Or by column id using layout item: {"col": "left" | "middle" | "right" | ...}
- Tokens:
    * page.left, page.right, page.top, page.bottom
    * <col>.x, <col>.w, <col>.y for any column id present in computed frames
"""

from __future__ import annotations

from io import BytesIO
from typing import List, Dict, Any, Tuple, Optional

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from .config import *  # UI_LANG, CARD_PAD, GAP_AFTER_HEADING, colors...
from .blocks import Frame, RenderContext, get  # registry + types
from .theme_loader import get_page_cfg  # reads theme["page"] if provided


# -----------------------------
# Helpers: page + columns
# -----------------------------
def _page_mm_from_theme(theme_page: Dict[str, Any] | None, PAGE_W: float, PAGE_H: float) -> Dict[str, float]:
    page = theme_page or {}
    marg = page.get("margins_mm") or {}
    return {
        "top": float(marg.get("top", 16.0)),
        "right": float(marg.get("right", 16.0)),
        "bottom": float(marg.get("bottom", 16.0)),
        "left": float(marg.get("left", 16.0)),
        "gap": float(page.get("gap_mm", 8.0)),
        "left_col": float(page.get("left_col_mm", 62.0)),
        "draw_left_panel": bool(page.get("left_panel_bg", False)),
        "page_w_mm": PAGE_W / mm,
        "page_h_mm": PAGE_H / mm,
    }


def _compute_columns_from_spec(
    columns_spec: List[Dict[str, Any]],
    page_w_mm: float,
    page_h_mm: float,
    margins_mm: Dict[str, float],
) -> Dict[str, Dict[str, float]]:
    """
    Compute frames for N columns. Supports fixed width (w_mm) and flex columns.

    Returns frames dict:
        {
          "<col_id>": {"x": px, "y": py, "w": pw, "y_cursor": py}
        }
    """
    top_y_mm = page_h_mm - margins_mm["top"]
    x_mm = margins_mm["left"]
    usable_w_mm = page_w_mm - margins_mm["left"] - margins_mm["right"]

    frames: Dict[str, Dict[str, float]] = {}

    # Sum fixed + count flex
    total_fixed = 0.0
    flex_count = 0
    for col in columns_spec:
        if "w_mm" in col:
            total_fixed += float(col["w_mm"])
        else:
            flex_count += 1

    remaining = max(usable_w_mm - total_fixed, 0.0)
    flex_unit = remaining / flex_count if flex_count else 0.0

    for col in columns_spec:
        cid = str(col["id"])
        if "w_mm" in col:
            w_mm = float(col["w_mm"])
        else:
            # flex
            w_mm = float(flex_unit)

        frames[cid] = {
            "x": x_mm * mm,
            "y": top_y_mm * mm,
            "w": w_mm * mm,
            "y_cursor": top_y_mm * mm,
        }
        x_mm += w_mm + float(col.get("gap_right_mm", 0.0))

    return frames


def _compute_default_two_cols(
    page_w_mm: float,
    page_h_mm: float,
    margins_mm: Dict[str, float],
    left_col_mm: float = 60.0,
    gap_mm: float = 8.0,
) -> Dict[str, Dict[str, float]]:
    """
    Legacy 2-column layout (left/right) for backward compatibility.
    """
    top_y_mm = page_h_mm - margins_mm["top"]
    x_mm = margins_mm["left"]
    usable_w_mm = page_w_mm - margins_mm["left"] - margins_mm["right"]

    left_w = float(left_col_mm)
    right_w = max(usable_w_mm - left_w - float(gap_mm), 0.0)

    frames = {
        "left":  {"x": x_mm * mm, "y": top_y_mm * mm, "w": left_w * mm,  "y_cursor": top_y_mm * mm},
        "right": {"x": (x_mm + left_w + float(gap_mm)) * mm, "y": top_y_mm * mm,
                  "w": right_w * mm, "y_cursor": top_y_mm * mm},
    }
    return frames


def _resolve_token(token: str, frames: Dict[str, Dict[str, float]], page_edges: Dict[str, float]) -> float:
    """
    Resolve tokens:
      page.left, page.right, page.top, page.bottom
      <col>.x, <col>.w, <col>.y
    """
    t = (token or "").strip()
    if t == "page.left":
        return page_edges["left"]
    if t == "page.right":
        return page_edges["right"]
    if t == "page.top":
        return page_edges["top"]
    if t == "page.bottom":
        return page_edges["bottom"]

    if "." in t:
        col_id, key = t.split(".", 1)
        if col_id in frames and key in ("x", "w", "y"):
            if key == "y":
                # Prefer live y_cursor if available
                return frames[col_id].get("y_cursor", frames[col_id]["y"])
            return frames[col_id][key]
    return 0.0


def _val_from_maybe_token(v: Any, default_px: float, frames: Dict[str, Dict[str, float]], page_edges: Dict[str, float]) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        return _resolve_token(v, frames, page_edges)
    return float(default_px)


# -----------------------------
# Main builder
# -----------------------------
def build_resume_pdf(
    *,
    layout_plan: List[Dict[str, Any]],   # REQUIRED
    ui_lang: Optional[str] = None,
    rtl_mode: bool = False,
    theme: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Generate PDF from `layout_plan` + theme-aware page geometry.

    layout_plan item examples:
      NEW (recommended with multi-columns):
        { "block_id": "projects", "col": "right", "data": {...} }

      LEGACY:
        { "block_id": "header_name", "frame": "left" | "right" | {"x":..., "y":..., "w":...}, "data": {...} }
    """
    if not layout_plan or not isinstance(layout_plan, list):
        raise ValueError("resume builder requires a non-empty `layout_plan` list.")

    # ---------- PDF setup ----------
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    PAGE_W, PAGE_H = A4

    # ---------- Page geometry from theme ----------
    page_cfg = get_page_cfg(theme or {})  # reads theme["page"] if present
    page_mm = _page_mm_from_theme(page_cfg, PAGE_W, PAGE_H)

    page_left   = page_mm["left"] * mm
    page_right  = PAGE_W - page_mm["right"] * mm
    page_top    = PAGE_H - page_mm["top"] * mm
    page_bottom = page_mm["bottom"] * mm

    page_edges = {
        "left": page_left,
        "right": page_right,
        "top": page_top,
        "bottom": page_bottom,
    }

    # ---------- Compute frames: columns or legacy 2-col ----------
    theme_columns = (theme or {}).get("columns")
    if theme_columns and isinstance(theme_columns, list) and len(theme_columns) >= 1:
        frames = _compute_columns_from_spec(
            theme_columns,
            page_mm["page_w_mm"],
            page_mm["page_h_mm"],
            {"top": page_mm["top"], "right": page_mm["right"], "bottom": page_mm["bottom"], "left": page_mm["left"]},
        )
    else:
        frames = _compute_default_two_cols(
            page_mm["page_w_mm"],
            page_mm["page_h_mm"],
            {"top": page_mm["top"], "right": page_mm["right"], "bottom": page_mm["bottom"], "left": page_mm["left"]},
            left_col_mm=page_mm["left_col"],
            gap_mm=page_mm["gap"],
        )

    # ---------- Optional legacy left panel background (rect) ----------
    # Prefer drawing a real block (left_panel_bg) in the theme layout.
    if page_mm["draw_left_panel"] and "left" in frames:
        # draw a subtle card behind left column area
        from .shapes import draw_round_rect  # local import to avoid cycle in unused contexts
        left_f = frames["left"]
        card_x = left_f["x"]
        card_y = page_bottom
        card_w = left_f["w"]
        card_h = (PAGE_H - page_mm["top"] * mm) - page_bottom
        draw_round_rect(c, card_x, card_y, card_w, card_h)

    # ---------- Render context ----------
    ctx: RenderContext = {
        "rtl_mode": rtl_mode,
        "ui_lang": ui_lang or UI_LANG,
        "page_h": PAGE_H,
        "page_top_y": page_top,
        "theme": theme or {},
    }

    # Initialize each column y cursor (start slightly below top for aesthetics)
    # If you prefer different starting paddings per column, adjust here:
    for cid, fr in frames.items():
        # legacy kept right column slightly lower than left; keep consistent offsets if you like:
        start_offset = CARD_PAD if cid != "right" else GAP_AFTER_HEADING
        fr["y_cursor"] = fr["y"] - start_offset

    # ---------- Resolve frame from layout item ----------
    def resolve_frame_from_item(item: Dict[str, Any]) -> Tuple[Frame, Optional[str]]:
        """
        Returns (Frame, lane_id_if_known)
        lane_id is used to update that column's y_cursor afterwards.
        Priority:
          1) item["col"] -> use that column frame & y_cursor
          2) item["frame"] == "left"/"right" -> legacy lanes (if exist)
          3) item["frame"] is dict -> absolute / token-based frame (no lane to update)
          4) fallback -> try "right" if exists, otherwise first available column
        """
        # 1) New: column id
        col_id = item.get("col")
        if col_id and col_id in frames:
            fr = frames[col_id]
            f = Frame(x=fr["x"], y=fr["y_cursor"], w=fr["w"])
            return f, col_id

        # 2) Legacy lanes
        frame_spec = item.get("frame")
        if frame_spec == "left" and "left" in frames:
            fr = frames["left"]
            return Frame(x=fr["x"], y=fr["y_cursor"], w=fr["w"]), "left"
        if frame_spec == "right" and "right" in frames:
            fr = frames["right"]
            return Frame(x=fr["x"], y=fr["y_cursor"], w=fr["w"]), "right"

        # 3) Explicit dict frame (tokens allowed)
        if isinstance(frame_spec, dict):
            fx = _val_from_maybe_token(frame_spec.get("x"), list(frames.values())[0]["x"], frames, page_edges)
            fy = _val_from_maybe_token(frame_spec.get("y"), page_top, frames, page_edges)
            fw = _val_from_maybe_token(frame_spec.get("w"), list(frames.values())[0]["w"], frames, page_edges)
            return Frame(x=fx, y=fy, w=fw), None

        # 4) Fallback: prefer right column if present, else first column
        if "right" in frames:
            fr = frames["right"]
            return Frame(x=fr["x"], y=fr["y_cursor"], w=fr["w"]), "right"
        # first available
        first_id = next(iter(frames))
        fr = frames[first_id]
        return Frame(x=fr["x"], y=fr["y_cursor"], w=fr["w"]), first_id

    # ---------- Draw blocks ----------
    for item in layout_plan:
        if not isinstance(item, dict):
            continue
        bid = item.get("block_id")
        if not bid:
            continue

        data = item.get("data") or {}
        block = get(bid)  # may raise if not registered

        frame, lane = resolve_frame_from_item(item)
        new_y = block.render(c, frame, data, ctx)

        # update the lane's y_cursor if we used a known column
        if lane and lane in frames:
            frames[lane]["y_cursor"] = new_y

    # ---------- finalize ----------
    c.showPage()
    c.save()
    out = buffer.getvalue()
    buffer.close()
    return out
