# Repository Structure

Kaam Sahayak is one product built as a few independently-owned services in one
repo, not six identical clones of a template. Default to adding a new phase as a
module/route inside the root Node app (Phase 1/2's app) — only break out a
separate service when the phase genuinely needs a different runtime, the way
Phase 5 needs Python for `google-genai` + Sarvam's Python-friendly flow. The
`frontend/` app is the one applicant-facing UI and is expected to call every
phase's real API directly as each comes online.

## What's actually here today

```text
ai-build-challenge/
├── idea-breakdown.md            # original concept + demo narrative
├── detailed-build-plan.md       # full spec: data contract + per-phase prompts/build steps
├── structure.md                 # this file
├── README.md                    # setup for the root Node app (Phase 1/2)
├── .env.example                 # every secret needed, across all phases
├── .env                         # actual secrets (gitignored, not committed)
├── .gitignore
├── package.json / package-lock.json   # Phase 1/2's Node app manifest
│
├── src/                          # Phase 1 (voice intake) + Phase 2 (profile extraction), Node/Express
│   ├── server.js                 # HTTP server + API routes, port 3000
│   ├── profile-extraction.js     # Gemini prompt, structured output, repair retry
│   └── profile-schema.js         # runtime JobSearchProfile validation
├── public/                       # Phase 1/2's own reference UI (vanilla JS) — superseded by frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── test/
│   └── profile-extraction.test.js   # mocks Gemini, no API quota used
│
├── shared/
│   ├── schemas/                  # JSON Schema mirror of detailed-build-plan.md section 0
│   │   ├── job_search_profile_phase-1.schema.json
│   │   ├── job_search_profile.schema.json
│   │   ├── raw_posting.schema.json
│   │   ├── shortlist_posting.schema.json
│   │   ├── conversation_turn.schema.json
│   │   └── final_output.schema.json
│   └── fixtures/                 # mock data so phases can build without waiting on each other
│       ├── sample_profile_phase-1.json
│       ├── shortlist.json        # sample ShortlistPosting[] (owned by Phase 4, used by Phase 5/6)
│       ├── raw_postings.json     # sample RawPosting[] (owned by Phase 3) — TODO: not added yet
│       └── sample_profile.json   # sample JobSearchProfile (owned by Phase 2) — TODO: not added yet
│
├── phase5-voice-readback/        # Phase 5, Python/FastAPI (separate runtime: google-genai + Sarvam), port 8005
│   ├── app/
│   └── README.md
│
├── frontend/                     # React/Vite applicant-facing UI, port 5173 — talks to every phase's
│                                  # real backend as it comes online, mocking whatever isn't built yet
│
└── (phase 3, 4, 6 — not built yet; default to adding them as routes/modules in src/
     unless they need a separate runtime, per the rule above)
```

## Ground rules

1. **Own your service, don't reach into someone else's.** Phase 1/2 owns `src/`,
   `public/`, root `package.json`. Phase 5 owns `phase5-voice-readback/`. Everyone
   can extend `frontend/` to wire in their own phase's real API. Changes to
   `shared/`, this file, or another phase's service get flagged to the team first.
2. **The data contract is law.** `detailed-build-plan.md` section 0 defines the
   exact JSON shape passed between phases, mirrored machine-readably in
   `shared/schemas/`. Missing field -> `null` (or `[]` for arrays). Never omit a
   key, never invent a value, never rename/add fields without team agreement.
3. **Build and test against fixtures, not against each other.** Each phase should
   run and be testable standalone using the mock data in `shared/fixtures/`.
   Wire the real upstream call in as a drop-in replacement once both sides are ready.
4. **One LLM provider: Gemini Flash** (model `gemini-3.6-flash` — Node via
   `@google/genai`, Python via `google-genai`), for every phase that makes an LLM
   call. Keeps JSON-formatting behavior consistent. Free-tier quota is 20
   requests/day per model and is shared across the whole team's testing — expect
   to hit it, and don't burn it on repeated live-demo runs while developing.
5. **One shared `.env` at repo root.** No per-service `.env` files — see
   `.env.example` for the full key list and which phase uses what.
6. **applicant_id**: use the hardcoded `"demo_applicant_1"` for standalone
   dev/testing until Phase 1 is wired in everywhere.

## Dev ports

| Service | Port |
|---|---|
| Phase 1 + 2 (root Node app) | 3000 |
| Phase 5 (voice readback) | 8005 |
| frontend (Vite dev server) | 5173 |

## Integration

Per `detailed-build-plan.md` section 7: once a phase works standalone against the
fixtures, hand its real output format to the next phase's owner and confirm it
validates against the shared schema. `frontend/` is where the real end-to-end
demo path gets wired together as each phase's backend comes online — replace its
client-side mock for that step with a real call, the way `ReadbackStep` already
calls the live Phase 5 API.
