"""Job searcher: finds PhD / postdoc / research positions from free public sources.

Sources: DuckDuckGo, Euraxess, jobs.ac.uk (RSS), FindAPhD, Academic Positions.
All scrapers are wrapped in try/except — if one source is down the rest continue.
"""

from __future__ import annotations

import re
import time
from typing import Any, TypedDict
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


class JobListing(TypedDict, total=False):
    title: str
    institution: str
    location: str
    url: str
    description: str
    deadline: str | None
    email: str | None
    source: str
    type: str


_TYPE_KEYWORDS: dict[str, list[str]] = {
    "phd": ["phd", "ph.d", "doctoral", "doctorate", "phd student", "phd candidate",
            "phd position", "phd fellowship", "graduate student"],
    "postdoc": ["postdoc", "post-doc", "post doc", "postdoctoral", "research associate",
                "research fellow"],
    "fellowship": ["fellowship", "stipend", "marie curie", "marie skłodowska",
                   "horizon europe", "erc", "scholarship"],
    "research_staff": ["researcher", "research scientist", "research engineer",
                       "staff scientist", "principal investigator", "pi position"],
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

_DELAY = 1.0  # polite delay between HTTP requests (seconds)


def _detect_type(title: str, description: str) -> str:
    combined = (title + " " + description).lower()
    for pos_type, keywords in _TYPE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return pos_type
    return "other"


def _extract_email(text: str) -> str | None:
    m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return m.group() if m else None


def _deduplicate(listings: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for item in listings:
        url = (item.get("url") or "").strip().rstrip("/")
        if url and url not in seen:
            seen.add(url)
            result.append(item)
        elif not url:
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Source scrapers (module-level private functions)
# ---------------------------------------------------------------------------

def _search_duckduckgo(field: str, location: str) -> list[dict]:
    try:
        from duckduckgo_search import DDGS  # type: ignore
    except ImportError:
        return []

    queries = [
        f"PhD position {field} {location} 2025 site:euraxess.ec.europa.eu",
        f"postdoc {field} {location} 2025 fellowship",
        f"research position {field} {location} university",
        f"PhD fellowship {field} site:findaphd.com",
        f"academic jobs {field} site:jobs.ac.uk",
    ]

    raw: list[dict] = []
    ddgs = DDGS()
    for query in queries:
        try:
            results = ddgs.text(query, max_results=10)
            if results:
                raw.extend(results)
            time.sleep(_DELAY)
        except Exception:
            continue

    return [
        {
            "title": r.get("title", ""),
            "institution": "",
            "location": location,
            "url": r.get("href", ""),
            "description": r.get("body", ""),
            "deadline": None,
            "email": _extract_email(r.get("body", "")),
            "source": "ddg",
            "type": _detect_type(r.get("title", ""), r.get("body", "")),
        }
        for r in raw
    ]


def _search_euraxess(field: str, location: str) -> list[dict]:
    url = "https://euraxess.ec.europa.eu/api/v1/jobs/search"
    params: dict[str, Any] = {"keywords": field, "page": 1, "per_page": 20}
    if location and location.lower() not in ("europe", "anywhere", "worldwide", ""):
        params["country"] = location

    try:
        resp = requests.get(url, params=params, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        jobs_raw = data if isinstance(data, list) else data.get("jobs", data.get("data", []))
        if not isinstance(jobs_raw, list):
            return []

        return [
            {
                "title": job.get("title") or job.get("name") or "",
                "institution": job.get("organisation") or job.get("institution") or job.get("employer") or "",
                "location": job.get("location") or job.get("country") or job.get("city") or location,
                "url": job.get("url") or job.get("link") or "",
                "description": job.get("description") or job.get("body") or "",
                "deadline": job.get("application_deadline") or job.get("deadline"),
                "email": _extract_email(job.get("description") or ""),
                "source": "euraxess",
                "type": _detect_type(job.get("title") or "", job.get("description") or ""),
            }
            for job in jobs_raw
        ]
    except Exception:
        return []


def _search_jobs_ac_uk(field: str, location: str) -> list[dict]:
    try:
        import feedparser  # type: ignore
    except ImportError:
        return []

    rss_url = (
        f"https://www.jobs.ac.uk/search/?keywords={quote_plus(field)}"
        f"&location={quote_plus(location)}&rss=1"
    )
    try:
        feed = feedparser.parse(rss_url)
        return [
            {
                "title": entry.get("title", ""),
                "institution": entry.get("author") or entry.get("dc_source") or "",
                "location": location,
                "url": entry.get("link", ""),
                "description": entry.get("summary", ""),
                "deadline": entry.get("published"),
                "email": _extract_email(entry.get("summary", "")),
                "source": "jobs.ac.uk",
                "type": _detect_type(entry.get("title", ""), entry.get("summary", "")),
            }
            for entry in feed.entries[:20]
        ]
    except Exception:
        return []


def _search_findaphd(field: str, location: str) -> list[dict]:
    url = f"https://www.findaphd.com/phds/?Keywords={quote_plus(field)}&Location={quote_plus(location)}"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        listings = []
        for card in soup.select(".phd-result, .row.phd-result, article.phd-result")[:20]:
            title_el = card.select_one("h3 a, h2 a, .phd-result__title a")
            if not title_el:
                continue
            href = title_el.get("href", "")
            full_url = ("https://www.findaphd.com" + href) if href.startswith("/") else href
            inst_el = card.select_one(".phd-result__dept, .phd-result__uni, .uni-link")
            desc_el = card.select_one(".phd-result__description, .project-description, p")
            deadline_el = card.select_one(".deadline, .closing-date, time")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            listings.append({
                "title": title_el.get_text(strip=True),
                "institution": inst_el.get_text(strip=True) if inst_el else "",
                "location": location,
                "url": full_url,
                "description": desc,
                "deadline": deadline_el.get_text(strip=True) if deadline_el else None,
                "email": _extract_email(desc),
                "source": "findaphd",
                "type": "phd",
            })
        return listings
    except Exception:
        return []


def _search_academic_positions(field: str, location: str) -> list[dict]:
    url = f"https://academicpositions.com/find-jobs/?query={quote_plus(field)}&location={quote_plus(location)}"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        listings = []
        for card in soup.select("article.job, .job-item, li.job-listing, .vacancy-item")[:20]:
            title_el = card.select_one("h2 a, h3 a, .job-title a, a.job-link")
            if not title_el:
                continue
            href = title_el.get("href", "")
            if href and not href.startswith("http"):
                href = "https://academicpositions.com" + href
            inst_el = card.select_one(".employer, .institution, .university")
            loc_el = card.select_one(".location, .job-location")
            desc_el = card.select_one(".description, .job-description, p")
            deadline_el = card.select_one(".deadline, .closing, time")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            listings.append({
                "title": title_el.get_text(strip=True),
                "institution": inst_el.get_text(strip=True) if inst_el else "",
                "location": loc_el.get_text(strip=True) if loc_el else location,
                "url": href,
                "description": desc,
                "deadline": deadline_el.get_text(strip=True) if deadline_el else None,
                "email": _extract_email(desc),
                "source": "academicpositions",
                "type": _detect_type(title_el.get_text(strip=True), desc),
            })
        return listings
    except Exception:
        return []


# ---------------------------------------------------------------------------
# JobSearcher class
# ---------------------------------------------------------------------------

class JobSearcher:
    """Searches for research/PhD positions across all available free sources."""

    def search(
        self,
        field: str,
        location: str = "Europe",
        position_type: str = "any",
    ) -> list[dict]:
        """Search all sources and return deduplicated listings.

        Args:
            field:         Research field (e.g. "machine learning").
            location:      Preferred location (e.g. "Europe", "UK").
            position_type: Filter: "phd", "postdoc", "fellowship", "research_staff", or "any".

        Returns:
            Deduplicated list of JobListing dicts, sorted with richer entries first.
        """
        all_listings: list[dict] = []

        for scraper in [
            _search_duckduckgo,
            _search_euraxess,
            _search_jobs_ac_uk,
            _search_findaphd,
            _search_academic_positions,
        ]:
            try:
                results = scraper(field, location)
                all_listings.extend(results)
            except Exception:
                pass
            time.sleep(_DELAY)

        all_listings = _deduplicate(all_listings)

        if position_type and position_type.lower() != "any":
            all_listings = [j for j in all_listings if j.get("type") == position_type.lower()]

        all_listings.sort(key=lambda j: len(j.get("description") or ""), reverse=True)
        return all_listings
