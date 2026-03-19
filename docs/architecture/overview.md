# Architecture Overview

PhdScout is structured as a layered agent system. The interface layer (Gradio UI or Click CLI) calls the `JobAgent` orchestrator, which delegates to specialised services. All LLM-backed services share a common base class, and all scrapers share a different base class with shared HTTP utilities.

---

## System Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Interface Layer                              │
│                                                                      │
│   app.py (Gradio)                        main.py (Click CLI)        │
│   Tab-based web UI                       Rich terminal output        │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  imports
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         agent/pipeline.py                            │
│                                                                      │
│                          JobAgent                                    │
│   parse_cv()  search_jobs()  score_jobs()  prepare_application()    │
│   regenerate_letter()                                                │
└──────────┬───────────────────┬──────────────────────────────────────┘
           │                   │
    ┌──────┴──────┐     ┌──────┴───────────────────────────────┐
    │             │     │          LLM-backed Services          │
    │ JobSearcher │     │                                       │
    │             │     │  CVParser   JobMatcher  CVTailor      │
    └──────┬──────┘     │  CoverLetterWriter                   │
           │            └──────────┬────────────────────────────┘
    ┌──────┴──────────────┐        │ inherits from
    │      Scrapers       │  ┌─────┴──────────────┐
    │                     │  │  BaseLLMService     │
    │  EuraxessScraper    │  │  _generate()        │
    │  MLScientistScraper │  │  _generate_json()   │
    │  JobsAcUkScraper    │  └─────────┬───────────┘
    │  WebSearchScraper   │            │ uses
    └──────┬──────────────┘     ┌──────┴──────┐
           │ inherits from      │  LLMClient  │
    ┌──────┴──────────┐         │             │
    │   BaseScraper   │         │  Groq        │
    │  _fetch()       │         │  HuggingFace │
    │  _sleep()       │         │  Ollama      │
    │  _detect_type() │         └─────────────┘
    │  _extract_email │
    └─────────────────┘
```

---

## Module Responsibilities

| Module | Class | Responsibility |
|---|---|---|
| `agent/__init__.py` | — | Public API exports: `JobAgent`, `LLMQuotaError` |
| `agent/pipeline.py` | `JobAgent` | Orchestrates the full pipeline; one instance per session |
| `agent/llm_client.py` | `LLMClient`, `LLMQuotaError` | Unified LLM interface for Groq, HuggingFace, Ollama |
| `agent/base_service.py` | `BaseLLMService` | Base for all LLM services; error policy |
| `agent/cv_parser.py` | `CVParser` | PDF/DOCX/TXT extraction + LLM-based structured parsing |
| `agent/searcher.py` | `JobSearcher` | Orchestrates scrapers; deduplication; field/type filtering |
| `agent/job_matcher.py` | `JobMatcher` | Semantic match scoring (0–100) + recommendation |
| `agent/cv_tailor.py` | `CVTailor`, `format_hints_text` | Per-position CV tailoring hints |
| `agent/cover_letter.py` | `CoverLetterWriter` | Draft cover letter generation (EN/IT) |
| `agent/interactive_review.py` | `ReviewSession` | CLI interactive review loop |
| `agent/utils.py` | — | `parse_json`, `job_institution`, `job_description` helpers |
| `agent/scrapers/base.py` | `BaseScraper` | Abstract scraper with shared HTTP and detection utilities |
| `agent/scrapers/euraxess.py` | `EuraxessScraper` | Euraxess EU portal |
| `agent/scrapers/mlscientist.py` | `MLScientistScraper` | mlscientist.com WordPress blog |
| `agent/scrapers/jobs_ac_uk.py` | `JobsAcUkScraper` | jobs.ac.uk UK academic board |
| `agent/scrapers/web.py` | `WebSearchScraper` | Available but not active by default |
| `config.py` | `AppConfig`, `EmailConfig` | Singleton config from `.env` |
| `app.py` | — | Gradio Blocks UI; event handlers |
| `main.py` | — | Click CLI entry point; Rich display helpers |

---

## Data Flow

### 1. CV Parsing

```
cv.pdf ──► CVParser.extract_raw_text()
              │
              ▼ (up to 8000 chars)
          LLM (json_mode=True)
              │
              ▼
          CVProfile dict
          {name, education, research_interests,
           publications, skills, awards, ...}
              │
          CVParser.summarize()
              │
              ▼
          profile_text (compact string for prompts)
```

### 2. Job Search

```
(field, location, position_type)
              │
    JobSearcher.search()
              │
    ┌─────────┼──────────────┐
    │         │              │
