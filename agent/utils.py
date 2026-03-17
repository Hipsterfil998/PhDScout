"""Shared utilities for parsing LLM responses."""

from __future__ import annotations

import json
import re
from typing import Any


def strip_fences(text: str) -> str:
    """Remove markdown code fences that models sometimes emit."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_json(raw: str) -> dict[str, Any] | None:
    """Parse JSON from a model response, tolerating fences and partial wrapping.

    Returns None if parsing fails entirely.
    """
    clean = strip_fences(raw)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", clean, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return None
