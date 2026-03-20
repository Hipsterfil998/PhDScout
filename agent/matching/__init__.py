"""agent.matching — job matching against CV profiles."""

from agent.matching.matcher import JobMatcher, MatchResult, _fallback, _phd_status

__all__ = [
    "JobMatcher",
    "MatchResult",
    "_fallback",
    "_phd_status",
]
