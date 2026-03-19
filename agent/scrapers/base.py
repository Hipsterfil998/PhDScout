"""Abstract base class and shared utilities for all job board scrapers."""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from typing import ClassVar

import requests
from bs4 import BeautifulSoup


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

_DELAY = 1.5  # polite delay between HTTP requests (seconds)

_TYPE_KEYWORDS: dict[str, list[str]] = {
    "predoctoral": [
        "predoctoral", "pre-doctoral", "pre doctoral",
        "master student", "master's student", "msc student",
        "junior researcher", "research trainee", "research internship",
        "early-stage researcher", "early stage researcher", "esr",
    ],
    "phd": [
        "phd", "ph.d", "doctoral", "doctorate",
        "phd student", "phd candidate", "phd position",
        "phd fellowship", "graduate student", "studentship",
    ],
    "postdoc": [
        "postdoc", "post-doc", "post doc", "postdoctoral",
        "research associate", "research fellow",
    ],
    "fellowship": [
        "fellowship", "stipend", "marie curie", "marie skłodowska",
        "horizon europe", "erc", "scholarship", "grant",
    ],
    "research_staff": [
        "researcher", "research scientist", "research engineer",
        "staff scientist", "principal investigator", "pi position",
        "lecturer", "professor", "faculty",
    ],
}


class BaseScraper(ABC):
    """Abstract base for all job board scrapers.

    Subclasses implement ``scrape()`` and declare a ``name`` class variable.
    Shared helpers (``_fetch``, ``_sleep``, ``_detect_type``, ``_extract_email``)
    are available to all subclasses.
    """

    name: ClassVar[str] = ""

    @abstractmethod
    def scrape(self, field: str, location: str, position_type: str) -> list[dict]:
        """Return a list of job listing dicts for the given search parameters."""
        ...

    # ------------------------------------------------------------------
    # Protected helpers
    # ------------------------------------------------------------------

    def _fetch(self, url: str, timeout: int = 15) -> BeautifulSoup | None:
        """GET ``url`` and return a parsed ``BeautifulSoup``, or ``None`` on failure."""
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=timeout)
            if resp.status_code != 200:
                return None
            return BeautifulSoup(resp.text, "lxml")
        except Exception:
            return None

    def _sleep(self) -> None:
        """Polite delay between requests."""
        time.sleep(_DELAY)

    @staticmethod
    def _detect_type(title: str, description: str) -> str:
        """Infer position type from title and description text."""
        combined = (title + " " + description).lower()
        for pos_type, keywords in _TYPE_KEYWORDS.items():
            if any(kw in combined for kw in keywords):
                return pos_type
        return "other"

    @staticmethod
    def _extract_email(text: str) -> str | None:
        """Extract the first email address found in ``text``, or ``None``."""
        m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
        return m.group() if m else None
