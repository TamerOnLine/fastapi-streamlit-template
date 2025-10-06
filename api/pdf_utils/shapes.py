from reportlab.pdfgen import canvas

from .config import LEFT_BG, LEFT_BORDER, RULE_COLOR, CARD_RADIUS

def draw_round_rect(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    fill_color=LEFT_BG,
    stroke_color=LEFT_BORDER,
    radius=CARD_RADIUS,
):
    """
    Draw a filled and stroked rounded rectangle.

    Args:
        c (canvas.Canvas): ReportLab canvas object.
        x (float): X-coordinate of the bottom-left corner.
        y (float): Y-coordinate of the bottom-left corner.
        w (float): Width of the rectangle.
        h (float): Height of the rectangle.
        fill_color: Fill color of the rectangle.
        stroke_color: Border color.
        radius: Radius of the rounded corners.
    """
    c.setFillColor(fill_color)
    c.setStrokeColor(stroke_color)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)

def draw_rule(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    color=RULE_COLOR,
):
    """
    Draw a horizontal rule (line) on the canvas.

    Args:
        c (canvas.Canvas): ReportLab canvas object.
        x (float): Starting x-coordinate.
        y (float): Y-coordinate for the rule.
        w (float): Width of the rule.
        color: Stroke color of the rule.
    """
    c.setStrokeColor(color)
    c.setLineWidth(0.7)
    c.line(x, y, x + w, y)