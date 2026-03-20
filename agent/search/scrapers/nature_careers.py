"""nature.com/careers scraper — multidisciplinary global academic job board."""

from __future__ import annotations

import re
from urllib.parse import quote_plus

from agent.search.scrapers.base import BaseScraper


# ISO 3166-1 alpha-2 → normalised country name (lowercase, matches location strings)
_CC_COUNTRY: dict[str, str] = {
    "AT": "austria", "BE": "belgium", "BG": "bulgaria", "HR": "croatia",
    "CY": "cyprus", "CZ": "czech republic", "DK": "denmark", "EE": "estonia",
    "FI": "finland", "FR": "france", "DE": "germany", "GR": "greece",
    "HU": "hungary", "IE": "ireland", "IT": "italy", "LV": "latvia",
    "LT": "lithuania", "LU": "luxembourg", "MT": "malta", "NL": "netherlands",
    "PL": "poland", "PT": "portugal", "RO": "romania", "SK": "slovakia",
    "SI": "slovenia", "ES": "spain", "SE": "sweden", "GB": "united kingdom",
    "IS": "iceland", "NO": "norway", "CH": "switzerland", "TR": "turkey",
    "RS": "serbia", "US": "united states", "CA": "canada", "AU": "australia",
    "JP": "japan", "KR": "south korea", "CN": "china", "SG": "singapore",
    "IN": "india", "NZ": "new zealand", "ZA": "south africa", "IL": "israel",
    "BR": "brazil",
}

_UK_ALIASES: frozenset[str] = frozenset({"uk", "united kingdom", "great britain", "england", "scotland", "wales"})

_EUROPEAN_CC: frozenset[str] = frozenset({
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE", "GB", "IS", "NO", "CH", "TR", "RS",
})


class NatureCareersScraper(BaseScraper):
    """Scrapes nature.com/careers with keyword search and client-side location filter."""

    name = "nature.com/careers"

    def scrape(self, field: str, location: str, position_type: str) -> list[dict]:
        url = (
            f"https://www.nature.com/naturecareers/jobs/search/"
            f"?q={quote_plus(field)}&pageSize=25"
        )
        soup = self._fetch(url)
        if soup is None:
            return []

        loc_lower = location.lower()
        is_worldwide = loc_lower in ("worldwide", "")
        is_europe = loc_lower in ("europe", "europe (all)")
        # Resolve UK aliases to a single canonical string for matching
        canonical_loc = "united kingdom" if loc_lower in _UK_ALIASES else loc_lower

        listings: list[dict] = []
        for item in soup.select("li.lister__item")[:25]:
            title_el = item.select_one("h3.lister__header a")
            if not title_el:
                continue

            href = title_el.get("href", "").strip()
            if not href:
                continue
            full_url = ("https://www.nature.com" + href) if href.startswith("/") else href

            loc_el = item.select_one(".lister__meta-item--location")
            loc_text = loc_el.get_text(strip=True) if loc_el else ""

            # Extract ISO 2-letter country code from e.g. "Berlin (DE)"
            cc_match = re.search(r"\(([A-Z]{2})\)\s*$", loc_text)
            cc = cc_match.group(1) if cc_match else ""
            country_name = _CC_COUNTRY.get(cc, "")

            # Location filtering
            if not is_worldwide:
                if is_europe:
                    if cc and cc not in _EUROPEAN_CC:
                        continue
                else:
                    # Specific country: match via country code → name, or direct text
                    if cc:
                        if country_name != canonical_loc:
                            continue
                    elif canonical_loc not in loc_text.lower():
                        continue

            employer_el = item.select_one(".lister__meta-item--recruiter")
            institution = employer_el.get_text(strip=True) if employer_el else ""

            desc_el = item.select_one("p:not(.badge)")
            desc = desc_el.get_text(strip=True) if desc_el else ""

            # "New" badge means posted within last 2 days; no exact date available
            is_new = bool(item.select_one(".badge--green"))
            posted = "1 day ago" if is_new else None

            title_text = re.sub(r"\s+", " ", title_el.get_text(" ", strip=True)).strip()
            listings.append({
                "title": title_text,
                "institution": institution,
                "location": loc_text,
                "url": full_url,
                "description": desc,
                "deadline": None,
                "posted": posted,
                "email": self._extract_email(desc),
                "source": self.name,
                "type": self._detect_type(title_text, desc),
            })

        return listings
