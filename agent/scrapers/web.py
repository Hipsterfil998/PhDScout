"""Web search scraper — DuckDuckGo targeted queries for open academic positions."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from agent.scrapers.base import BaseScraper

_CURRENT_YEAR = str(datetime.now().year)

_JOB_SIGNALS = [
    "open position", "open call", "call for applications", "we are recruiting",
    "we are hiring", "vacancy", "apply now", "applications are invited",
    "phd position", "phd studentship", "postdoc position", "postdoctoral position",
    "research fellowship", "funded position", "fully funded", "stipend",
    "deadline", "closing date", "how to apply",
]


def _looks_like_job_posting(title: str, body: str) -> bool:
    combined = (title + " " + body).lower()
    return any(sig in combined for sig in _JOB_SIGNALS)


class WebSearchScraper(BaseScraper):
    """Searches for open positions via DuckDuckGo with targeted academic queries."""

    name = "web"

    _TYPE_LABELS: ClassVar[dict[str, str]] = {
        "predoctoral":    'predoctoral position OR "early-stage researcher"',
        "phd":            "PhD studentship",
        "postdoc":        "postdoctoral position",
        "fellowship":     "research fellowship",
        "research_staff": "research scientist",
        "any":            "PhD OR postdoc OR fellowship",
    }

    def scrape(self, field: str, location: str, position_type: str) -> list[dict]:
        try:
            from duckduckgo_search import DDGS  # type: ignore
        except ImportError:
            return []

        loc = location.strip() if location.lower() not in ("worldwide", "anywhere", "") else ""
        yr = _CURRENT_YEAR
        type_label = self._TYPE_LABELS.get(position_type, "PhD OR postdoc OR fellowship")
        loc_part = f'"{loc}"' if loc else ""

        queries = [
            f'"{field}" {type_label} {loc_part} "call for applications" {yr}'.strip(),
            f'"{field}" {type_label} {loc_part} "open position" OR "vacancy" {yr} apply'.strip(),
            f'"{field}" {type_label} {loc_part} university funded {yr} deadline'.strip(),
        ]

        raw: list[dict] = []
        ddgs = DDGS()
        for query in queries:
            try:
                results = ddgs.text(query, max_results=8)
                if results:
                    raw.extend(results)
                self._sleep()
            except Exception:
                continue

        listings: list[dict] = []
        for r in raw:
            title = r.get("title", "")
            body = r.get("body", "")
            combined = (title + " " + body).lower()
            if yr not in combined:
                continue
            if not _looks_like_job_posting(title, body):
                continue
            listings.append({
                "title": title,
                "institution": "",
                "location": location,
                "url": r.get("href", ""),
                "description": body,
                "deadline": None,
                "email": self._extract_email(body),
                "source": self.name,
                "type": self._detect_type(title, body),
            })

        return listings
