"""Tests for CoverLetterWriter — mocks LLM."""

from unittest.mock import MagicMock
import pytest
from agent.cv.cover_letter import CoverLetterWriter
from agent.llm_client import LLMClient, LLMQuotaError
from agent.prompts import COVER_LETTER_DRAFT_HEADER


JOB_EN = {"title": "PhD in ML", "institution": "MIT", "location": "USA",
           "type": "phd", "description": "Machine learning research."}
JOB_IT = {"title": "Dottorato in ML", "institution": "Università di Bologna",
           "location": "Bologna, Italia", "type": "phd",
           "description": "Ricerca in machine learning e reti neurali."}
PROFILE = "Alice Rossi, NLP researcher, 2 publications at ACL."


def _make_writer(response: str | Exception) -> CoverLetterWriter:
    llm = MagicMock(spec=LLMClient)
    if isinstance(response, Exception):
        llm.generate.side_effect = response
    else:
        llm.generate.return_value = response
    return CoverLetterWriter(llm)


class TestGenerate:
    def test_draft_header_prepended(self):
        writer = _make_writer("Dear Professor,\n\nI am writing...")
        result = writer.generate(JOB_EN, PROFILE)
        assert result.startswith(COVER_LETTER_DRAFT_HEADER.strip()[:20])

    def test_letter_content_included(self):
        writer = _make_writer("Dear Professor,\n\nI am writing to apply.")
        result = writer.generate(JOB_EN, PROFILE)
        assert "Dear Professor" in result

    def test_runtime_error_returns_graceful_string(self):
        writer = _make_writer(RuntimeError("connection timeout"))
        result = writer.generate(JOB_EN, PROFILE)
        assert "GENERATION FAILED" in result
        assert "connection timeout" in result

    def test_quota_error_propagates(self):
        writer = _make_writer(LLMQuotaError("Quota exceeded"))
        with pytest.raises(LLMQuotaError):
            writer.generate(JOB_EN, PROFILE)


class TestDetectLanguage:
    def test_english_job(self):
        lang = CoverLetterWriter._detect_language(JOB_EN)
        assert lang == "English"

    def test_italian_job(self):
        lang = CoverLetterWriter._detect_language(JOB_IT)
        assert lang == "Italian"