EuraxessScraper  MLScientist
    │         │              │
    └─────────┼──────────────┘
              │
    _deduplicate() by URL
              │
    _field_matches() filter
              │
    type filter
              │
    sort by description length
              │
          list[JobListing]
```

### 3. Scoring

```
for job in jobs:
    JobMatcher.score(job, profile_text)
         │
    LLM (json_mode=True)
         │
    MatchResult {
      match_score: int,
      recommendation: "apply"|"consider"|"skip",
      matching_areas: list[str],
      missing_requirements: list[str],
      why_good_fit: str,
      concerns: str
    }
         │
sort by match_score descending
```

### 4. Application Preparation

```
job + profile_text
    │
    ├──► CVTailor.generate()
    │        │
    │    LLM (json_mode=True)
    │        │
    │    TailoringHints dict
    │
    └──► CoverLetterWriter.generate()
             │
         language detection (EN/IT)
             │
         LLM (prose mode)
             │
         DRAFT header + letter text
```

---

## Class Hierarchy

```
object
├── BaseLLMService
│   ├── CVParser
│   ├── JobMatcher
│   ├── CVTailor
│   └── CoverLetterWriter
│
├── BaseScraper (ABC)
│   ├── EuraxessScraper
│   ├── MLScientistScraper
│   ├── JobsAcUkScraper
│   └── WebSearchScraper
│
└── LLMClient
```

`JobAgent` and `JobSearcher` are standalone classes (not in the hierarchy above).

---

## Error Handling Strategy

PhdScout distinguishes between two categories of error:

### LLMQuotaError (user-facing)

`LLMQuotaError` is raised by `LLMClient._generate_hf()` when the HuggingFace API returns HTTP 402. It **always propagates** up the call stack:

```
LLMClient._generate_hf()
    raises LLMQuotaError
        │
BaseLLMService._generate_json()
    re-raises LLMQuotaError   ◄─── does NOT absorb it
        │
JobMatcher.score()
    propagates
        │
JobAgent.score_jobs()
    propagates
        │
app.py run_search()
    catches and shows error in UI
```

The Gradio UI and CLI both catch `LLMQuotaError` at the top level and display a meaningful message to the user.

### RuntimeError (absorbed in JSON mode)

`BaseLLMService._generate_json()` absorbs all `RuntimeError` exceptions other than `LLMQuotaError`:

```python
def _generate_json(self, prompt: str) -> dict | None:
    try:
        raw = self.llm.generate(..., json_mode=True)
    except LLMQuotaError:
        raise           # always propagates
    except RuntimeError:
        return None     # absorbed — caller uses fallback
    return parse_json(raw)
```

Callers that use `_generate_json()` (`JobMatcher`, `CVTailor`) check for `None` and substitute a fallback result:

- `JobMatcher` returns `_fallback("LLM call or JSON parse failed")` — a score of 0 with recommendation `skip`.
- `CVTailor` returns `_fallback("LLM call or JSON parse failed")` — empty hints with default section order.

### Prose mode (_generate)

`BaseLLMService._generate()` does **not** absorb errors — all exceptions propagate. `CoverLetterWriter` catches `RuntimeError` (but not `LLMQuotaError`) and returns a graceful error string instead of a letter.

### Scraper failures

Each scraper is wrapped in a `try/except Exception: pass` block in `JobSearcher.search()`. If a scraper raises any exception (network error, parse error, etc.), it is silently skipped and the remaining scrapers continue.

---

## TypedDict Contracts

Key data structures use `TypedDict` for documentation and static analysis:

```python
class CVProfile(TypedDict, total=False):
    name: str
    contact: dict          # email, phone, linkedin, github, website
    summary: str
    education: list[dict]  # degree, institution, field, year, thesis_topic
    research_interests: list[str]
    publications: list[dict]
    skills: dict           # programming, tools, languages, lab_techniques
    awards: list[str]
    languages: list[dict]
    references: list[dict]

class MatchResult(TypedDict, total=False):
    match_score: int       # 0–100
    recommendation: str    # "apply" | "consider" | "skip"
    matching_areas: list[str]
    missing_requirements: list[str]
    why_good_fit: str
    concerns: str

class TailoringHints(TypedDict, total=False):
    headline_suggestion: str
    skills_to_highlight: list[str]
    experience_to_emphasize: list[str]
    research_alignment: str
    keywords_to_add: list[str]
    suggested_order: list[str]

class JobListing(TypedDict, total=False):
    title: str
    institution: str
    location: str
    url: str
    description: str
    deadline: str | None
    email: str | None
    source: str
    type: str
```

All `total=False` means every field is optional — callers should use `.get()` with defaults.
