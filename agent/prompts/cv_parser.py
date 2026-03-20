"""CV parser prompts."""

CV_PARSER_SYSTEM = (
    "You are an expert academic CV parser. "
    "Extract ALL information from the CV text into structured JSON. "
    "Pay special attention to research-specific fields: thesis topics, "
    "publications, research interests, and lab/technical skills. "
    "Respond only with valid JSON — no markdown fences, no commentary."
)

CV_PARSER_PROMPT = """Extract ALL information from the following CV and return a single JSON object.

Expected structure (use null for missing scalars, [] for missing lists):
{{
  "name": "Full Name",
  "contact": {{"email": "...", "phone": "...", "linkedin": "...", "github": "...", "website": "..."}},
  "summary": "Brief research summary",
  "education": [{{"degree": "PhD", "institution": "MIT", "field": "CS", "year": "2021", "thesis_topic": "..."}}],
  "experience": [{{"title": "Research Assistant", "institution": "ETH Zurich", "dates": "2019-2021", "description": "..."}}],
  "research_interests": ["machine learning", "NLP"],
  "publications": [{{"title": "...", "venue": "NeurIPS 2022", "year": "2022", "authors": "..."}}],
  "skills": {{"programming": ["Python"], "tools": ["PyTorch"], "languages": ["LaTeX"], "lab_techniques": []}},
  "awards": ["Best Paper Award NeurIPS 2022"],
  "languages": [{{"language": "English", "level": "Native"}}],
  "references": [{{"name": "Prof. Jane Smith", "title": "Full Professor", "institution": "MIT"}}]
}}

Do NOT invent information — extract only what is present.

CV TEXT:
---
{cv_text}
---"""
