# Job Search API (Phase 3 + Phase 4 integration)

Chains Phase 3 (`phase3-job-search/`, live search via Anakin) into Phase 4
(`phase4-posting-summary/`, deterministic ranking + grounded LLM summaries)
behind one HTTP endpoint, so the frontend makes a single call instead of
visiting two separate services. Doesn't modify either phase's code — imports
their functions directly.

**Input:** `{ "profile": <JobSearchProfile>, "use_llm": true }`
**Output:** `{ "postings": <ShortlistPosting[]>, "raw_postings": <RawPosting[]>, "benchmark": <SalaryBenchmark> }`

## Known scope limitation

Phase 3's title gate (`phase3-job-search/filter.py`) and Phase 4's scoring
(`phase4-posting-summary/score.py`) are both hard-coded to the **security
guard** role in Bengaluru (`sources.py`'s `QUERY`/`CITY`, `GUARD_WORDS`,
`SENIOR_WORDS`) — they don't yet read `profile.skills` to search/rank other
trades. A profile for any other trade (electrician, driver, etc.) will search
for security guard jobs anyway and likely rank nothing (`score.rank` drops any
posting with zero role points). For a live demo, use a security-guard-shaped
applicant profile (e.g. "I've done security guard work for two years, based in
Bengaluru...") until this is generalized.

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
