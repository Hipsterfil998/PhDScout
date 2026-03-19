"""Job matcher: scores research/PhD positions against a CV profile."""

from __future__ import annotations

from typing import Any, TypedDict

from agent.llm_client import LLMClient, LLMQuotaError
from agent.utils import parse_json, job_institution, job_description


class MatchResult(TypedDict, total=False):
    match_score: int
    recommendation: str               # "apply" | "consider" | "skip"
    matching_areas: list[str]
    missing_requirements: list[str]
    why_good_fit: str
    concerns: str


_SYSTEM = (
    "You are an expert academic recruiter specialising in PhD and postdoc placements. "
    "Evaluate how well a candidate's research profile fits a given position. "
    "Respond only with valid JSON — no markdown, no commentary."
)

_PROMPT = """Evaluate how well this candidate fits the research position below.

CANDIDATE PROFILE:
{profile}

POSITION:
Title: {title}
Institution: {institution}
Location: {location}
Type: {pos_type}
Description:
{description}

Return a JSON object with exactly these keys:
{{
  "match_score": <integer 0-100>,
  "recommendation": "apply" | "consider" | "skip",
  "matching_areas": ["research areas / skills that align"],
  "missing_requirements": ["gaps between candidate and requirements"],
  "why_good_fit": "2-3 sentence explanation of main strengths",
  "concerns": "1-2 sentence summary of gaps (empty string if none)"
}}

Scoring guide:
  85-100: Excellent match — research interests closely aligned, strong publication record in the area
  70-84:  Good match — clear research overlap, most skills present
  55-69:  Partial match — meaningful overlap even if not all keywords match exactly
  35-54:  Weak match — limited overlap, significant gaps
  0-34:   Poor match — very different research areas

Important instructions:
- The job description may be a short excerpt. When it is vague or brief, rely primarily
  on the TITLE and INSTITUTION to infer the research area — do NOT penalise short descriptions.
- Reason SEMANTICALLY, not by keyword matching. "Deep learning" and "neural networks",
  "NLP" and "natural language processing", "ML" and "machine learning" are equivalent.
- Adjacent and complementary fields count as partial overlap (score ≥ 55).
- Highlight ALL matching areas found in the candidate profile, including transferable
  methodological skills, domain knowledge, tools, and publications.
- Be generous when evidence is ambiguous — a candidate who publishes in area X is
  likely qualified for positions requiring closely related area Y.
- Consider: research interest alignment, thesis relevance, methodological overlap,
  publication track record, technical skills, career stage fit."""


def _fallback(raw: str) -> MatchResult:
    return {
        "match_score": 0,
        "recommendation": "skip",
        "matching_areas": [],
        "missing_requirements": [],
        "why_good_fit": "",
        "concerns": f"Could not parse match result. Raw: {raw[:200]}",
    }


class JobMatcher:
    """Scores job listings against a CV profile using an LLM."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def score(
        self,
        job: dict[str, Any],
        profile_text: str,
    ) -> MatchResult:
        """Score a single job listing against a CV profile summary."""
        prompt = _PROMPT.format(
            profile=profile_text,
            title=job.get("title", "Unknown"),
            institution=job_institution(job) or "Unknown",
            location=job.get("location", "Unknown"),
            pos_type=job.get("type", "unknown"),
            description=job_description(job),
        )

        try:
            raw = self.llm.generate(system=_SYSTEM, user=prompt, json_mode=True)
        except LLMQuotaError:
            raise  # propagate — caller should surface this to the user
        except RuntimeError as exc:
            return _fallback(str(exc))

        result: MatchResult = parse_json(raw) or _fallback(raw)

        # Clamp and normalise
        try:
            result["match_score"] = max(0, min(100, int(result.get("match_score", 0))))
        except (TypeError, ValueError):
            result["match_score"] = 0

        if result.get("recommendation") not in ("apply", "consider", "skip"):
            score = result.get("match_score", 0)
            result["recommendation"] = "apply" if score >= 70 else ("consider" if score >= 50 else "skip")

        return result

    def score_all(
        self,
        jobs: list[dict[str, Any]],
        profile_text: str,
    ) -> list[dict[str, Any]]:
        """Score all jobs and return them sorted by score (highest first)."""
        scored = []
        for job in jobs:
            match = self.score(job, profile_text)
            scored.append({**job, "match": match})

        scored.sort(key=lambda j: j["match"].get("match_score", 0), reverse=True)
        return scored
