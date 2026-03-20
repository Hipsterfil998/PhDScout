"""Job board scrapers — public surface of the scrapers sub-package."""

from agent.search.scrapers.euraxess import EuraxessScraper
from agent.search.scrapers.jobs_ac_uk import JobsAcUkScraper
from agent.search.scrapers.mlscientist import MLScientistScraper
from agent.search.scrapers.nature_careers import NatureCareersScraper
from agent.search.scrapers.scholarshipdb import ScholarshipDbScraper

__all__ = [
    "EuraxessScraper",
    "JobsAcUkScraper",
    "MLScientistScraper",
    "NatureCareersScraper",
    "ScholarshipDbScraper",
]
