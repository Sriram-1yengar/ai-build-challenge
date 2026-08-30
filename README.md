# Kaam Sahayak

A single Node.js application that currently implements Phase 1 and Phase 2 of the build plan:

1. Records an applicant's voice and translates it to English with Sarvam.
2. Extracts a validated `JobSearchProfile` with Gemini 3.6 Flash.

## Project structure

```text
src/                         server and application logic
  server.js                  HTTP server and API routes
  profile-extraction.js      Gemini prompt, structured output, repair retry
  profile-schema.js          runtime contract validation
public/                      browser UI
test/                        automated tests
shared/schemas/
  job_search_profile_phase-1.schema.json
shared/fixtures/
  sample_profile_phase-1.json
```

## Setup

Copy `.env.example` to `.env`, provide `SARVAM_API_KEY` and `GEMINI_API_KEY`, then run:

```sh
npm install
npm start
```

Open `http://127.0.0.1:3000`. The UI runs the complete voice-to-profile flow through the same application server.

## API

- `POST /api/transcribe` — audio body plus `x-applicant-id` header; returns the Phase 1 transcript.
- `POST /api/extract-profile` — Phase 1 JSON body; returns a validated `JobSearchProfile`.
- `GET /api/health` — reports service status and configured Gemini model.

Run `npm test` for the profile extraction suite. Tests mock Gemini and do not use API quota.
