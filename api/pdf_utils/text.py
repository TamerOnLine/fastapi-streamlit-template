"""
Text wrapping and paragraph rendering utilities for PDF generation.
Handles LTR and RTL text alignment and spacing.
"""

from typing import List
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics

from .fonts import rtl
from .config import LEADING_BODY, LEADING_BODY_RTL, GAP_BETWEEN_PARAS


def wrap_text(text: str, font: str, size: int, max_w: float) -> List[str]:
    """Wraps a single block of text into lines fitting the specified width."""
    words = text.split()
    if not words:
        return [""]
    lines, cur = [], words[0]
    for w in words[1:]:
        trial = f"{cur} {w}"
        if pdfmetrics.stringWidth(trial, font, size) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def wrap_lines(lines: List[str], font: str, size: int, max_w: float, do_rtl=False) -> List[str]:
    """Wraps multiple lines of text to fit within a max width, optionally applying RTL logic."""
    out: List[str] = []
    for ln in lines:
        t = rtl(ln) if do_rtl else ln
        out.extend(wrap_text(t, font, size, max_w))
    return out


def draw_par(
    c: canvas.Canvas,
    x: float,
    y: float,
    lines: List[str],
    font: str,
    size: int,
    max_w: float,
    align: str = "left",
    rtl_mode: bool = False,
    leading: int | None = None,
    para_gap: int | None = None,
) -> float:
    """
    Draws paragraphs with wrapping and spacing control.

    Args:
        c (canvas.Canvas): The PDF canvas.
        x (float): X-coordinate.
        y (float): Starting Y-coordinate.
        lines (List[str]): Paragraph lines.
        font (str): Font name.
        size (int): Font size.
        max_w (float): Maximum width for wrapping.
        align (str): Text alignment ("left" or "right").
        rtl_mode (bool): Enables RTL reshaping.
        leading (int | None): Line spacing.
        para_gap (int | None): Gap between paragraphs.

    Returns:
        float: Updated y-coordinate after drawing.
    """
    c.setFont(font, size)
    cur = y
    line_gap = leading if leading is not None else (
        LEADING_BODY_RTL if (rtl_mode and align == "right") else LEADING_BODY
    )
    gap_between_paras = GAP_BETWEEN_PARAS if para_gap is None else para_gap

    for raw in lines:
        txt = rtl(raw) if (rtl_mode and align == "right") else raw
        wrapped = wrap_text(txt, font, size, max_w) if txt else [""]
        for ln in wrapped:
            if align == "right":
                c.drawRightString(x + max_w, cur, ln)
            else:
                c.drawString(x, cur, ln)
            cur -= line_gap
        cur -= gap_between_paras

    return cur