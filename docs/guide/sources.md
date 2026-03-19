# Job Sources

PhdScout searches four independent job sources in every query. All sources are publicly accessible with no authentication required. The `JobSearcher` runs them sequentially (with a polite 1.5-second delay between requests) and deduplicates results by URL.

---

## Euraxess

**URL:** [euraxess.ec.europa.eu](https://euraxess.ec.europa.eu/jobs/search)
**Scraper:** `agent/scrapers/euraxess.py` — `EuraxessScraper`
**Source tag in results:** `euraxess`

### What it is

Euraxess is the official European Commission portal for research mobility and academic job postings. It is the most comprehensive source for European academic positions and covers institutions from all EU member states, Iceland, Norway, Switzerland, and several non-EU countries.

### How it works

The scraper builds a URL like:

```
https://euraxess.ec.europa.eu/jobs/search?keywords=machine+learning&job_country[]=794
```

It fetches up to 20 result cards and extracts title, institution, location, deadline, and a short description from each article element. For country-specific searches it applies an additional client-side location filter because Euraxess' `job_country[]` parameter is not reliably enforced server-side.

### Supported locations

Euraxess has internal country IDs for most European countries and several non-European ones:

| Region | Countries |
|---|---|
| Western Europe | Austria, Belgium, France, Germany, Ireland, Italy, Luxembourg, Netherlands, Portugal, Spain, Switzerland, UK |
| Nordic | Denmark, Finland, Norway, Sweden |
| Eastern Europe | Bulgaria, Croatia, Czech Republic, Estonia, Hungary, Latvia, Lithuania, Poland, Romania, Slovakia, Slovenia |
| Mediterranean | Cyprus, Greece, Malta, Serbia, Turkey |
| Non-EU | Australia, Brazil, Canada, China, India, Israel, Japan, New Zealand, Singapore, South Africa, South Korea, USA |

For `Europe (all)` or `Worldwide` searches, no country filter is applied and all results are returned.

### Limitations

- Returns at most 20 results per search page (the scraper does not paginate).
- Descriptions are short excerpts; full details require visiting the linked URL.
- The `job_country[]` filter is applied client-side; positions with ambiguous location strings may be included or excluded.

---

## mlscientist.com

**URL:** [mlscientist.com](https://mlscientist.com)
**Scraper:** `agent/scrapers/mlscientist.py` — `MLScientistScraper`
**Source tag in results:** `mlscientist`

### What it is

mlscientist.com is a curated WordPress blog aggregating ML and AI academic job postings. It is particularly strong for PhD and postdoc positions in machine learning, computer vision, NLP, and related fields. The site organises posts by categories including `phd-positions`, `postdoc-positions`, and country names.

### How it works

The scraper constructs up to two URLs — one with a country category slug (if the location maps to a known slug) and one with a position-type category slug — both with a WordPress search query:

```
https://mlscientist.com/category/germany/?s=natural+language+processing
https://mlscientist.com/category/phd-positions/?s=natural+language+processing
```

It extracts up to 15 posts per URL from `article.type-post` elements, infers location from CSS category classes, and extracts deadline dates from the excerpt text using a regex pattern.

### Supported locations

Country slugs are available for: UK, Germany, Netherlands, Denmark, France, Norway, Canada, USA, Spain.

For other locations (e.g. `Italy`, `Sweden`) the scraper falls back to the position-type category without a country filter.

### Limitations

- Only covers ML/AI fields; not suitable for biology, chemistry, or humanities searches.
- Country slug coverage is limited to about a dozen countries.
- Institution names are often missing; the `institution` field is left empty for mlscientist results.
- Does not paginate beyond the first page of results.

---

## jobs.ac.uk

**URL:** [jobs.ac.uk](https://www.jobs.ac.uk/search/)
**Scraper:** `agent/scrapers/jobs_ac_uk.py` — `JobsAcUkScraper`
**Source tag in results:** `jobs.ac.uk`

### What it is

jobs.ac.uk is the UK's primary academic job board, covering universities, research councils (UKRI, MRC, EPSRC, etc.), NHS, and other public sector research organisations. It is only included in searches when the location is UK, England, Scotland, Wales, Great Britain, Worldwide, or left blank.

### How it works

The scraper submits a keyword search with optional facets:

```
https://www.jobs.ac.uk/search/?keywords=bioinformatics&sortOrder=2&pageSize=25&jobTypeFacet[]=phds
```

Position type facets:

| Position type | Modification |
|---|---|
| `phd` | `jobTypeFacet[]=phds` parameter added |
| `postdoc` | Appends `postdoc` to the keyword query |
| `fellowship` | Appends `fellowship` to the keyword query |
| `research_staff` | Appends `researcher` to the keyword query |
| `any` | No modification |

Up to 25 results are extracted per search.

### Best use

jobs.ac.uk is the best source for UK-specific positions, especially UKRI-funded PhD studentships and postdocs at Russell Group universities. It is not included for non-UK locations to avoid noise.

### Limitations

- UK only — not useful for non-UK searches.
- Descriptions are short metadata strings (department, salary) rather than full text.
- Email addresses are not included in search results.

---

## DuckDuckGo Web Search

**URL:** Targets any academic website via DuckDuckGo
**Scraper:** `agent/scrapers/web.py` — `WebSearchScraper`
**Source tag in results:** `web`
**Dependency:** `duckduckgo-search` package

### What it is

The `WebSearchScraper` uses the `duckduckgo-search` library to run targeted queries and find job postings on institutional pages, research group websites, and smaller job boards not covered by the other scrapers. It is the most flexible source and can find positions anywhere in the world.

### How it works

Three queries are built per search, combining the field, position type, location, and current year:

```
"machine learning" PhD studentship "Germany" "call for applications" 2025
"machine learning" PhD studentship "Germany" "open position" OR "vacancy" 2025 apply
"machine learning" PhD studentship "Germany" university funded 2025 deadline
```

Up to 8 results per query are fetched. Results are filtered to:

1. Contain the current year (removes outdated postings).
2. Contain at least one "job signal" keyword such as `call for applications`, `open position`, `vacancy`, `deadline`, `apply now`, etc.

### Supported locations

Any location can be specified as a free-text string. The location is quoted and added directly to the search query. This makes `WebSearchScraper` the most flexible source for countries not covered by Euraxess or mlscientist (e.g. Singapore, South Korea, Brazil).

### Limitations

- Results may include false positives (conference calls, non-academic jobs) that pass the keyword filter.
- The `institution` field is always empty — it is inferred from the title text only.
- DuckDuckGo rate limits may occasionally return empty results; the scraper silently continues.
- Results depend on search engine indexing and may miss recently posted positions.

!!! note "duckduckgo-search package"
    If `duckduckgo-search` is not installed, `WebSearchScraper.scrape()` returns an empty list silently. This is intentional — the other three sources continue to work.

---

## Source Activation Summary

| Source | Always active | Only for UK/Worldwide |
|---|---|---|
| Euraxess | Yes | — |
| mlscientist.com | Yes | — |
| DuckDuckGo | Yes | — |
| jobs.ac.uk | — | Yes (UK, England, Scotland, Wales, Great Britain, Worldwide, blank) |

---

## Deduplication

After all scrapers run, `JobSearcher._deduplicate()` removes listings with duplicate URLs. The first occurrence (from the highest-priority source) is kept. Listings without a URL are always retained.

Results are then filtered by field relevance: the query field is split into phrases and each phrase must appear either in the job title, or have all significant words (4+ characters) present in either the title or description.

Finally, if a `--type` filter other than `any` is specified, only positions whose detected type matches (or is `other`) are retained. Results are sorted by description length (longer descriptions first, as they tend to be more complete).
