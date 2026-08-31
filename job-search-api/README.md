# Job Search API (Phase 3 + Phase 4 integration)

Chains Phase 3 (`phase3-job-search/`, live search via Anakin) into Phase 4
(`phase4-posting-summary/`, deterministic ranking + grounded LLM summaries)
behind one HTTP endpoint, so the frontend makes a single call instead of
visiting two separate services. Doesn't modify either phase's code — imports
their functions directly.

**Input:** `{ "profile": <JobSearchProfile>, "use_llm": true }`
**Output:** `{ "postings": <ShortlistPosting[]>, "raw_postings": <RawPosting[]>, "benchmark": <SalaryBenchmark> }`

## Role coverage

Search query, Apna's category slug, and Phase 3/4's title-gate and ranking are
all driven by `profile.skills[0]`, mapped from Phase 2's normalized skill
phrasing to real job-title vocabulary (`sources.SKILL_TITLE_TERMS`, duplicated
in `phase4-posting-summary/score.py` so each phase stays standalone-testable).
Covers: driving, electrical work, construction labor/construction, plumbing,
painting, cooking, delivery, carpentry, masonry, security, housekeeping,
welding. A skill outside that list falls back to searching/matching on the
raw skill text as given — works, but less precisely than a mapped trade.

Location is still fixed to Bengaluru (`sources.py`'s `CITY`, and the
Bengaluru-only post-search filter) regardless of `profile.location` —
broadening that is a separate, not-yet-done change.

## Setup

```bash
cd job-search-api
python -m venv .venv
source .venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```

Needs `ANAKIN_API_KEY` and `GEMINI_API_KEY` in the root `.env`.

## Run

```bash
python server.py
```

Runs on port 8003.

## Test

```bash
curl -s -X POST localhost:8003/api/job-search \
  -H "Content-Type: application/json" \
  -d '{"profile": {"skills": ["security guard"], "years_experience": 2, "location": {"area": "Whitefield", "city": "Bengaluru"}, "min_pay_expectation": 15000}}' \
  | python -m json.tool
```

A live run calls Anakin (job search) and Gemini (summaries) for real —
expect it to take a while and to consume both quotas.
