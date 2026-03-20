"""Tests for JobMatcher — mocks LLM to test scoring logic without API calls."""

from unittest.mock import MagicMock, patch
import pytest
from agent.job_matcher import JobMatcher, _fallback
from agent.llm_client import LLMClient, LLMQuotaError


def _make_matcher(llm_response: str | Exception) -> JobMatcher:
    """Return a JobMatcher whose LLM always returns the given response."""
    llm = MagicMock(spec=LLMClient)
    if isinstance(llm_response, Exception):
        llm.generate.side_effect = llm_response
    else:
        llm.generate.return_value = llm_response
    return JobMatcher(llm)


GOOD_JSON = """{
    "match_score": 82,
    "recommendation": "apply",
    "matching_areas": ["machine learning", "NLP"],
    "missing_requirements": [],
    "why_good_fit": "Strong ML background.",
    "concerns": ""
}"""

LOW_JSON = """{
    "match_score": 20,
    "recommendation": "skip",
    "matching_areas": [],
    "missing_requirements": ["wet lab experience"],
    "why_good_fit": "",
    "concerns": "Very different field."
}"""

JOB = {"title": "PhD in ML", "institution": "MIT", "location": "USA",
       "type": "phd", "description": "Machine learning research position."}
PROFILE = "Researcher with 3 years ML experience, 2 NeurIPS papers."


class TestScore:
    def test_good_match(self):
        matcher = _make_matcher(GOOD_JSON)
        result = matcher.score(JOB, PROFILE)
        assert result["match_score"] == 82
        assert result["recommendation"] == "apply"
        assert "machine learning" in result["matching_areas"]

    def test_low_match(self):
        matcher = _make_matcher(LOW_JSON)
        result = matcher.score(JOB, PROFILE)
        assert result["match_score"] == 20
        assert result["recommendation"] == "skip"

    def test_score_clamped_to_100(self):
        matcher = _make_matcher('{"match_score": 150, "recommendation": "apply", '
                                '"matching_areas": [], "missing_requirements": [], '
                                '"why_good_fit": "", "concerns": ""}')
        result = matcher.score(JOB, PROFILE)
        assert result["match_score"] == 100

    def test_score_clamped_to_0(self):
        matcher = _make_matcher('{"match_score": -10, "recommendation": "skip", '
                                '"matching_areas": [], "missing_requirements": [], '
                                '"why_good_fit": "", "concerns": ""}')
        result = matcher.score(JOB, PROFILE)
        assert result["match_score"] == 0

    def test_llm_error_surfaces_message(self):
        matcher = _make_matcher(RuntimeError("Groq inference failed: 401 Unauthorized"))
        result = matcher.score(JOB, PROFILE)
        assert result["match_score"] == 0
        assert "Groq inference failed" in result["concerns"]

    def test_invalid_json_returns_fallback(self):
        matcher = _make_matcher("this is not json at all")
        result = matcher.score(JOB, PROFILE)
        assert result["match_score"] == 0
        assert result["recommendation"] == "skip"

    def test_quota_error_propagates(self):
        matcher = _make_matcher(LLMQuotaError("Quota exceeded"))
        with pytest.raises(LLMQuotaError):
            matcher.score(JOB, PROFILE)

    def test_recommendation_inferred_when_missing(self):
        # LLM returns invalid recommendation — should be inferred from score
        matcher = _make_matcher('{"match_score": 75, "recommendation": "maybe", '
                                '"matching_areas": [], "missing_requirements": [], '
                                '"why_good_fit": "", "concerns": ""}')
        result = matcher.score(JOB, PROFILE)
        assert result["recommendation"] == "apply"  # score >= 70


class TestScoreAll:
    def test_sorted_by_score_descending(self):
        responses = [GOOD_JSON, LOW_JSON, GOOD_JSON]
        call_count = [0]
        llm = MagicMock(spec=LLMClient)
        def side_effect(*args, **kwargs):
            r = responses[call_count[0]]
            call_count[0] += 1
            return r
        llm.generate.side_effect = side_effect
        matcher = JobMatcher(llm)
        jobs = [JOB, JOB, JOB]
        scored = matcher.score_all(jobs, PROFILE)
        scores = [j["match"]["match_score"] for j in scored]
        assert scores == sorted(scores, reverse=True)


class TestFallback:
    def test_fallback_structure(self):
        fb = _fallback("test error")
        assert fb["match_score"] == 0
        assert fb["recommendation"] == "skip"
        assert "test error" in fb["concerns"]
        assert isinstance(fb["matching_areas"], list)
