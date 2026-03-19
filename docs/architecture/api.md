# Agent API Reference

This page documents the public API of PhdScout. The primary entry point is `JobAgent` in `agent/pipeline.py`, exported from `agent/__init__.py` alongside `LLMQuotaError`.

```python
from agent import JobAgent, LLMQuotaError
```

---

## JobAgent

`agent/pipeline.py`

Orchestrates the full research job application pipeline. Each instance holds its own `LLMClient` and is safe to instantiate per-request (e.g. once per Gradio button click).

### Constructor

```python
JobAgent(
    model: str,
    backend: str = "groq",
    api_key: str = "",
)
```

| Parameter | Type | Description |
|---|---|---|
| `model` | `str` | Model ID for the selected backend. E.g. `"llama-3.3-70b-versatile"` for Groq, `"llama3.1:8b"` for Ollama, `"mistralai/Mistral-7B-Instruct-v0.3"` for HuggingFace. |
| `backend` | `str` | LLM backend: `"groq"`, `"huggingface"`, or `"ollama"`. Default: `"groq"`. |
| `api_key` | `str` | API key for the backend. Not required for Ollama. |

### Methods

#### `parse_cv`

```python
def parse_cv(self, cv_path: str) -> tuple[CVProfile, str]
```

Parse a CV file and return the structured profile plus a compact text summary.

| Parameter | Type | Description |
|---|---|---|
| `cv_path` | `str` | Path to a `.pdf`, `.docx`, or `.txt` file. |

**Returns:** `(profile, profile_text)` where `profile` is a `CVProfile` dict and `profile_text` is a compact string suitable for use in LLM prompts.

**Raises:**
- `FileNotFoundError` if `cv_path` does not exist.
- `ValueError` if the file format is not supported or no text could be extracted.
- `RuntimeError` if the LLM call fails.
- `LLMQuotaError` if the HuggingFace quota is exhausted.

---

#### `search_jobs`

```python
def search_jobs(
    self,
    field: str,
    location: str = "Europe",
    position_type: str = "phd",
) -> list[dict]
```

Search all configured job boards and return deduplicated, field-filtered listings.

| Parameter | Type | Description |
|---|---|---|
| `field` | `str` | Research field, e.g. `"machine learning"`. Comma-separated values work: `"NLP, natural language processing"`. |
| `location` | `str` | Location string, e.g. `"Germany"`, `"Europe"`, `"UK"`. Default: `"Europe"`. |
| `position_type` | `str` | One of `"phd"`, `"postdoc"`, `"fellowship"`, `"research_staff"`, `"predoctoral"`. Default: `"phd"`. |

**Returns:** List of `JobListing` dicts, each with keys: `title`, `institution`, `location`, `url`, `description`, `deadline`, `email`, `source`, `type`.

**Raises:** Does not raise — scraper errors are silently absorbed. Returns an empty list if all sources fail.

---

#### `score_jobs`

```python
def score_jobs(
    self,
    jobs: list[dict],
    profile_text: str,
) -> list[dict]
```

Score all jobs against the CV profile and return them sorted by score (highest first).

| Parameter | Type | Description |
|---|---|---|
| `jobs` | `list[dict]` | List of job listings from `search_jobs`. |
| `profile_text` | `str` | Compact profile text from `parse_cv`. |

**Returns:** Same list as input, each job extended with a `"match"` key containing a `MatchResult` dict:

```python
{
    "match_score": 87,                     # int 0–100
    "recommendation": "apply",             # "apply" | "consider" | "skip"
    "matching_areas": ["deep learning", "PyTorch"],
    "missing_requirements": [],
    "why_good_fit": "Strong alignment in...",
    "concerns": "",
}
```

**Raises:** `LLMQuotaError` if the HuggingFace quota is exhausted. Individual scoring failures return a fallback score of 0.

---

#### `prepare_application`

```python
def prepare_application(
    self,
    job: dict,
    profile_text: str,
) -> tuple[TailoringHints, str]
```

Generate CV tailoring hints and a draft cover letter for a single position.

