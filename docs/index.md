# PhdScout

**AI-powered academic job search — find PhD positions, postdocs, and fellowships that match your CV.**

[Try the live demo on HuggingFace Spaces](https://huggingface.co/spaces/HipFil98/PhDScout){ .md-button .md-button--primary }
[View on GitHub](https://github.com/Hipsterfil998/PhDScout){ .md-button }

---

## What is PhdScout?

PhdScout is an open-source Python agent that automates the most tedious parts of an academic job search. You upload your CV, specify a research field and location, and the agent:

1. **Parses your CV** using an LLM to extract your education, publications, research interests, and skills into a structured profile.
2. **Searches four free job sources** simultaneously — Euraxess, mlscientist.com, and jobs.ac.uk — and deduplicates the results.
3. **Scores every position** from 0–100 against your profile using semantic reasoning, not just keyword matching. A position about "deep learning" will match a candidate whose CV says "neural networks".
4. **Generates a tailored cover letter draft** and **CV tailoring hints** for each qualifying position.
5. **Exports approved applications** as a ZIP archive containing the cover letter, tailoring hints, and full position details.

PhdScout runs entirely on **free infrastructure**: the Groq API (free tier, no credit card required) powers the LLM calls, and all job sources are scraped from public pages.

---

## Features at a Glance

| Feature | Details |
|---|---|
| CV formats supported | PDF, DOCX, TXT |
| Job sources | Euraxess, mlscientist.com, jobs.ac.uk |
| Position types | PhD, postdoc, fellowship, research staff, predoctoral |
| Match scoring | 0–100 semantic score with recommendation and reasoning |
| Cover letters | 400–600 word academic drafts, English or Italian |
| CV tailoring | Per-position hints: skills to highlight, keywords, section order |
| LLM backends | Groq (recommended), HuggingFace Serverless, Ollama (local) |
| Interfaces | Gradio web UI + Click CLI |
| Export | ZIP with cover letter, hints, position JSON, summary |

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│                  Interfaces                  │
│         Gradio Web UI  |  Click CLI          │
└────────────────────┬────────────────────────┘
                     │
              ┌──────▼──────┐
              │  JobAgent   │   agent/pipeline.py
              │ orchestrator│
              └──────┬──────┘
       ┌─────────────┼────────────────┐
       │             │                │
  ┌────▼────┐  ┌─────▼─────┐  ┌──────▼──────┐
  │CVParser │  │JobSearcher│  │ JobMatcher  │
  │         │  │           │  │ CVTailor    │
  └────┬────┘  └─────┬─────┘  │ CoverLetter │
       │             │        └──────┬──────┘
       │    ┌────────┼────────┐      │
       │    │        │        │      │
       │  Euraxess  ML  jobs.ac  DuckDDG
       │  Scraper Scientist  uk    Web
       │                           │
       └───────────────────────────┘
                    │
              ┌─────▼─────┐
              │ LLMClient │   Groq / HuggingFace / Ollama
              └───────────┘
```

All LLM-backed services inherit from `BaseLLMService`. All scrapers inherit from `BaseScraper`. The `JobAgent` class in `agent/pipeline.py` is the single public entry point for programmatic use.

---

## Quick Start

=== "Web UI"

    The fastest way to get started is the hosted demo — no installation needed:

    [Open PhdScout on HuggingFace Spaces](https://huggingface.co/spaces/HipFil98/PhDScout){ .md-button .md-button--primary }

=== "Local install (Groq)"

    ```bash
    git clone https://github.com/Hipsterfil998/PhDScout.git
    cd PhDScout
    pip install -r requirements.txt
    echo "LLM_BACKEND=groq" >> .env
    echo "GROQ_API_KEY=gsk_..." >> .env
    python app.py          # web UI at http://localhost:7860
    ```

=== "CLI"

    ```bash
    python main.py \
      --cv cv.pdf \
      --field "machine learning" \
      --location "Germany" \
      --type phd \
      --min-score 65
    ```

---

## Getting Started

- [Installation guide](getting-started/installation.md) — prerequisites, backends, and `.env` setup
- [Quick Start](getting-started/quickstart.md) — web UI walkthrough and Python API example

## License

PhdScout is released under the [MIT License](https://github.com/Hipsterfil998/PhDScout/blob/main/LICENSE).
