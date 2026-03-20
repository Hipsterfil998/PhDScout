"""Tests for ScholarshipDbScraper and NatureCareersScraper — no real HTTP calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from agent.search.scrapers.scholarshipdb import ScholarshipDbScraper
from agent.search.scrapers.nature_careers import NatureCareersScraper


# ---------------------------------------------------------------------------
# Minimal HTML fixtures
# ---------------------------------------------------------------------------

_SCHOLARSHIPDB_HTML = """
<html><body><ul>
<li>
  <div><h4><a href="/jobs-in-Germany/Phd-Machine-Learning-TU-Berlin=abc.html">
    PhD in Machine Learning</a></h4></div>
  <div>
    <a href="/scholarships-at-TU-Berlin">TU Berlin</a> |
    <span class="text-success">Berlin, Berlin</span> |
    <a class="text-success" href="/scholarships-in-Germany">Germany</a> |
    <span class="text-muted">2 days ago</span>
  </div>
  <div><p>PhD position in deep learning and computer vision.</p></div>
</li>
<li>
  <div><h4><a href="/jobs-in-France/Postdoc-NLP-CNRS=xyz.html">
    Postdoc in NLP</a></h4></div>
  <div>
    <a href="/scholarships-at-CNRS">CNRS</a> |
    <a class="text-success" href="/scholarships-in-France">France</a> |
    <span class="text-muted">5 days ago</span>
  </div>
  <div><p>Postdoctoral position in natural language processing.</p></div>
</li>
</ul></body></html>
"""

_NATURE_HTML = """
<html><body><ul>
<li class="lister__item" id="item-111">
  <p class="badge badge--right badge--green">New</p>
  <div class="lister__details cf js-clickable">
    <h3 class="lister__header">
      <a class="js-clickable-area-link" href="/naturecareers/job/111/phd-ml/">
        <span>PhD position in Machine Learning</span>
      </a>
    </h3>
    <ul class="lister__meta">
      <li class="lister__meta-item lister__meta-item--location">Berlin (DE)</li>
      <li class="lister__meta-item lister__meta-item--recruiter">TU Berlin</li>
    </ul>
    <p>Join our ML group for cutting-edge deep learning research.</p>
  </div>
</li>
<li class="lister__item" id="item-222">
  <div class="lister__details cf js-clickable">
    <h3 class="lister__header">
      <a class="js-clickable-area-link" href="/naturecareers/job/222/postdoc-nlp/">
        <span>Postdoctoral researcher in NLP</span>
      </a>
    </h3>
    <ul class="lister__meta">
      <li class="lister__meta-item lister__meta-item--location">Paris (FR)</li>
      <li class="lister__meta-item lister__meta-item--recruiter">CNRS</li>
    </ul>
    <p>NLP postdoc at CNRS Paris.</p>
  </div>
