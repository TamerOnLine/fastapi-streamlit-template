from __future__ import annotations

from typing import Any, Dict, List

# Blocks that are allowed to be empty (decorative or layout-related)
_BLOCKS_CAN_BE_EMPTY = {
    "header_name",
    "left_panel_bg",
    "rule",
    "header_bar",
    "links_inline",
    "decor_curve",
}

def _has_meaningful_value(d: Dict[str, Any]) -> bool:
    """
    Check whether a dictionary contains any meaningful (non-empty, non-null) values.

    Args:
        d (Dict[str, Any]): Dictionary to inspect.

    Returns:
        bool: True if a meaningful value exists, False otherwise.
    """
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
    Construct the final layout plan by merging a theme layout definition with data from 'ready'.

    Supports:
      - item["col"] for modern column-based layout.
      - item["frame"] for legacy positioning.
      - item["source"] to refer to keys like "text_section:summary".

    Data from layout overrides values from 'ready'. Skips blocks without meaningful content,
    except those listed in _BLOCKS_CAN_BE_EMPTY.

    Args:
        theme_layout (List[Dict[str, Any]]): List of layout configuration items.
        ready (Dict[str, Any]): Dictionary of pre-loaded data content.

    Returns:
        List[Dict[str, Any]]: Final merged layout plan.
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

        if bid not in _BLOCKS_CAN_BE_EMPTY and not _has_meaningful_value(merged):
            continue

        entry: Dict[str, Any] = {"block_id": bid, "data": merged}
        if "col" in item:
            entry["col"] = item["col"]
        elif "frame" in item:
            entry["frame"] = item["frame"]
        else:
            entry["col"] = item.get("col", "right")

        if src:
            entry["source"] = src

        plan.append(entry)

    return plan