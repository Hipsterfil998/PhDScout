"""agent.prompts — re-exports all prompt constants for backward compatibility."""

from agent.prompts.cv_parser import CV_PARSER_SYSTEM, CV_PARSER_PROMPT
from agent.prompts.job_matcher import JOB_MATCHER_SYSTEM, JOB_MATCHER_PROMPT
from agent.prompts.cv_tailor import CV_TAILOR_SYSTEM, CV_TAILOR_PROMPT
from agent.prompts.cover_letter import (
    COVER_LETTER_SYSTEM,
    COVER_LETTER_PROMPT,
    COVER_LETTER_REGEN_NOTE,
    COVER_LETTER_DRAFT_HEADER,
)

__all__ = [
    "CV_PARSER_SYSTEM",
    "CV_PARSER_PROMPT",
    "JOB_MATCHER_SYSTEM",
    "JOB_MATCHER_PROMPT",
    "CV_TAILOR_SYSTEM",
    "CV_TAILOR_PROMPT",
    "COVER_LETTER_SYSTEM",
    "COVER_LETTER_PROMPT",
    "COVER_LETTER_REGEN_NOTE",
    "COVER_LETTER_DRAFT_HEADER",
]
