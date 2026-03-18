"""CV tailoring hints: actionable, position-specific suggestions (not a rewrite)."""

from __future__ import annotations

from typing import Any, TypedDict

from agent.llm_client import LLMClient
from agent.utils import parse_json, job_institution, job_description


class TailoringHints(TypedDict, total=False):
    headline_suggestion: str
    skills_to_highlight: list[str]
    experience_to_emphasize: list[str]
    research_alignment: str
    keywords_to_add: list[str]
    suggested_order: list[str]


_SYSTEM = (
    "You are an expert academic career advisor helping a researcher tailor their CV "
    "for a specific PhD / postdoc / fellowship application. "
    "Give concrete, actionable hints — do NOT rewrite the CV. "
    "Respond only with valid JSON."
)

_PROMPT = """The researcher is applying for the following position:

POSITION:
Title: {title}
Institution: {institution}
Type: {pos_type}
Description:
{description}

CANDIDATE CV PROFILE:
{profile}

Produce a JSON object with EXACTLY these keys:
{{
  "headline_suggestion": "One sentence suggestion for tweaking the profile summary",
  "skills_to_highlight": ["skill (why relevant)"],
  "experience_to_emphasize": ["Experience entry — which aspect to highlight"],
  "research_alignment": "2-3 sentences on how to frame research interests for this group",
  "keywords_to_add": ["keyword from JD not in CV"],
  "suggested_order": ["Research Interests", "Publications", "Education", "Experience", "Skills"]
}}

Rules: be specific, reference actual CV entries, do NOT suggest fabricating anything."""


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
        lines += ["SUGGESTED SECTION ORDER:"] + [f"  {i}. {s}" for i, s in enumerate(hints["suggested_order"], 1)]
    return "\n".join(lines)


class CVTailor:
    """Generates per-position CV tailoring hints using an LLM."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate(
        self,
        job: dict[str, Any],
        profile_text: str,
    ) -> TailoringHints:
        """Generate actionable tailoring hints for a specific position."""
        prompt = _PROMPT.format(
            title=job.get("title", "Unknown"),
            institution=job_institution(job) or "Unknown",
            pos_type=job.get("type", "unknown"),
            description=job_description(job),
            profile=profile_text,
        )

        try:
            raw = self.llm.generate(system=_SYSTEM, user=prompt, json_mode=True)
        except RuntimeError as exc:
            return _fallback(str(exc))

        hints: TailoringHints = parse_json(raw) or _fallback("JSON parse error")

        hints.setdefault("headline_suggestion", "")
        hints.setdefault("skills_to_highlight", [])
        hints.setdefault("experience_to_emphasize", [])
        hints.setdefault("research_alignment", "")
        hints.setdefault("keywords_to_add", [])
        hints.setdefault("suggested_order", _FALLBACK_ORDER)

        return hints
