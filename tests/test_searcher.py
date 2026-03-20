"""Tests for JobSearcher — filtering, labelling, dedup, sorting. No HTTP."""

from datetime import datetime, timedelta
import pytest
from agent.searcher import JobSearcher


TODAY = datetime.now()
YESTERDAY = TODAY - timedelta(days=1)
LAST_YEAR = TODAY.replace(year=TODAY.year - 1)
RECENT = TODAY - timedelta(days=10)
OLDER = TODAY - timedelta(days=60)
CLOSING_SOON = TODAY + timedelta(days=7)
FAR_DEADLINE = TODAY + timedelta(days=90)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%d %B %Y")


class TestIsStale:
    def test_old_posting_year_filtered(self):
        job = {"posted": _fmt(LAST_YEAR), "deadline": None}
        assert JobSearcher._is_stale(job, TODAY)

    def test_expired_deadline_filtered(self):
        job = {"posted": None, "deadline": _fmt(YESTERDAY)}
        assert JobSearcher._is_stale(job, TODAY)

    def test_current_year_posting_kept(self):
        job = {"posted": _fmt(RECENT), "deadline": None}
        assert not JobSearcher._is_stale(job, TODAY)

    def test_future_deadline_kept(self):
        job = {"posted": None, "deadline": _fmt(CLOSING_SOON)}
        assert not JobSearcher._is_stale(job, TODAY)

    def test_no_dates_kept(self):
        job = {"posted": None, "deadline": None}
        assert not JobSearcher._is_stale(job, TODAY)

    def test_old_posting_future_deadline_filtered_by_posting(self):
        # posted last year → stale even if deadline is future
        job = {"posted": _fmt(LAST_YEAR), "deadline": _fmt(FAR_DEADLINE)}
        assert JobSearcher._is_stale(job, TODAY)


class TestFreshnessLabel:
    def test_recent(self):
        job = {"posted": _fmt(RECENT), "deadline": None}
        assert JobSearcher._freshness_label(job, TODAY) == "🟢 Recent"

    def test_older(self):
        job = {"posted": _fmt(OLDER), "deadline": _fmt(FAR_DEADLINE)}
        assert JobSearcher._freshness_label(job, TODAY) == "🟡 Older"

    def test_closing_soon_overrides_recent(self):
        job = {"posted": _fmt(RECENT), "deadline": _fmt(CLOSING_SOON)}
        assert JobSearcher._freshness_label(job, TODAY) == "🔴 Closing soon"

    def test_no_date_empty_label(self):
        job = {"posted": None, "deadline": None}
        assert JobSearcher._freshness_label(job, TODAY) == ""

    def test_only_far_deadline_no_posted(self):
        job = {"posted": None, "deadline": _fmt(FAR_DEADLINE)}
        assert JobSearcher._freshness_label(job, TODAY) == "🟡 Older"


class TestDeduplicate:
    def test_removes_duplicate_url(self):
        jobs = [
            {"url": "https://example.com/job/1", "title": "A"},
            {"url": "https://example.com/job/1", "title": "A duplicate"},
        ]
        result = JobSearcher._deduplicate(jobs)
        assert len(result) == 1

    def test_trailing_slash_dedup(self):
        jobs = [
            {"url": "https://example.com/job/1/", "title": "A"},
            {"url": "https://example.com/job/1", "title": "B"},
        ]
        assert len(JobSearcher._deduplicate(jobs)) == 1

    def test_different_urls_kept(self):
        jobs = [
            {"url": "https://example.com/job/1", "title": "A"},
            {"url": "https://example.com/job/2", "title": "B"},
        ]
        assert len(JobSearcher._deduplicate(jobs)) == 2

    def test_no_url_always_kept(self):
        jobs = [{"url": "", "title": "A"}, {"url": "", "title": "B"}]
        assert len(JobSearcher._deduplicate(jobs)) == 2


class TestFieldMatches:
    STOP = {"and", "the", "for", "with", "from"}

    def _match(self, listing, field):
        phrases = [p.strip().lower() for p in field.split(",") if p.strip()]
        return JobSearcher._field_matches(listing, phrases, self.STOP)

    def test_exact_phrase_in_title(self):
        job = {"title": "PhD in machine learning", "description": ""}
        assert self._match(job, "machine learning")

    def test_keywords_in_description(self):
        job = {"title": "Research Position", "description": "deep learning and neural networks"}
        assert self._match(job, "deep learning")

    def test_no_match(self):
        job = {"title": "Chemistry Lab Technician", "description": "wet lab experience"}
        assert not self._match(job, "machine learning")

    def test_multi_field_any_matches(self):
        job = {"title": "Postdoc in NLP", "description": ""}
        assert self._match(job, "computer vision, NLP")


class TestSortKey:
    def test_dated_before_undated(self):
        dated = {"posted": _fmt(OLDER), "deadline": None, "description": "x"}
        undated = {"posted": None, "deadline": None, "description": "x" * 1000}
        # dated should sort higher (has_date=True > False)
        assert JobSearcher._sort_key(dated) > JobSearcher._sort_key(undated)

    def test_newer_before_older(self):
        newer = {"posted": _fmt(RECENT), "deadline": None, "description": "x"}
        older = {"posted": _fmt(OLDER), "deadline": None, "description": "x"}
        assert JobSearcher._sort_key(newer) > JobSearcher._sort_key(older)

    def test_longer_desc_tiebreaker(self):
        a = {"posted": _fmt(RECENT), "deadline": None, "description": "x" * 100}
        b = {"posted": _fmt(RECENT), "deadline": None, "description": "x" * 50}
        assert JobSearcher._sort_key(a) > JobSearcher._sort_key(b)
