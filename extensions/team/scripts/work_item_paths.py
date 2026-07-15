"""Canonical paths for Team Feature and Bugfix artifacts."""

from __future__ import annotations

import re
from pathlib import Path


SAFE_WORK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CATEGORY_ALIASES = {
    "feature": "feature",
    "new-project": "feature",
    "template": "feature",
    "bug": "bugfix",
    "bugfix": "bugfix",
}


def normalize_category(work_type: str) -> str:
    category = CATEGORY_ALIASES.get(work_type.strip().lower())
    if category is None:
        raise ValueError("work type must resolve to feature or bugfix")
    return category


def resolve_work_root(project_root: Path, work_type: str, work_id: str) -> Path:
    if not SAFE_WORK_ID.fullmatch(work_id):
        raise ValueError("work ID must be a safe stable identifier")
    return project_root / ".specify" / normalize_category(work_type) / work_id
