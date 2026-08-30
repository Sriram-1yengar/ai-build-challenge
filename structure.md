# Repo Structure

Kaam Sahayak is built as 6 independently-owned phases (see `detailed-build-plan.md`)
in one repo. This doc is the map every phase owner (and their coding agent) should
follow so parallel work doesn't collide, and so the pieces integrate cleanly at the end.

## Ground rules

1. **Own only your phase folder.** Don't edit another phase's directory. If you need
   a change to shared contract, fixtures, or this doc, flag it to the team first —
   downstream phases depend on these staying stable.
2. **The data contract is law.** `detailed-build-plan.md` section 0 defines the exact
   JSON shape passed between phases, mirrored machine-readably in `shared/schemas/`.
   Validate your output against it before calling your phase "done." Missing field →
   `null` (or `[]` for arrays). Never omit a key, never invent a value, never rename
   or add fields without team agreement.
3. **Build and test against fixtures, not against each other.** Each phase should run
   and be testable standalone using the mock data in `shared/fixtures/`, without
   waiting on the phase before it to be finished. Wire the real upstream call in as
   a drop-in replacement once both sides are ready.
4. **One LLM provider: Gemini Flash** (`google-genai`, model `gemini-2.5-flash`),
   for every phase that makes an LLM call (2, 4, 5). Keeps JSON-formatting behavior
   consistent across phases.
5. **One shared `.env` at repo root.** No per-phase `.env` files — see `.env.example`
   for the full key list and which phase uses what. Copy it to `.env` and fill in keys.
6. **applicant_id**: use the hardcoded `"demo_applicant_1"` for all standalone dev/testing
   until Phase 1 is wired in, so every phase can be tested independently.

## Directory layout

```
ai-build-challenge/
├── idea-breakdown.md            # original concept + demo narrative
├── detailed-build-plan.md       # full spec: data contract + per-phase prompts/build steps
├── structure.md                 # this file
├── .env.example                 # every secret needed, across all phases
├── .env                         # actual secrets (gitignored, not committed)
├── .gitignore
│
├── shared/
│   ├── schemas/                 # JSON Schema mirror of detailed-build-plan.md section 0
│   │   ├── job_search_profile.schema.json
│   │   ├── raw_posting.schema.json
│   │   ├── shortlist_posting.schema.json
│   │   ├── conversation_turn.schema.json
│   │   └── final_output.schema.json
│   └── fixtures/                # mock data so phases can build without waiting on each other
│       ├── shortlist.json       # sample ShortlistPosting[] (owned by Phase 4, used by Phase 5/6)
│       ├── raw_postings.json    # sample RawPosting[] (owned by Phase 3, used by Phase 4) — TODO: Phase 3 owner to add
│       └── sample_profile.json  # sample JobSearchProfile (owned by Phase 2, used by Phase 3) — TODO: Phase 2 owner to add
│
├── phase1-voice-intake/         # Sarvam STT+Translate: mic audio -> transcript_en
├── phase2-profile-extraction/   # LLM: transcript_en -> JobSearchProfile
├── phase3-job-search/           # Anakin.io: JobSearchProfile -> RawPosting[]
├── phase4-posting-summary/      # LLM: RawPosting[] + JobSearchProfile -> ShortlistPosting[]
├── phase5-voice-readback/       # LLM spoken rewrite + Sarvam TTS + Q&A loop -> shortlisted_ids (built)
├── phase6-shortlist-output/     # tracks interest, assembles FinalOutput, renders final UI
│
└── integration/                 # wired end-to-end demo path; built last, once all 6 phases work standalone
```

Each `phaseN-*/` folder is a self-contained project: its own dependency manifest
(`requirements.txt`, `package.json`, whatever fits), its own source code, and its
own `README.md` stating (a) exact input/output per the contract, (b) how to run it,
(c) how to test it standalone against the fixtures. `phase5-voice-readback/README.md`
is a reference example of the expected shape.

Phase owners pick their own language/framework per folder — the contract is the
only thing that has to match across phases, not the tech stack. (Phase 5 is
Python/FastAPI; other phases are free to differ.)

## Dev ports (when running multiple phases as local services at once)

| Phase | Port |
|---|---|
| 1 — voice intake | 8001 |
| 2 — profile extraction | 8002 |
| 3 — job search | 8003 |
| 4 — posting summary | 8004 |
| 5 — voice readback | 8005 |
| 6 — shortlist output | 8006 |

## Integration

Per `detailed-build-plan.md` section 7 (Integration Checklist): once your phase
works standalone against the fixtures, hand your real output format to the next
phase's owner and confirm it validates against the shared schema. The `integration/`
folder is where the full pipeline gets wired end-to-end near the end of the build —
don't build it prematurely; standalone-per-phase is what unblocks parallel work.
