# api/pdf_utils/layout_utils.py
from __future__ import annotations

from typing import Any, Dict, List


# بعض البلوكات يسمح رسمها حتى إن كانت بلا بيانات (زخرفية/رأس/خط فاصل)
_BLOCKS_CAN_BE_EMPTY = {
    "header_name",
    "left_panel_bg",
    "rule",
    "header_bar",
    "links_inline",
    "decor_curve",
}


def _has_meaningful_value(d: Dict[str, Any]) -> bool:
    for v in (d or {}).values():
        if isinstance(v, (list, tuple, set, dict)):
            if len(v) > 0:
                return True
        else:
            if v not in (None, "", False):
                return True
    return False


def merge_layout(theme_layout: List[Dict[str, Any]], ready: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    يبني layout_plan النهائي من ملف layout (أو theme.layout) + مخزن البيانات ready.
    يدعم:
      - item["col"]   (الأعمدة الحديثة)
      - item["frame"] (النمط القديم "left"/"right"/{x,y,w})
      - item["source"] لانتقاء مفتاح بيانات مثل "text_section:summary"
    يدمج data من الـlayout فوق بيانات ready (override).
    يتخطى البلوكات الفارغة ما عدا _BLOCKS_CAN_BE_EMPTY.
    """
    plan: List[Dict[str, Any]] = []

    for item in theme_layout or []:
        if not isinstance(item, dict):
            continue

        bid = item.get("block_id")
        if not bid:
            continue

        src = item.get("source")
        override = item.get("data") or {}
        data_key = f"{bid}:{src}" if src else bid

        base = ready.get(data_key) or ready.get(bid) or {}
        merged = {**base, **override} if override else base

        # تخطّي البلوكات الفارغة باستثناء الزخرفية/الرؤوس
        if bid not in _BLOCKS_CAN_BE_EMPTY and not _has_meaningful_value(merged):
            continue

        entry: Dict[str, Any] = {"block_id": bid, "data": merged}
        if "col" in item:
            entry["col"] = item["col"]
        elif "frame" in item:
            entry["frame"] = item["frame"]
        else:
            # افتراضيًا ضعها في يمين إن وُجد أو اتركها تُحلّ في resume.py
            entry["col"] = item.get("col", "right")

        # أعِد تمرير source إن كان البلوك يستخدمه داخليًا
        if src:
            entry["source"] = src

        plan.append(entry)

    return plan
