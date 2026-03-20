"""CV tailoring hints — actionable, position-specific suggestions."""

from __future__ import annotations

from typing import Any, TypedDict

from agent.base_service import BaseLLMService
from agent.prompts import CV_TAILOR_SYSTEM, CV_TAILOR_PROMPT
from agent.utils import job_description, job_institution


class TailoringHints(TypedDict, total=False):
    headline_suggestion: str
    skills_to_highlight: list[str]
    experience_to_emphasize: list[str]
    research_alignment: str
    keywords_to_add: list[str]
    suggested_order: list[str]



_FALLBACK_ORDER = ["Education", "Research Interests", "Publications", "Experience", "Skills", "Awards"]


def _fallback(reason: str) -> TailoringHints:
    return {
        "headline_suggestion": f"Could not generate hints: {reason}",
        "skills_to_highlight": [],
        "experience_to_emphasize": [],
        "research_alignment": "",
        "keywords_to_add": [],
        "suggested_order": _FALLBACK_ORDER,
    }


def format_hints_text(hints: TailoringHints) -> str:
    """Render TailoringHints as plain text (used when saving to disk)."""
    lines = ["CV TAILORING HINTS", "==================", ""]
    if hints.get("headline_suggestion"):
        lines += ["PROFILE SUMMARY TWEAK:", f"  {hints['headline_suggestion']}", ""]
    if hints.get("research_alignment"):
        lines += ["RESEARCH ALIGNMENT:", f"  {hints['research_alignment']}", ""]
    if hints.get("skills_to_highlight"):
        lines += ["SKILLS TO EMPHASISE:"] + [f"  - {s}" for s in hints["skills_to_highlight"]] + [""]
    if hints.get("experience_to_emphasize"):
        lines += ["EXPERIENCE TO HIGHLIGHT:"] + [f"  - {e}" for e in hints["experience_to_emphasize"]] + [""]
    if hints.get("keywords_to_add"):
        lines += ["KEYWORDS TO ADD:", "  " + ", ".join(hints["keywords_to_add"]), ""]
    if hints.get("suggested_order"):
        lines += ["SUGGESTED SECTION ORDER:"] + [
            f"  {i}. {s}" for i, s in enumerate(hints["suggested_order"], 1)
        ]
    return "\n".join(lines)


class CVTailor(BaseLLMService):
    """Generates per-position CV tailoring hints using an LLM."""

    _SYSTEM = CV_TAILOR_SYSTEM

    def generate(self, job: dict[str, Any], profile_text: str) -> TailoringHints:
        """Generate actionable tailoring hints for a specific position."""
        prompt = CV_TAILOR_PROMPT.format(
            title=job.get("title", "Unknown"),
            institution=job_institution(job) or "Unknown",
            pos_type=job.get("type", "unknown"),
            description=job_description(job),
            profile=profile_text,
        )

        result = self._generate_json(prompt)
        hints: TailoringHints = result if result is not None else _fallback("LLM call or JSON parse failed")

        hints.setdefault("headline_suggestion", "")
        hints.setdefault("skills_to_highlight", [])
        hints.setdefault("experience_to_emphasize", [])
        hints.setdefault("research_alignment", "")
        hints.setdefault("keywords_to_add", [])
        hints.setdefault("suggested_order", _FALLBACK_ORDER)

        return hints
