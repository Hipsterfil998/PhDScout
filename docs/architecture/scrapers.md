# Adding a New Scraper

This guide walks through everything needed to add a new job source to PhdScout. You will implement a subclass of `BaseScraper`, register it in `JobSearcher._build_scrapers`, and optionally add location mappings.

---

## Overview

Every scraper is a Python class in `agent/scrapers/` that:

1. Inherits from `BaseScraper` (defined in `agent/scrapers/base.py`).
2. Declares a `name` class variable — a short identifier that appears in the `source` field of every listing.
3. Implements the `scrape(field, location, position_type)` abstract method, returning a list of dicts.
4. Uses the shared helpers `_fetch()`, `_sleep()`, `_detect_type()`, `_extract_email()`.

---

## Step 1 — Create the scraper file

Create a new file in `agent/scrapers/`. Name it after the source, e.g. `agent/scrapers/academicjobs.py`.

```python
"""academicjobs.world scraper — example new scraper."""

from __future__ import annotations

from urllib.parse import quote_plus

from agent.scrapers.base import BaseScraper


class AcademicJobsScraper(BaseScraper):
    """Scrapes academicjobs.world for research positions."""

    name = "academicjobs"

    def scrape(self, field: str, location: str, position_type: str) -> list[dict]:
        url = (
            "https://academicjobs.world/jobs"
            f"?keywords={quote_plus(field)}"
            f"&location={quote_plus(location)}"
        )
        soup = self._fetch(url)
        if soup is None:
            return []

        listings: list[dict] = []

        for card in soup.select(".job-card")[:20]:
            title_el = card.select_one(".job-title a")
            if not title_el:
                continue

            title_text = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            full_url = f"https://academicjobs.world{href}" if href.startswith("/") else href

            institution_el = card.select_one(".institution-name")
            institution = institution_el.get_text(strip=True) if institution_el else ""

            location_el = card.select_one(".location")
            loc_text = location_el.get_text(strip=True) if location_el else location

            desc_el = card.select_one(".job-summary")
            desc = desc_el.get_text(strip=True) if desc_el else ""

            deadline_el = card.select_one(".deadline")
            deadline = deadline_el.get_text(strip=True) if deadline_el else None

            listings.append({
                "title": title_text,
                "institution": institution,
                "location": loc_text,
                "url": full_url,
                "description": desc,
                "deadline": deadline,
                "email": self._extract_email(desc),
                "source": self.name,
                "type": self._detect_type(title_text, desc),
            })

            self._sleep()  # polite delay between detail page fetches if needed

        return listings
```

### Required dict keys

Every listing dict returned by `scrape()` should have these keys (use `""` or `None` for missing values — never omit a key):

| Key | Type | Description |
|---|---|---|
| `title` | `str` | Position title |
| `institution` | `str` | University or research institute name (can be `""`) |
| `location` | `str` | City/country of the position |
| `url` | `str` | Direct URL to the listing |
| `description` | `str` | Text excerpt or full description |
| `deadline` | `str \| None` | Application deadline string, or `None` |
| `email` | `str \| None` | Contact email, or `None` |
| `source` | `str` | Must equal `self.name` |
| `type` | `str` | Use `self._detect_type(title, desc)` |

---

## Step 2 — Export from the scrapers package

Open `agent/scrapers/__init__.py` and add your class to the imports and `__all__`:

```python
# agent/scrapers/__init__.py

from agent.scrapers.euraxess import EuraxessScraper
from agent.scrapers.mlscientist import MLScientistScraper
from agent.scrapers.jobs_ac_uk import JobsAcUkScraper
from agent.scrapers.web import WebSearchScraper
from agent.scrapers.academicjobs import AcademicJobsScraper  # ← add this

__all__ = [
    "EuraxessScraper",
    "MLScientistScraper",
    "JobsAcUkScraper",
    "WebSearchScraper",
    "AcademicJobsScraper",  # ← add this
]
```

---

## Step 3 — Register in JobSearcher

Open `agent/searcher.py` and add your scraper to the `_build_scrapers` static method:

```python
from agent.scrapers import (
    EuraxessScraper,
    JobsAcUkScraper,
    MLScientistScraper,
    WebSearchScraper,
    AcademicJobsScraper,  # ← add this import
)

@staticmethod
def _build_scrapers(location: str) -> list[BaseScraper]:
    scrapers: list[BaseScraper] = [
        EuraxessScraper(),
        MLScientistScraper(),
        AcademicJobsScraper(),  # ← add here
        WebSearchScraper(),
    ]
    if location.lower() in _UK_LOCATIONS or location.lower() in _WORLDWIDE_LOCATIONS:
        scrapers.insert(0, JobsAcUkScraper())
    return scrapers
```

!!! tip "Ordering matters"
    Scrapers are run in the order they appear in the list. Deduplication keeps the first occurrence of each URL, so put higher-quality sources earlier. `WebSearchScraper` is traditionally last because its results are noisier.

---

## Step 4 — Add location mappings (optional)

If your scraper needs to map human-readable location names to internal IDs, slugs, or query parameters, add a class-level dict like `EuraxessScraper._COUNTRY_ID` or `MLScientistScraper._COUNTRY_SLUG`:

```python
class AcademicJobsScraper(BaseScraper):
    name = "academicjobs"

    _REGION_SLUG: ClassVar[dict[str, str]] = {
        "uk": "united-kingdom",
        "united kingdom": "united-kingdom",
        "germany": "germany",
        "france": "france",
        "netherlands": "netherlands",
        "united states": "north-america",
        "usa": "north-america",
        "canada": "north-america",
        "australia": "australia",
        "japan": "asia",
    }

    def scrape(self, field: str, location: str, position_type: str) -> list[dict]:
        region = self._REGION_SLUG.get(location.lower(), "")
        url = f"https://academicjobs.world/jobs/{region}?q={quote_plus(field)}" if region \
              else f"https://academicjobs.world/jobs?q={quote_plus(field)}"
        ...
```

