#!/usr/bin/env python3
"""Shared architecture-level terminology and compatibility aliases."""

from __future__ import annotations

import re
from typing import Any


ARCHITECTURE_LEVEL_LABELS = {
    "none": "none",
    "pending": "pending",
    "l0": "l0",
    "top-level-design": "l0",
    "顶层设计": "l0",
    "l1": "l1",
    "module-design": "l1",
    "模块设计": "l1",
    "l2": "l2",
    "interface-and-data-structure-design": "l2",
    "interface-data-structure-design": "l2",
    "接口与数据结构设计": "l2",
}


def normalize_architecture_level(value: Any) -> str | None:
    """Return the canonical machine level for legacy or descriptive labels."""

    text = str(value or "").strip().casefold()
    if not text:
        return None
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"\s*\(l[012]\)\s*$", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return ARCHITECTURE_LEVEL_LABELS.get(text)
