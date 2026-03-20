"""Job matcher prompts."""

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

Eligibility gate — apply BEFORE scoring:
- If the position type is "postdoc" or "fellowship" AND the candidate's education
  shows NO completed or in-progress PhD/doctorate, the score MUST be ≤ 30
  regardless of research overlap. Postdoc and fellowship positions legally and
  practically require a doctoral degree. Report the missing PhD in "concerns" and
  set recommendation to "skip".
- If the candidate is a current PhD student (degree in progress, expected graduation
  listed), they may apply to postdoc positions but score conservatively (cap at 65)
  since eligibility depends on completion timing.
- PhD positions are open to master's graduates and above — no eligibility cap applies.

Scoring guide:
  85-100: Excellent match — research interests closely aligned, strong publication record in the area
  70-84:  Good match — clear research overlap, most skills present
  55-69:  Partial match — meaningful overlap even if not all keywords match exactly
  35-54:  Weak match — limited overlap, significant gaps
  0-34:   Poor match — very different research areas or eligibility not met

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
