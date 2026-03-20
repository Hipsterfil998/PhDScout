"""Tests for config.py — checks defaults and types."""

from config import config


class TestAppConfigDefaults:
    def test_default_model(self):
        assert config.default_model == "llama-3.1-8b-instant"

    def test_max_tokens_positive(self):
        assert config.max_tokens > 0

    def test_groq_base_url(self):
        assert "groq.com" in config.groq_base_url

    def test_scraper_delay_positive(self):
        assert config.scraper_delay > 0

    def test_recent_days_positive(self):
        assert config.recent_days > 0

    def test_deadline_warn_days_positive(self):
        assert config.deadline_warn_days > 0

    def test_min_score_in_range(self):
        assert 0 <= config.min_score_default <= 100

    def test_max_results_per_source_positive(self):
        assert config.max_results_per_source > 0
