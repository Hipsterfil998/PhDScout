"""Tests for CVParser — mocks LLM, tests extraction logic and summarize()."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from agent.cv.parser import CVParser
from agent.llm_client import LLMClient


PROFILE_JSON = """{
    "name": "Alice Rossi",
    "contact": {"email": "alice@example.com", "phone": "", "linkedin": "", "github": "", "website": ""},
    "summary": "ML researcher with focus on NLP",
    "education": [{"degree": "PhD", "institution": "ETH Zurich", "field": "Computer Science",
                   "year": "2023", "thesis_topic": "Transformers for low-resource NLP"}],
    "experience": [{"title": "Research Assistant", "institution": "ETH Zurich",
                    "dates": "2019-2023", "description": "LLM research"}],
    "research_interests": ["NLP", "machine learning", "low-resource languages"],
    "publications": [{"title": "Efficient NLP", "venue": "ACL 2022", "year": "2022", "authors": "Rossi et al."}],
    "skills": {"programming": ["Python", "PyTorch"], "tools": ["HuggingFace"], "languages": ["LaTeX"], "lab_techniques": []},
    "awards": ["Best Paper ACL 2022"],
    "languages": [{"language": "English", "level": "Fluent"}, {"language": "Italian", "level": "Native"}],
    "references": []
}"""


def _make_parser(response: str) -> CVParser:
    llm = MagicMock(spec=LLMClient)
    llm.generate.return_value = response
    return CVParser(llm)


class TestSummarize:
    def _profile(self):
        import json
        return json.loads(PROFILE_JSON)

    def test_name_in_summary(self):
        parser = _make_parser("")
        text = parser.summarize(self._profile())
        assert "Alice Rossi" in text

    def test_research_interests_in_summary(self):
        parser = _make_parser("")
        text = parser.summarize(self._profile())
        assert "NLP" in text

    def test_education_in_summary(self):
        parser = _make_parser("")
        text = parser.summarize(self._profile())
        assert "ETH Zurich" in text

    def test_publication_in_summary(self):
        parser = _make_parser("")
        text = parser.summarize(self._profile())
        assert "Efficient NLP" in text

    def test_skills_in_summary(self):
        parser = _make_parser("")
        text = parser.summarize(self._profile())
        assert "Python" in text

    def test_empty_profile_no_crash(self):
        parser = _make_parser("")
        text = parser.summarize({})
        assert isinstance(text, str)


class TestExtractRawText:
    def test_txt_file(self, tmp_path):
        f = tmp_path / "cv.txt"
        f.write_text("My research CV content")
        text = CVParser.extract_raw_text(f)
        assert "My research CV content" in text

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            CVParser.extract_raw_text(tmp_path / "nonexistent.txt")

    def test_unsupported_format_raises(self, tmp_path):
        f = tmp_path / "cv.odt"
        f.write_text("content")
        with pytest.raises(ValueError, match="Unsupported"):
            CVParser.extract_raw_text(f)
