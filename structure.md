# Repository Structure

Kaam Sahayak is one application with phase boundaries represented by modules and shared data contracts—not separate nested projects.

```text
ai-build-challenge/
├── src/
│   ├── server.js                  # web server, Phase 1 and Phase 2 routes
│   ├── profile-extraction.js      # Gemini profile extraction and repair retry
│   └── profile-schema.js          # runtime JobSearchProfile validation
├── public/
│   ├── index.html                 # voice-to-profile interface
│   ├── app.js                     # browser recording and API workflow
│   └── styles.css
├── test/
│   └── profile-extraction.test.js
├── shared/
│   ├── schemas/
│   │   └── job_search_profile_phase-1.schema.json
│   └── fixtures/
│       └── sample_profile_phase-1.json
├── detailed-build-plan.md         # product requirements and phase contracts
├── .env.example                   # all environment variable names
├── package.json                   # single dependency manifest
└── README.md                      # setup and API documentation
```

## Architecture rules

1. Keep one root package and one application server.
2. Put server-side business logic in focused modules under `src/`.
3. Keep phase handoffs as validated JSON contracts under `shared/schemas/`.
4. Use Gemini Flash through `@google/genai`; the configured default is `gemini-3.6-flash`.
5. Keep secrets only in the root `.env` and document variable names in `.env.example`.
6. Add later phases as modules and routes in this application unless they require a genuinely separate runtime.

## Implemented request flow

```text
Browser recording
  → POST /api/transcribe
  → Sarvam speech-to-text translation
  → POST /api/extract-profile
  → Gemini structured extraction
  → JobSearchProfile validation
  → Profile displayed in the browser
```

The application runs on port `3000` by default. Use `PORT` to override it.
