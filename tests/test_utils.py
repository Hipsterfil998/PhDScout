"""Tests for agent/utils.py — pure functions, no LLM needed."""

import pytest
from agent.utils import strip_fences, parse_json, job_institution, job_description


class TestStripFences:
    def test_no_fence(self):
        assert strip_fences('{"a": 1}') == '{"a": 1}'

    def test_json_fence(self):
        assert strip_fences('```json\n{"a": 1}\n```') == '{"a": 1}'

    def test_plain_fence(self):
        assert strip_fences('```\n{"a": 1}\n```') == '{"a": 1}'

    def test_leading_trailing_whitespace(self):
        assert strip_fences('  ```json\n{"a": 1}\n```  ') == '{"a": 1}'


class TestParseJson:
    def test_valid_json(self):
        assert parse_json('{"score": 80}') == {"score": 80}

    def test_json_inside_fence(self):
        assert parse_json('```json\n{"score": 80}\n```') == {"score": 80}

    def test_json_embedded_in_text(self):
        raw = 'Here is the result: {"score": 75} done.'
        assert parse_json(raw) == {"score": 75}

    def test_invalid_json_returns_none(self):
        assert parse_json("not json at all") is None

    def test_empty_string_returns_none(self):
        assert parse_json("") is None

    def test_nested_json(self):
        raw = '{"match_score": 85, "areas": ["ML", "NLP"]}'
        result = parse_json(raw)
        assert result["match_score"] == 85
        assert result["areas"] == ["ML", "NLP"]


class TestJobInstitution:
    def test_institution_field(self):
        assert job_institution({"institution": "MIT"}) == "MIT"

    def test_missing_returns_empty(self):
        assert job_institution({}) == ""

    def test_none_returns_empty(self):
        assert job_institution({"institution": None}) == ""


class TestJobDescription:
    def test_returns_description(self):
        job = {"description": "PhD in ML"}
        assert job_description(job) == "PhD in ML"

    def test_missing_returns_placeholder(self):
        assert job_description({}) == "No description provided."

    def test_truncation(self):
        job = {"description": "x" * 5000}
        result = job_description(job, max_chars=100)
        assert len(result) == 100
