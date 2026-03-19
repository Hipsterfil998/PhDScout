# Using the CLI

PhdScout includes a full-featured command-line interface in `main.py`, built with [Click](https://click.palletsprojects.com/) and [Rich](https://rich.readthedocs.io/). It provides the same pipeline as the web UI: CV parsing, job search, scoring, interactive review, and file saving.

---

## Basic Usage

```bash
python main.py --cv cv.pdf --field "machine learning"
```

This is the minimum required invocation. It uses all defaults: location `Europe`, position type `any`, minimum score `60`, and the LLM backend from your `.env`.

---

## All Options

```
Usage: python main.py [OPTIONS]

  PhD / postdoc / fellowship job agent — powered by local LLMs (Ollama).

Options:
  --cv PATH               Path to your CV file (.pdf, .docx, or .txt).
                          [required]
  --field TEXT            Research field to search for (e.g. "machine
                          learning", "molecular biology"). [required]
  --location TEXT         Preferred location (e.g. 'Europe', 'UK',
                          'Germany'). [default: Europe]
  --type CHOICE           Filter by position type.
                          [phd|postdoc|fellowship|research_staff|other|any]
                          [default: any]
  --min-score INTEGER     Minimum match score (0-100) to include a position
                          in the review queue. [default: 60]
  --max-positions INTEGER Maximum number of positions to score and evaluate.
                          [default: 20]
  --output-dir TEXT       Directory where approved application materials are
                          saved. [default: ./output]
  --model TEXT            Override the LLM model (e.g. 'mistral:7b',
                          'llama3:8b'). Defaults to OLLAMA_MODEL in .env.
  --no-interactive        Skip the review loop — automatically save all
                          qualifying positions.
  --help                  Show this message and exit.
```

---

## Example Commands

### PhD positions in NLP, Germany

```bash
python main.py \
  --cv cv.pdf \
  --field "natural language processing" \
  --location "Germany" \
  --type phd \
  --min-score 65
```

### Postdoc search, UK, high threshold

```bash
python main.py \
  --cv cv.pdf \
  --field "computational biology" \
  --location "UK" \
  --type postdoc \
  --min-score 75 \
  --output-dir ./my_applications
```

### Fellowship search, all of Europe, batch mode (no review)

```bash
python main.py \
  --cv cv.pdf \
  --field "quantum computing" \
  --location "Europe" \
  --type fellowship \
  --no-interactive \
  --output-dir ./fellowship_batch
```

### Override model (Groq)

```bash
python main.py \
  --cv cv.pdf \
  --field "computer vision" \
  --model "llama-3.1-8b-instant"
```

### Score many positions with a lower threshold

```bash
python main.py \
  --cv cv.pdf \
  --field "molecular biology" \
  --max-positions 50 \
  --min-score 40
```

---

## Pipeline Steps

The CLI prints a step-by-step summary with Rich formatting.

### Step 1 — LLM Backend Check

Prints the current backend and model, then calls `config.validate()`. For Ollama this performs a quick health check to `localhost:11434`. For Groq and HuggingFace it checks whether the API key is set.

### Step 2 — CV Parsing

A spinner runs while the LLM parses your CV. Once complete, a formatted panel shows:

```
╭─ Parsed CV Profile ────────────────────────────────────────╮
│  Name               Jane Smith                             │
│  Email              jane@example.com                       │
│  Research interests deep learning, NLP, computer vision    │
│  Publications       8                                      │
│  Highest degree     PhD in CS (MIT) — Thesis: ...         │
│  Programming        Python, PyTorch, TensorFlow, JAX       │
╰────────────────────────────────────────────────────────────╯
```

### Step 3 — Job Search

Shows the search parameters and a table of all found positions with their source, type, and location.

### Step 4 — Scoring

A progress bar tracks scoring of each position. When complete, a sorted table shows scores with colour coding:

- Green (≥80): strong match
- Yellow (60–79): good match
- Red (<60): weak match

### Step 5 — Interactive Review

For each qualifying position (above `--min-score`), the agent:

1. Generates CV tailoring hints (spinner)
2. Generates a cover letter draft (spinner)
3. Shows a detailed position panel
4. Prompts for your decision

---

## Interactive Review Session

The review session is handled by `agent/interactive_review.py`. For each position you are presented with:

```
[1/5] PhD in Deep Learning @ TU Munich (score: 87)

┌─ Position Details ────────────────────────────────────────┐
│  Score: 87  Recommendation: apply                         │
│  Why good fit: Strong alignment in deep learning and CV   │
│  Concerns: None                                           │
└───────────────────────────────────────────────────────────┘

┌─ CV Tailoring Hints ──────────────────────────────────────┐
│  Skills to highlight: PyTorch, medical imaging            │
│  Keywords to add: contrastive learning, ViT               │
└───────────────────────────────────────────────────────────┘

--- COVER LETTER DRAFT ---
[letter text...]

Options:
  [a] Approve and save
  [e] Edit cover letter
  [r] Regenerate cover letter
  [s] Skip this position
  [q] Quit review
```

Enter one character and press Enter:

| Key | Action |
|---|---|
| `a` | Approve the current letter and save to disk |
| `e` | Open the cover letter in your `$EDITOR` for manual editing |
| `r` | Regenerate the cover letter (new LLM call) |
| `s` | Skip this position (not saved) |
| `q` | Quit the review loop early |

### Batch mode (`--no-interactive`)

With `--no-interactive`, all qualifying positions are automatically saved without prompting. Useful for initial exploration or when processing many positions overnight:

```bash
python main.py --cv cv.pdf --field "robotics" --no-interactive --min-score 55
```

---

## Output Structure

Saved applications go to `--output-dir` (default `./output`):

```
output/
├── summary.json                      ← full session summary
└── applications/
    ├── TU_Munich_PhD_Deep_Learning/
    │   ├── cover_letter_draft.txt
    │   ├── tailoring_hints.txt
    │   └── position_details.json
    └── ETH_Zurich_Postdoc_NLP/
        ├── cover_letter_draft.txt
        ├── tailoring_hints.txt
        └── position_details.json
```

`summary.json` contains the full session metadata including search parameters, totals (positions found, scored, qualifying, approved, skipped), and a record for every reviewed position.

`tailoring_hints.txt` is a formatted plain-text version of the LLM's tailoring hints:

```
CV TAILORING HINTS
==================

PROFILE SUMMARY TWEAK:
  Emphasise your experience with transformer architectures...

RESEARCH ALIGNMENT:
  Frame your work on medical image segmentation as directly relevant...

SKILLS TO EMPHASISE:
  - PyTorch (used extensively in the group's code)
  - Docker (mentioned in job description)

KEYWORDS TO ADD:
  contrastive learning, vision transformer, self-supervised
```

---

## Tips

!!! tip "Start with `--no-interactive` to explore"
    Run with `--no-interactive` and a low `--min-score` to get a feel for what is available before doing a proper interactive review session.

!!! tip "Pipe output to a file"
    The Rich-formatted output renders beautifully in a terminal, but you can also redirect to a file:
    ```bash
    python main.py --cv cv.pdf --field "NLP" 2>&1 | tee search_log.txt
    ```

!!! tip "Run multiple fields"
    You can run separate searches for different fields and consolidate:
    ```bash
    python main.py --cv cv.pdf --field "NLP" --output-dir ./output/nlp
    python main.py --cv cv.pdf --field "computer vision" --output-dir ./output/cv
    ```
