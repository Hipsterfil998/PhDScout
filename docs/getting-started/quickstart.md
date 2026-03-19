# Quick Start

There are two ways to use PhdScout: the **web UI** (recommended for most users) and the **Python API** (for scripting and integration).

---

## Path 1 — Web UI

### Step 1: Start the app

If you want to use the hosted demo, go directly to [huggingface.co/spaces/HipFil98/PhDScout](https://huggingface.co/spaces/HipFil98/PhDScout) — no installation needed.

To run locally after [installing](installation.md):

```bash
pip install gradio>=4.0.0
python app.py
```

Open [http://localhost:7860](http://localhost:7860) in your browser.

---

### Step 2: Configure the LLM and upload your CV

On the **Setup & Search** tab:

1. **Upload your CV** — click the file upload area and select your `.pdf`, `.docx`, or `.txt` file.
2. **Enter a research field** — type a specific area, e.g. `machine learning`, `computational neuroscience`, or `structural biology`. More specific queries yield better results.
3. **Select a location** — choose from the dropdown (e.g. `Europe (all)`, `Germany`, `UK`) or type a custom location.
4. **Select a position type** — choose `any` to see all types, or filter to `phd`, `postdoc`, `fellowship`, etc.
5. **Set the minimum match score** — positions scoring below this threshold will still be shown in the results but highlighted differently. The default is 60.
6. **Choose a model** — `llama-3.3-70b-versatile` is the default and gives the best results. Switch to `llama-3.1-8b-instant` for faster (but slightly lower quality) responses.

Click **Parse CV & Search Positions**.

!!! note "Search time"
    The search takes approximately 30–90 seconds. Scraping four sources with polite delays accounts for most of this time; LLM scoring adds a few seconds per position.

---

### Step 3: Review the results

Switch to the **Results** tab. You will see:

- **Your CV Profile** on the left — the structured data the LLM extracted from your CV. Check this for accuracy.
- **Scored Positions** table on the right — all found positions sorted by match score, with the recommendation (`apply`, `consider`, or `skip`) and a brief explanation.

---

### Step 4: Review and edit a cover letter

Click **Go to Review** or switch to the **Review & Edit** tab.

1. Select a position from the **dropdown** (sorted highest score first).
2. Click **Load Position**.
3. The left panel shows **position details** including the full match analysis.
4. The right panel shows **CV tailoring hints** — specific suggestions for that position.
5. The **Cover Letter Draft** text box contains a generated 400–600 word letter. Edit it freely.
6. Click **Regenerate Letter** to get a different version if you are not satisfied.
7. Add any **personal notes** in the notes field.
8. Click **Approve & Save** when you are happy.

!!! warning "Always review AI-generated letters"
    Cover letters are marked `DRAFT — Review and personalise before sending.` The LLM may make mistakes or hallucinate details. Always read carefully and correct any inaccuracies before submitting.

---

### Step 5: Export

Switch to the **Export** tab. Click **Download as ZIP**.

The ZIP contains one directory per approved application:

```
applications.zip
├── summary.json
└── applications/
    ├── MIT_PhD_Machine_Learning/
    │   ├── cover_letter_draft.txt
    │   ├── my_notes.txt
    │   └── position_details.json
    └── ETH_Zurich_Postdoc_NLP/
        ├── cover_letter_draft.txt
        └── position_details.json
```

---

## Path 2 — Python API

The `JobAgent` class exposes the full pipeline as a Python API. This is useful for scripting, notebooks, or integration into other tools.

### Complete example

```python
from agent import JobAgent, LLMQuotaError

# Initialise the agent with your chosen backend
agent = JobAgent(
    model="llama-3.3-70b-versatile",
    backend="groq",
    api_key="gsk_your_key_here",
)

# Step 1: Parse CV
profile, profile_text = agent.parse_cv("cv.pdf")
print(f"Parsed CV for: {profile.get('name')}")
print(f"Research interests: {profile.get('research_interests')}")

# Step 2: Search for positions
jobs = agent.search_jobs(
    field="machine learning",
    location="Germany",
    position_type="phd",
)
print(f"Found {len(jobs)} positions")

# Step 3: Score all jobs
scored = agent.score_jobs(jobs, profile_text)

# Print the top 5
for job in scored[:5]:
    m = job["match"]
    print(
        f"  [{m['match_score']:3d}] {job['title']} "
        f"@ {job.get('institution', 'Unknown')} "
        f"({m['recommendation']})"
    )

# Step 4: Generate application materials for the top result
if scored:
    top_job = scored[0]
    try:
        hints, cover_letter = agent.prepare_application(top_job, profile_text)
        print("\n--- Cover Letter Preview ---")
        print(cover_letter[:500] + "...")
        print("\n--- CV Tailoring Hints ---")
        print("Skills to highlight:", hints.get("skills_to_highlight"))
    except LLMQuotaError as e:
        print(f"Quota exceeded: {e}")
```

### Expected output

```
Parsed CV for: Jane Smith
Research interests: ['deep learning', 'computer vision', 'medical imaging']
Found 23 positions

  [ 87] PhD Position in Deep Learning for Medical Image Analysis @ TU Munich (apply)
  [ 82] PhD Studentship: Computer Vision and Healthcare @ KIT (apply)
  [ 76] Postdoctoral Researcher: AI for Radiology @ Charité Berlin (consider)
  [ 71] Research Associate in Machine Learning @ Max Planck Institute (consider)
  [ 65] PhD in Applied Machine Learning @ Heidelberg University (consider)

--- Cover Letter Preview ---
========================================
  DRAFT — Review and personalise before sending.
  Generated by AI — may contain errors.
========================================

Dear Professor [Name],

I am writing to apply for the PhD position in Deep Learning for Medical Image Analysis
at TU Munich...
```

!!! tip "Handling quota errors"
    Always wrap LLM calls in a `try/except LLMQuotaError` block when using the HuggingFace backend. The `LLMQuotaError` exception is re-raised from all service methods and must be handled by the caller.
