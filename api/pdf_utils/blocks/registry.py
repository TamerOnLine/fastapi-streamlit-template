from __future__ import annotations
from typing import Dict
from .base import Block

_REGISTRY: Dict[str, Block] = {}

def register(block: Block) -> None:
    bid = getattr(block, "BLOCK_ID", None)
    if not bid:
        raise ValueError("Block must define BLOCK_ID")
    _REGISTRY[bid] = block

def get(bid: str) -> Block:
    if bid not in _REGISTRY:
        raise KeyError(f"Block '{bid}' not registered")
    return _REGISTRY[bid]

def all_blocks() -> Dict[str, Block]:
    return dict(_REGISTRY)