---

## Step 5 — Handle location filtering

If your source does not support server-side location filtering (common with many sites), apply a client-side filter before appending to `listings`:

```python
# Skip if location doesn't match (for non-Europe/Worldwide searches)
if location.lower() not in ("europe", "worldwide", ""):
    if location.lower() not in loc_text.lower():
        continue
```

This is the same pattern used by `EuraxessScraper`.

---

## Step 6 — Write a test

Add a test to ensure your scraper returns the expected structure. At minimum:

```python
# tests/test_academicjobs_scraper.py
from unittest.mock import patch, MagicMock
from agent.scrapers.academicjobs import AcademicJobsScraper


def test_scrape_returns_list():
    scraper = AcademicJobsScraper()
    # Patch _fetch to return None (simulates a down site)
    with patch.object(scraper, "_fetch", return_value=None):
        result = scraper.scrape("machine learning", "Germany", "phd")
    assert result == []


def test_scrape_structure():
    scraper = AcademicJobsScraper()
    # Provide minimal mock HTML
    from bs4 import BeautifulSoup
    html = """
    <div class="job-card">
      <div class="job-title"><a href="/jobs/123">PhD in ML</a></div>
      <div class="institution-name">TU Berlin</div>
      <div class="location">Berlin, Germany</div>
      <div class="job-summary">We seek a PhD candidate in machine learning.</div>
    </div>
    """
    mock_soup = BeautifulSoup(html, "lxml")
    with patch.object(scraper, "_fetch", return_value=mock_soup):
        with patch.object(scraper, "_sleep"):
            result = scraper.scrape("machine learning", "Germany", "phd")

    assert len(result) == 1
    job = result[0]
    assert job["title"] == "PhD in ML"
    assert job["institution"] == "TU Berlin"
    assert job["source"] == "academicjobs"
    assert "type" in job
    assert "url" in job
```

---

## Design Guidelines

### Be polite

Always call `self._sleep()` between HTTP requests to the same domain. The default delay is 1.5 seconds. Do not make parallel requests within a single scraper.

### Fail gracefully

`JobSearcher.search()` wraps each scraper in `try/except Exception: pass`. Your scraper should also be defensive internally — check for `None` returns from `_fetch()` and use `.get()` when accessing BeautifulSoup elements.

### Keep descriptions short but informative

Descriptions are truncated to 1500 characters in `job_description()` before being passed to the LLM. Include the most relevant information (research area, requirements, supervisor) near the beginning.

### Do not paginate aggressively

Scraping too many pages slows down the search and may trigger rate limits. Aim for 15–25 results per source. The overall pipeline is designed for interactive use, not bulk scraping.

### Position type detection

Always set `"type"` using `self._detect_type(title_text, desc)`. Never hardcode the type based on the source — the same board may list PhD, postdoc, and fellowship positions.

---

## Full Example: Nature Jobs Scraper

Here is a more complete example showing all the patterns together:

```python
"""naturejobs.com scraper (example — not in the default codebase)."""

from __future__ import annotations

from typing import ClassVar
from urllib.parse import quote_plus

from agent.scrapers.base import BaseScraper


class NatureJobsScraper(BaseScraper):
    """Scrapes nature.com/naturejobs for research positions."""

    name = "naturejobs"

    _DISCIPLINE_MAP: ClassVar[dict[str, str]] = {
        "biology": "biological-sciences",
        "chemistry": "chemistry",
        "physics": "physics",
        "computer science": "computer-science",
        "machine learning": "computer-science",
    }

    def scrape(self, field: str, location: str, position_type: str) -> list[dict]:
        discipline = self._find_discipline(field)
        loc_param = f"&location={quote_plus(location)}" if location else ""
        url = (
            f"https://www.nature.com/naturejobs/science/jobs"
            f"?utf8=✓&keywords={quote_plus(field)}"
            f"{loc_param}"
            + (f"&discipline={discipline}" if discipline else "")
        )

        soup = self._fetch(url)
        if soup is None:
            return []

        listings: list[dict] = []
        for card in soup.select("li.job-card")[:20]:
            title_el = card.select_one("h3 a.job-title")
            if not title_el:
                continue

            title_text = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            full_url = f"https://www.nature.com{href}" if href.startswith("/") else href

            employer_el = card.select_one(".employer")
            employer = employer_el.get_text(strip=True) if employer_el else ""

            loc_el = card.select_one(".location")
            loc_text = loc_el.get_text(strip=True) if loc_el else location

            # Location filter for non-worldwide searches
            if location.lower() not in ("europe", "worldwide", ""):
                if location.lower() not in loc_text.lower():
                    continue

            summary_el = card.select_one(".summary")
            desc = summary_el.get_text(strip=True) if summary_el else ""

            closing_el = card.select_one(".closing-date")
            deadline = closing_el.get_text(strip=True) if closing_el else None

            listings.append({
                "title": title_text,
                "institution": employer,
                "location": loc_text,
                "url": full_url,
                "description": desc,
                "deadline": deadline,
                "email": self._extract_email(desc),
                "source": self.name,
                "type": self._detect_type(title_text, desc),
            })

        return listings

    def _find_discipline(self, field: str) -> str:
        """Map a free-text field to a Nature Jobs discipline slug."""
        field_lower = field.lower()
        for key, slug in self._DISCIPLINE_MAP.items():
            if key in field_lower:
                return slug
        return ""
```
