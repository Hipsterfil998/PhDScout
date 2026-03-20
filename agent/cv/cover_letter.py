"""Cover letter generator for research/PhD/postdoc applications."""

from __future__ import annotations

from typing import Any

from agent.base_service import BaseLLMService
from agent.llm_client import LLMQuotaError
from agent.prompts import (
    COVER_LETTER_SYSTEM, COVER_LETTER_PROMPT,
    COVER_LETTER_REGEN_NOTE, COVER_LETTER_DRAFT_HEADER,
)
from agent.utils import job_description, job_institution

_ITALIAN_KEYWORDS = {
    "ricerca", "lavoro", "azienda", "esperienza", "candidato", "assunzione",
    "offerta", "contratto", "sede", "università", "bando", "dottorato",
    "assegno di ricerca", "borsa", "ricercatore",
    "Milano", "Roma", "Torino", "Napoli", "Firenze", "Bologna", "Italia",
}



class CoverLetterWriter(BaseLLMService):
    """Generates DRAFT cover letters for research positions."""

    _SYSTEM = COVER_LETTER_SYSTEM

    def generate(
        self,
        job: dict[str, Any],
        profile_text: str,
        regenerate: bool = False,
    ) -> str:
        """Generate a draft cover letter prefixed with a DRAFT notice.

        LLMQuotaError propagates — it must be surfaced to the user.
        Other LLM errors return a graceful error string.
        """
        language = self._detect_language(job)
        prompt = COVER_LETTER_PROMPT.format(
            profile=profile_text,
            title=job.get("title", "Unknown Position"),
            institution=job_institution(job) or "Unknown Institution",
            location=job.get("location", "Unknown"),
            pos_type=job.get("type", "research"),
            description=job_description(job),
            language=language,
            regen_note=COVER_LETTER_REGEN_NOTE if regenerate else "",
        )

        try:
            letter = self._generate(prompt)
        except LLMQuotaError:
            raise
        except RuntimeError as exc:
            return (
                "[DRAFT — GENERATION FAILED]\n\n"
                f"Error: {exc}\n\n"
                "Please write your cover letter manually."
            )

        return COVER_LETTER_DRAFT_HEADER + letter.strip()

    @staticmethod
    def _detect_language(job: dict[str, Any]) -> str:
        text = " ".join([
            job.get("title", ""),
            job.get("description", ""),
            job.get("location", ""),
            job_institution(job),
        ]).lower()
        hits = sum(1 for kw in _ITALIAN_KEYWORDS if kw.lower() in text)
        return "Italian" if hits >= 2 else "English"
