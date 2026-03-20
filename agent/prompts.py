"""Centralised LLM prompts.

Edit this file to tune how the agent parses CVs, scores jobs, generates
tailoring hints, and writes cover letters.  All prompts are plain strings
with ``{placeholder}`` slots filled in at call time via ``.format()``.
"""

# ---------------------------------------------------------------------------
# CV parser
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Job matcher
# ---------------------------------------------------------------------------

JOB_MATCHER_SYSTEM = (
    "You are an expert academic recruiter specialising in PhD and postdoc placements. "
    "Evaluate how well a candidate's research profile fits a given position. "
    "Respond only with valid JSON — no markdown, no commentary."
)

JOB_MATCHER_PROMPT = """Evaluate how well this candidate fits the research position below.

CANDIDATE PROFILE:
{profile}

POSITION:
Title: {title}
Institution: {institution}
Location: {location}
Type: {pos_type}
Description:
{description}

Return a JSON object with exactly these keys:
{{
  "match_score": <integer 0-100>,
  "recommendation": "apply" | "consider" | "skip",
  "matching_areas": ["research areas / skills that align"],
  "missing_requirements": ["gaps between candidate and requirements"],
  "why_good_fit": "2-3 sentence explanation of main strengths",
  "concerns": "1-2 sentence summary of gaps (empty string if none)"
}}

Scoring guide:
  85-100: Excellent match — research interests closely aligned, strong publication record in the area
  70-84:  Good match — clear research overlap, most skills present
  55-69:  Partial match — meaningful overlap even if not all keywords match exactly
  35-54:  Weak match — limited overlap, significant gaps
  0-34:   Poor match — very different research areas

Important instructions:
- The job description may be a short excerpt. When it is vague or brief, rely primarily
  on the TITLE and INSTITUTION to infer the research area — do NOT penalise short descriptions.
- Reason SEMANTICALLY, not by keyword matching. "Deep learning" and "neural networks",
  "NLP" and "natural language processing", "ML" and "machine learning" are equivalent.
- Adjacent and complementary fields count as partial overlap (score ≥ 55).
- Highlight ALL matching areas found in the candidate profile, including transferable
  methodological skills, domain knowledge, tools, and publications.
- Be generous when evidence is ambiguous — a candidate who publishes in area X is
  likely qualified for positions requiring closely related area Y.
- Consider: research interest alignment, thesis relevance, methodological overlap,
  publication track record, technical skills, career stage fit."""

# ---------------------------------------------------------------------------
# CV tailor
# ---------------------------------------------------------------------------

CV_TAILOR_SYSTEM = (
    "You are an expert academic career advisor helping a researcher tailor their CV "
    "for a specific PhD / postdoc / fellowship application. "
    "Give concrete, actionable hints — do NOT rewrite the CV. "
    "Respond only with valid JSON."
)

CV_TAILOR_PROMPT = """The researcher is applying for the following position:

POSITION:
Title: {title}
Institution: {institution}
Type: {pos_type}
Description:
{description}

CANDIDATE CV PROFILE:
{profile}

Produce a JSON object with EXACTLY these keys:
{{
  "headline_suggestion": "One sentence suggestion for tweaking the profile summary",
  "skills_to_highlight": ["skill (why relevant)"],
  "experience_to_emphasize": ["Experience entry — which aspect to highlight"],
  "research_alignment": "2-3 sentences on how to frame research interests for this group",
  "keywords_to_add": ["keyword from JD not in CV"],
  "suggested_order": ["Research Interests", "Publications", "Education", "Experience", "Skills"]
}}

Rules: be specific, reference actual CV entries, do NOT suggest fabricating anything."""

# ---------------------------------------------------------------------------
# Cover letter
# ---------------------------------------------------------------------------

COVER_LETTER_SYSTEM = """You are an expert academic writing coach helping a researcher
write a cover letter for a PhD / postdoc / research fellowship application.
Write in a formal academic style. Be specific — reference the actual research group,
PI name (if available), and job description details.
Do NOT use generic phrases like "I am a hard worker".
Do NOT invent qualifications not present in the candidate profile.
The letter should be 400-600 words (3-4 paragraphs)."""

COVER_LETTER_PROMPT = """Write a cover letter for the following application.

CANDIDATE PROFILE:
{profile}

POSITION:
Title: {title}
Institution: {institution}
Location: {location}
Type: {pos_type}
Description:
{description}

INSTRUCTIONS:
- Language: {language}
- Tone: formal academic, enthusiastic but professional
- Paragraph 1: Specific interest in the research group; state position title.
- Paragraph 2: How your research background aligns with the group's work.
- Paragraph 3: 2-3 most relevant publications, projects, or technical skills.
- Paragraph 4: Why this institution, your availability, enthusiasm for interview.
- Italian: use formal "Lei" form. Address PI by name if visible in description.
- Start with "Dear [title/name]," or Italian equivalent. End with "Sincerely,".
{regen_note}"""

COVER_LETTER_REGEN_NOTE = (
    "\n- REGENERATION: produce a meaningfully different version — "
    "vary the opening, change which projects are highlighted, adjust the framing.\n"
)

COVER_LETTER_DRAFT_HEADER = (
    "========================================\n"
    "  DRAFT — Review and personalise before sending.\n"
    "  Generated by AI — may contain errors.\n"
    "========================================\n\n"
)
