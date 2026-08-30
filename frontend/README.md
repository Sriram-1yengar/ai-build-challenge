# Frontend — Kaam Sahayak Demo Shell

The end-to-end applicant-facing UI for the full demo narrative (see
`detailed-build-plan.md` §0 at the repo root). It walks through all 6 phases,
but only **Phase 5 is wired to a real backend** right now — every other phase
is mocked client-side so the flow is demoable while Phases 1-4 and 6 are still
being built. Each step is visibly tagged "mock" or "live" in the UI.

| Step | Phase | Status |
|---|---|---|
| Tell us about yourself | 1 — voice intake | Mocked: type a self-description (mic capture not wired) |
| Confirm your profile | 2 — profile extraction | Mocked: a tiny keyword heuristic drafts the fields, you edit them |
| Job search | 3/4 — search + shortlist | Mocked: ranks `shared/fixtures/shortlist.json` (mirrored into `public/mock/`) by keyword match against your skills |
| Hear & discuss shortlist | 5 — voice readback & Q&A | **Live** — calls the real FastAPI backend in `../phase5-voice-readback` |
| Your shortlist | 6 — final output | **Live** — built client-side from that session's `/state` |

## Setup

```bash
cd frontend
npm install
```

Copy `.env.example` to `.env` only if you need to point at a backend that
isn't `http://localhost:8005` (e.g. a teammate's machine). No secrets live
here — those stay in the root `.env` per `structure.md`.

## Run

1. Start the Phase 5 backend first (see `../phase5-voice-readback/README.md`):
   ```bash
   cd ../phase5-voice-readback
   uvicorn app.main:app --reload --port 8005
   ```
2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open the printed `localhost` URL (default `http://localhost:5173`).

The "Hear & discuss shortlist" step needs mic permission for the "Ask by
voice" button (uses `getUserMedia` + `MediaRecorder`, sent to the backend's
`/ask-audio` endpoint, which transcribes it via Sarvam STT). This requires a
secure context — `localhost` is fine, but a non-`localhost` deployment needs
HTTPS or the browser will refuse mic access. The text box next to it hits
`/ask` directly and is there for debugging without a working mic.

## Notes for other phase owners

- Don't need to touch this folder to build your phase standalone — that's
  the point of `shared/fixtures/`. When your phase's real output is ready,
  swap the relevant mocked step here for a real API call (see `SearchStep.jsx`
  and `IntakeStep.jsx`/`ProfileStep.jsx` for where the mocks live) or ping the
  team to do the wiring together.
- The Phase 5 backend gained two additions beyond the original spec while
  building this UI: `POST /session/{id}/ask-audio` (voice question path) and
  `POST /session/{id}/shortlist` (manual shortlist toggle, per the build
  plan's Phase 6 fallback note). Both are documented in its README.