| Parameter | Type | Description |
|---|---|---|
| `job` | `dict` | A job listing dict (from `search_jobs` or `score_jobs`). |
| `profile_text` | `str` | Compact profile text from `parse_cv`. |

**Returns:** `(hints, cover_letter)` where:
- `hints` is a `TailoringHints` dict with keys: `headline_suggestion`, `skills_to_highlight`, `experience_to_emphasize`, `research_alignment`, `keywords_to_add`, `suggested_order`.
- `cover_letter` is a string beginning with `DRAFT` header followed by 400–600 word letter text.

**Raises:** `LLMQuotaError` propagates. Cover letter generation falls back to an error string on other failures.

---

#### `regenerate_letter`

```python
def regenerate_letter(
    self,
    job: dict,
    profile_text: str,
) -> str
```

Generate an alternative cover letter draft, varying the opening, highlighted projects, and framing.

| Parameter | Type | Description |
|---|---|---|
| `job` | `dict` | Job listing dict. |
| `profile_text` | `str` | Compact profile text. |

**Returns:** Cover letter string (with `DRAFT` header).

**Raises:** Same as `prepare_application`.

---

## LLMQuotaError

`agent/llm_client.py`

```python
class LLMQuotaError(RuntimeError):
    """Raised when the HuggingFace free-tier quota is exhausted (HTTP 402)."""
```

Raised when the HuggingFace Serverless Inference API returns HTTP 402. It is a subclass of `RuntimeError`.

`LLMQuotaError` is **always re-raised** — it propagates through `BaseLLMService._generate_json()` and all service methods. The UI and CLI catch it at the top level and display a user-facing message.

```python
try:
    scored = agent.score_jobs(jobs, profile_text)
except LLMQuotaError:
    print("HuggingFace quota exhausted. Switch to GROQ backend.")
```

---

## LLMClient

`agent/llm_client.py`

Low-level unified LLM client. You do not normally need to use this directly — `JobAgent` creates and manages it internally.

### Constructor

```python
LLMClient(
    model: str | None = None,
    backend: str | None = None,
    token: str | None = None,
)
```

| Parameter | Type | Description |
|---|---|---|
| `model` | `str \| None` | Model ID. Falls back to `config.ollama_model` or `config.hf_model`. |
| `backend` | `str \| None` | Backend name. Falls back to `config.llm_backend`. |
| `token` | `str \| None` | API key override. Falls back to `config.groq_api_key` / `config.hf_api_key`. |

### Methods

#### `generate`

```python
def generate(
    self,
    system: str,
    user: str,
    json_mode: bool = False,
) -> str
```

Generate a complete (non-streaming) response.

| Parameter | Type | Description |
|---|---|---|
| `system` | `str` | System/instruction prompt. |
| `user` | `str` | User message. |
| `json_mode` | `bool` | If `True`, prepends "Respond only with valid JSON." to the system prompt, and for Ollama/Groq sets `response_format={"type": "json_object"}`. |

**Returns:** Model response as a plain string.

**Raises:** `RuntimeError` on backend failures. `LLMQuotaError` for HuggingFace 402.

---

#### `stream_generate`

```python
def stream_generate(
    self,
    system: str,
    user: str,
) -> Iterator[str]
```

Stream response tokens one by one. Yields individual text chunks as they arrive from the backend.

---

## BaseLLMService

`agent/base_service.py`

Abstract base class for all LLM-backed agent services. Subclasses declare `_SYSTEM` as a class variable and call `_generate()` or `_generate_json()`.

### Class Variable

```python
_SYSTEM: str = ""  # Override in subclasses
```

### Constructor

```python
BaseLLMService(llm: LLMClient)
```

### Protected Methods

#### `_generate`

```python
def _generate(self, prompt: str, json_mode: bool = False) -> str
```

Raw LLM call using `self._SYSTEM` as the system prompt. All exceptions propagate unchecked.

#### `_generate_json`

```python
def _generate_json(self, prompt: str) -> dict | None
```

LLM call expecting a JSON response. Returns `None` if the call fails or JSON is malformed. **Re-raises `LLMQuotaError`** — never absorbs it.

