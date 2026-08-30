# Phase 5 — Voice Readback & Conversational Follow-Up

Owner's job: read the shortlist aloud, then handle a multi-turn conversation where
the applicant asks follow-up questions about the postings. See `detailed-build-plan.md`
section 5 at the repo root for the full spec this implements.

**Input:** `ShortlistPosting[]` (from Phase 4, or `shared/fixtures/shortlist.json` for standalone dev).
**Output:** conversation state + a running set of `posting_id`s the applicant expressed interest in
(consumed by Phase 6).

Stack: Python / FastAPI. LLM: Gemini Flash (`google-genai`). Voice: Sarvam TTS + STT.
Follow-up questions can come in as typed text (`/ask`, for debugging) or as a
spoken recording (`/ask-audio`, transcribed+translated via Sarvam STT) — both
land on the same Q&A logic.

## Setup

```bash
cd phase5-voice-readback
python -m venv .venv
source .venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```

Copy `.env.example` (repo root) to `.env` (repo root) and fill in `SARVAM_API_KEY`
and `GEMINI_API_KEY`. This app loads that root `.env`, not a local one.

## Run

```bash
uvicorn app.main:app --reload --port 8005
```

## Endpoints

- `POST /session/start` — body: `{}` (uses the mock fixture) or `{"postings": [...]}` to pass a real Phase 4 shortlist.
  Returns `session_id`, a spoken `guide_text` + `guide_audio_base64` explaining the colour system
  (green = strong match, yellow = worth a look, red = may not fit, based on each posting's
  `match_score`), then `postings`: a list of `{posting_id, text, audio_base64}` — one spoken
  blurb per posting, in order, so the frontend can play them one at a time and highlight the
  matching posting's colour while it's being narrated.
- `POST /session/{session_id}/ask` — body: `{"question_text": "which one pays more"}`.
  Returns the answer text + audio, any `referenced_posting_ids`, whether interest was expressed,
  and the running `shortlisted_ids` set.
- `POST /session/{session_id}/ask-audio` — multipart form, field `audio` = recorded question
  (webm/wav/mp3/etc). Transcribes+translates via Sarvam STT (`mode=translate`), then behaves
  exactly like `/ask`. Same response shape as `/ask`.
- `POST /session/{session_id}/shortlist` — body: `{"posting_id": "post_003", "shortlisted": true}`.
  Manual shortlist fallback (independent of the LLM's interest-detection) — returns full session state.
- `GET /session/{session_id}/state` — full session dump (postings, conversation history, shortlisted_ids).
  This is what Phase 6 should read to build `FinalOutput`.

## Manual test script

```bash
curl -s -X POST localhost:8005/session/start | python -m json.tool
# copy session_id from the response, then:
curl -s -X POST localhost:8005/session/{session_id}/ask \
  -H "Content-Type: application/json" \
  -d '{"question_text": "what benefits does it offer and is the shift fixed or rotational"}' | python -m json.tool

curl -s -X POST localhost:8005/session/{session_id}/ask \
  -H "Content-Type: application/json" \
  -d '{"question_text": "read the Whitefield one again"}' | python -m json.tool

curl -s -X POST localhost:8005/session/{session_id}/ask \
  -H "Content-Type: application/json" \
  -d '{"question_text": "I am interested in that one, shortlist it"}' | python -m json.tool

curl -s localhost:8005/session/{session_id}/state | python -m json.tool
```

Per the integration checklist in `detailed-build-plan.md`, confirm `referenced_posting_ids`
in the `/ask` responses always correspond to real IDs in the shortlist — `app/llm.py`
filters out anything else, but re-check this against real Gemini output, not just the mock.
