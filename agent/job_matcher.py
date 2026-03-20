"""Job matcher — scores research positions against a CV profile."""

from __future__ import annotations

from typing import Any, TypedDict

from agent.base_service import BaseLLMService
from agent.prompts import JOB_MATCHER_SYSTEM, JOB_MATCHER_PROMPT
from agent.utils import job_description, job_institution


class MatchResult(TypedDict, total=False):
    match_score: int
    recommendation: str               # "apply" | "consider" | "skip"
    matching_areas: list[str]
    missing_requirements: list[str]
    why_good_fit: str
    concerns: str




def _fallback(reason: str) -> MatchResult:
    return {
        "match_score": 0,
        "recommendation": "skip",
        "matching_areas": [],
        "missing_requirements": [],
        "why_good_fit": "",
        "concerns": f"Could not score position: {reason[:200]}",
    }


class JobMatcher(BaseLLMService):
    """Scores job listings against a CV profile using an LLM."""

    _SYSTEM = JOB_MATCHER_SYSTEM

    def score(self, job: dict[str, Any], profile_text: str) -> MatchResult:
        """Score a single job listing against a CV profile summary."""
        prompt = JOB_MATCHER_PROMPT.format(
            profile=profile_text,
            title=job.get("title", "Unknown"),
            institution=job_institution(job) or "Unknown",
            location=job.get("location", "Unknown"),
            pos_type=job.get("type", "unknown"),
            description=job_description(job),
        )

        result = self._generate_json(prompt)
        if result is None:
            return _fallback("Response was not valid JSON")
        if "_llm_error" in result:
            return _fallback(result["_llm_error"])

        try:
            result["match_score"] = max(0, min(100, int(result.get("match_score", 0))))
        except (TypeError, ValueError):
            result["match_score"] = 0

        if result.get("recommendation") not in ("apply", "consider", "skip"):
            score = result.get("match_score", 0)
            result["recommendation"] = (
                "apply" if score >= 70 else ("consider" if score >= 50 else "skip")
            )

        return result

    def score_all(
        self,
        jobs: list[dict[str, Any]],
        profile_text: str,
    ) -> list[dict[str, Any]]:
        """Score all jobs and return them sorted by score (highest first)."""
        scored = [{**job, "match": self.score(job, profile_text)} for job in jobs]
        scored.sort(key=lambda j: j["match"].get("match_score", 0), reverse=True)
        return scored