---

## BaseScraper

`agent/scrapers/base.py`

Abstract base class for all scrapers. Subclasses implement `scrape()` and declare `name`.

### Class Variable

```python
name: ClassVar[str] = ""  # Source identifier, e.g. "euraxess"
```

### Abstract Method

```python
@abstractmethod
def scrape(
    self,
    field: str,
    location: str,
    position_type: str,
) -> list[dict]
```

Return a list of job listing dicts for the given search parameters.

### Protected Helpers

#### `_fetch`

```python
def _fetch(self, url: str, timeout: int = 15) -> BeautifulSoup | None
```

GET `url` with a browser User-Agent header. Returns a parsed `BeautifulSoup` or `None` on any error (network failure, non-200 status).

#### `_sleep`

```python
def _sleep(self) -> None
```

Polite delay of 1.5 seconds between requests.

#### `_detect_type`

```python
@staticmethod
def _detect_type(title: str, description: str) -> str
```

Infer position type from title and description using a keyword dictionary. Returns one of: `"predoctoral"`, `"phd"`, `"postdoc"`, `"fellowship"`, `"research_staff"`, `"other"`.

Type detection keywords (case-insensitive):

| Type | Sample keywords |
|---|---|
| `predoctoral` | predoctoral, early-stage researcher, master's student, ESR |
| `phd` | phd, doctoral, doctorate, studentship, graduate student |
| `postdoc` | postdoc, postdoctoral, research associate, research fellow |
| `fellowship` | fellowship, Marie Curie, ERC, scholarship, stipend |
| `research_staff` | researcher, research scientist, lecturer, professor, faculty |

#### `_extract_email`

```python
@staticmethod
def _extract_email(text: str) -> str | None
```

Extract the first email address found in `text`, or `None`.

---

## Utility Functions

`agent/utils.py`

### `parse_json`

```python
def parse_json(text: str) -> dict | None
```

Parse a JSON object from an LLM response string. Handles common issues: strips markdown fences (` ```json ... ``` `), finds the first `{` character, and calls `json.loads`. Returns `None` on parse failure.

### `job_institution`

```python
def job_institution(job: dict) -> str
```

Return the institution name from a job dict, checking both `"institution"` and `"company"` keys. Returns an empty string if neither is set.

### `job_description`

```python
def job_description(job: dict) -> str
```

Return a truncated description for use in prompts. Truncates at 1500 characters and appends `"[truncated]"` if necessary.

---

## Usage Examples

### Minimal pipeline

```python
from agent import JobAgent, LLMQuotaError

agent = JobAgent("llama-3.3-70b-versatile", backend="groq", api_key="gsk_...")

profile, profile_text = agent.parse_cv("cv.pdf")
jobs = agent.search_jobs("machine learning", "Germany", "phd")
scored = agent.score_jobs(jobs, profile_text)

top = scored[0]
hints, letter = agent.prepare_application(top, profile_text)
print(letter[:200])
```

### Filtering results manually

```python
scored = agent.score_jobs(jobs, profile_text)

# Only positions with score >= 70 and recommendation "apply"
strong = [
    j for j in scored
    if j["match"]["match_score"] >= 70
    and j["match"]["recommendation"] == "apply"
]
```

### Using LLMClient directly

```python
from agent.llm_client import LLMClient

llm = LLMClient(model="llama-3.3-70b-versatile", backend="groq", token="gsk_...")
response = llm.generate(
    system="You are a helpful assistant.",
    user="Summarise the key requirements for a postdoc in NLP.",
)
print(response)

# Streaming
for token in llm.stream_generate(system="You are helpful.", user="What is BERT?"):
    print(token, end="", flush=True)
```

### Custom scraper integration

```python
from agent.scrapers.base import BaseScraper

class MyCustomScraper(BaseScraper):
    name = "my_source"

    def scrape(self, field, location, position_type):
        soup = self._fetch(f"https://example.com/jobs?q={field}")
        if soup is None:
            return []
        # ... parse and return list of dicts
        return []
```

See [Adding a Scraper](scrapers.md) for the full guide.