</li>
</ul></body></html>
"""


def _mock_fetch(html: str):
    """Return a _fetch side_effect that always returns parsed HTML."""
    def _fetch(url, **kwargs):
        return BeautifulSoup(html, "lxml")
    return _fetch


# ---------------------------------------------------------------------------
# ScholarshipDbScraper
# ---------------------------------------------------------------------------

class TestScholarshipDbScraper:
    def _scrape(self, location, html=_SCHOLARSHIPDB_HTML):
        s = ScholarshipDbScraper()
        with patch.object(s, "_fetch", side_effect=_mock_fetch(html)):
            return s.scrape("machine learning", location, "any")

    def test_parses_title_and_url(self):
        results = self._scrape("Germany")
        titles = [r["title"] for r in results]
        assert any("Machine Learning" in t for t in titles)

    def test_parses_institution(self):
        results = self._scrape("Germany")
        assert any(r["institution"] == "TU Berlin" for r in results)

    def test_parses_location_text(self):
        results = self._scrape("Germany")
        assert any("Germany" in r["location"] for r in results)

    def test_parses_posted_date(self):
        results = self._scrape("Germany")
        assert any(r["posted"] == "2 days ago" for r in results)

    def test_parses_description(self):
        results = self._scrape("Germany")
        assert any("deep learning" in r["description"] for r in results)

    def test_mapped_country_builds_slug_url(self):
        # For countries with a slug, filtering is server-side via URL path.
        # Verify the correct URL is requested.
        s = ScholarshipDbScraper()
        called_urls = []
        def fake_fetch(url, **kwargs):
            called_urls.append(url)
            return BeautifulSoup(_SCHOLARSHIPDB_HTML, "lxml")
        with patch.object(s, "_fetch", side_effect=fake_fetch):
            s.scrape("machine learning", "Germany", "any")
        assert any("scholarships-in-Germany" in u for u in called_urls)

    def test_unmapped_country_client_filters(self):
        # Malta has no slug → client-side filter applies using country link text.
        html = _SCHOLARSHIPDB_HTML.replace(
            '<a class="text-success" href="/scholarships-in-Germany">Germany</a>',
            '<a class="text-success" href="/scholarships-in-Malta">Malta</a>',
        ).replace(
            '<a class="text-success" href="/scholarships-in-France">France</a>',
            '<a class="text-success" href="/scholarships-in-France">France</a>',
        )
        results = self._scrape("Malta", html=html)
        assert len(results) == 1
        assert "Malta" in results[0]["location"]

    def test_europe_keeps_both(self):
        results = self._scrape("Europe")
        assert len(results) == 2

    def test_worldwide_keeps_all(self):
        results = self._scrape("")
        assert len(results) == 2

    def test_url_is_absolute(self):
        results = self._scrape("")
        for r in results:
            assert r["url"].startswith("https://scholarshipdb.net")

    def test_source_name(self):
        results = self._scrape("")
        assert all(r["source"] == "scholarshipdb" for r in results)

    def test_type_detected(self):
        results = self._scrape("Germany")
        phd_result = next(r for r in results if "PhD" in r["title"])
        assert phd_result["type"] == "phd"


# ---------------------------------------------------------------------------
# NatureCareersScraper
# ---------------------------------------------------------------------------

class TestNatureCareersScraper:
    def _scrape(self, location, html=_NATURE_HTML):
        s = NatureCareersScraper()
        with patch.object(s, "_fetch", side_effect=_mock_fetch(html)):
            return s.scrape("machine learning", location, "any")

    def test_parses_title(self):
        results = self._scrape("")
        titles = [r["title"] for r in results]
        assert "PhD position in Machine Learning" in titles

    def test_parses_institution(self):
        results = self._scrape("")
        assert any(r["institution"] == "TU Berlin" for r in results)

    def test_parses_location(self):
        results = self._scrape("")
        assert any(r["location"] == "Berlin (DE)" for r in results)

    def test_new_badge_sets_posted(self):
        results = self._scrape("")
        berlin = next(r for r in results if r["location"] == "Berlin (DE)")
        assert berlin["posted"] == "1 day ago"

    def test_no_badge_posted_is_none(self):
        results = self._scrape("")
        paris = next(r for r in results if r["location"] == "Paris (FR)")
        assert paris["posted"] is None

    def test_country_filter_germany_only(self):
        results = self._scrape("Germany")
        assert len(results) == 1
        assert results[0]["location"] == "Berlin (DE)"

    def test_country_filter_france_only(self):
        results = self._scrape("France")
        assert len(results) == 1
        assert results[0]["location"] == "Paris (FR)"

    def test_europe_keeps_both(self):
        results = self._scrape("Europe")
        assert len(results) == 2

    def test_worldwide_keeps_all(self):
        results = self._scrape("")
        assert len(results) == 2

    def test_url_is_absolute(self):
        results = self._scrape("")
        for r in results:
            assert r["url"].startswith("https://www.nature.com")

    def test_source_name(self):
        results = self._scrape("")
        assert all(r["source"] == "nature.com/careers" for r in results)

    def test_type_detected(self):
        results = self._scrape("")
        phd = next(r for r in results if "PhD" in r["title"])
        assert phd["type"] == "phd"
        postdoc = next(r for r in results if "Postdoctoral" in r["title"])
        assert postdoc["type"] == "postdoc"

    def test_uk_alias_resolves(self):
        """'UK' should match jobs with country code GB."""
        html = _NATURE_HTML.replace("Berlin (DE)", "London (GB)").replace(
            "TU Berlin", "UCL"
        )
        results = self._scrape("UK", html=html)
        assert len(results) == 1
        assert "GB" in results[0]["location"]
