"""scholarshipdb.net scraper — worldwide academic jobs and scholarships."""

from __future__ import annotations

import re
from typing import ClassVar
from urllib.parse import quote_plus

from agent.search.scrapers.base import BaseScraper


_EUROPEAN_COUNTRIES: frozenset[str] = frozenset({
    "austria", "belgium", "bulgaria", "croatia", "cyprus", "czech republic",
    "denmark", "estonia", "finland", "france", "germany", "greece", "hungary",
    "iceland", "ireland", "italy", "latvia", "lithuania", "luxembourg", "malta",
    "netherlands", "norway", "poland", "portugal", "romania", "serbia",
    "slovakia", "slovenia", "spain", "sweden", "switzerland", "turkey",
    "united kingdom",
})


class ScholarshipDbScraper(BaseScraper):
    """Scrapes scholarshipdb.net with keyword and optional country filters."""

    name = "scholarshipdb"

    _COUNTRY_SLUG: ClassVar[dict[str, str]] = {
        "uk": "United-Kingdom",
        "united kingdom": "United-Kingdom",
        "great britain": "United-Kingdom",
        "england": "United-Kingdom",
        "scotland": "United-Kingdom",
        "wales": "United-Kingdom",
        "germany": "Germany",
        "france": "France",
        "italy": "Italy",
        "spain": "Spain",
        "netherlands": "Netherlands",
        "denmark": "Denmark",
        "norway": "Norway",
        "austria": "Austria",
        "ireland": "Ireland",
        "belgium": "Belgium",
        "switzerland": "Switzerland",
        "sweden": "Sweden",
        "finland": "Finland",
        "portugal": "Portugal",
        "poland": "Poland",
        "czech republic": "Czech-Republic",
        "hungary": "Hungary",
        "romania": "Romania",
        "greece": "Greece",
        "croatia": "Croatia",
        "slovakia": "Slovakia",
        "slovenia": "Slovenia",
        "bulgaria": "Bulgaria",
        "estonia": "Estonia",
        "latvia": "Latvia",
        "lithuania": "Lithuania",
        "luxembourg": "Luxembourg",
        "serbia": "Serbia",
        "turkey": "Turkey",
        "united states": "United-States",
        "usa": "United-States",
        "canada": "Canada",
        "australia": "Australia",
        "japan": "Japan",
        "south korea": "South-Korea",
        "china": "China",
        "singapore": "Singapore",
        "india": "India",
        "new zealand": "New-Zealand",
        "south africa": "South-Africa",
        "israel": "Israel",
        "brazil": "Brazil",
    }

    def scrape(self, field: str, location: str, position_type: str) -> list[dict]:
        loc_lower = location.lower()
        country_slug = self._COUNTRY_SLUG.get(loc_lower, "")
        is_europe = loc_lower in ("europe", "europe (all)")
        is_worldwide = loc_lower in ("worldwide", "")

        if country_slug:
            url = (
                f"https://scholarshipdb.net/scholarships-in-{country_slug}"
                f"?q={quote_plus(field)}"
            )
        else:
            url = f"https://scholarshipdb.net/scholarships?q={quote_plus(field)}"

        soup = self._fetch(url)
        if soup is None:
            return []

        listings: list[dict] = []
        for li in soup.select("li"):
            title_el = li.select_one("h4 a")
            if not title_el:
                continue

            href = title_el.get("href", "")
            full_url = "https://scholarshipdb.net" + href if href.startswith("/") else href

            # Parse metadata from the second <div> inside the <li>
            divs = li.select("div")
            meta_div = divs[1] if len(divs) > 1 else None

            institution = ""
            city = ""
            country_text = ""
            posted_text = None

            if meta_div:
                inst_link = meta_div.select_one("a[href*='scholarships-at']")
                if inst_link:
                    institution = inst_link.get_text(strip=True)
                city_span = meta_div.select_one("span.text-success")
                if city_span:
                    city = city_span.get_text(strip=True)
                country_link = meta_div.select_one("a.text-success")
                if country_link:
                    country_text = country_link.get_text(strip=True)
                muted = meta_div.select_one(".text-muted")
                if muted:
                    posted_text = muted.get_text(strip=True)

            loc_text = ", ".join(filter(None, [city, country_text])) or location

            # Location post-filter
            if not is_worldwide and not country_slug:
                if is_europe:
                    if country_text and country_text.lower() not in _EUROPEAN_COUNTRIES:
                        continue
                else:
                    # Unsupported country: filter by card country text when available
                    if country_text and location.lower() not in country_text.lower():
                        continue

            desc_el = li.select_one("p")
            desc = desc_el.get_text(strip=True) if desc_el else ""

            title_text = re.sub(r"\s+", " ", title_el.get_text(" ", strip=True)).strip()
            listings.append({
                "title": title_text,
                "institution": institution,
                "location": loc_text,
                "url": full_url,
                "description": desc,
                "deadline": None,
                "posted": posted_text,
                "email": self._extract_email(desc),
                "source": self.name,
                "type": self._detect_type(title_text, desc),
            })

        return listings
