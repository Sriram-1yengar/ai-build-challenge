# Kaam Sahayak — Detailed Build Spec (6 Phases)

This doc defines the **data contract** between phases first (so everyone builds against the same shape), then gives each phase owner a self-contained spec: inputs, outputs, prompts, and API calls. If every phase owner honors the contract, the phases can be built in parallel and integrated at the end with minimal glue code.

---

## 0. Shared Data Contract

All phases pass JSON. Every object includes the fields below — don't rename keys, don't change types, extend by adding new optional fields only if agreed across the team.

### 0.1 `JobSearchProfile` (output of Phase 2, input to Phase 3)
```json
{
  "applicant_id": "string",
  "language": "string (BCP-47, e.g. 'hi-IN')",
  "skills": ["string"],
  "years_experience": "number | null",
  "location": {
    "raw_text": "string (as spoken)",
    "area": "string | null",
    "city": "string | null"
  },
  "age": "number | null",
  "physical_capability_notes": ["string"],
  "availability": "string | null",
  "min_pay_expectation": "number | null",
  "pay_unit": "string | null (e.g. 'per day', 'per month')",
  "notes": "string | null"
}
```

### 0.2 `RawPosting` (output of Phase 3, input to Phase 4)
```json
{
  "posting_id": "string",
  "source_url": "string",
  "raw_title": "string",
  "raw_text": "string (full scraped text block for this posting)",
  "scraped_at": "ISO8601 timestamp"
}
```
Phase 3 outputs a `RawPosting[]` array — call this file/object `raw_postings.json`.

### 0.3 `ShortlistPosting` (output of Phase 4, input to Phase 5)
```json
{
  "posting_id": "string",
  "title": "string",
  "employer": "string | null",
  "location": "string",
  "pay": "string (human readable, e.g. '₹600/day')",
  "requirements": ["string"],
  "contact_method": "string (phone number, apply link, or instructions)",
  "source_url": "string",
  "summary": "string (1-2 sentence plain-language summary)"
}
```
Phase 4 outputs a `ShortlistPosting[]` array of length N — call this `shortlist.json`.

### 0.4 `ConversationTurn` (used internally by Phase 5)
```json
{
  "role": "applicant | agent",
  "text": "string",
  "referenced_posting_ids": ["string"]
}
```

### 0.5 `FinalOutput` (output of Phase 6)
```json
{
  "applicant_id": "string",
  "shortlisted_postings": ["ShortlistPosting"],
  "shortlisted_at": "ISO8601 timestamp"
}
```

**Rule for every phase owner:** validate your output against these shapes before handing off. If a field is genuinely unavailable, use `null` (or `[]` for arrays) — never omit the key, never invent a value.

---

## 1. Phase 1 — Voice Intake Capture

**Owner's job:** capture the applicant's spoken self-description and turn it into a clean English transcript.

**Input:** live microphone audio from the applicant.
**Output:** `{ "applicant_id": "string", "language": "string", "transcript_en": "string" }` — hand this directly to Phase 2.

### Build steps
1. Set up audio capture (browser mic → WebSocket, or file upload for simplicity if live isn't needed for MVP).
2. Connect to Sarvam's Speech-to-Text-Translate endpoint (batch REST API is simplest for a non-real-time MVP; use the realtime WS only if the team wants live partials).
   - Endpoint: `speech-to-text-translate` (batch) or `/speech-to-text-translate/ws` (streaming)
   - Auth: `API-SUBSCRIPTION-KEY` header
   - Output language: `en-IN`
3. Prompt the applicant with a short spoken instruction before recording, e.g. (displayed on screen, or read via TTS if you want it fully voice-native):
   > "Please tell me about yourself — your work experience, your skills, where you're located, your age, any physical limitations, when you're available to start, and what pay you're looking for."
4. Capture until silence/stop, send audio to Sarvam, receive `transcript` field from response.
5. Package output per the contract above and hand off.

### Notes
- Don't try to parse/structure anything in this phase — that's Phase 2's job. Phase 1 only produces clean text.
- If using batch REST (recommended for MVP simplicity over WS), audio file constraints: under 30s for the plain REST endpoint, up to 1 hour for the Batch API. A self-description should easily fit either.
- Test with a rambling, unstructured sample answer (not a clean list) — that's the realistic case Phase 2 needs to handle.

---

## 2. Phase 2 — Profile Extraction (LLM)

**Owner's job:** turn the raw transcript into a structured `JobSearchProfile`.

**Input:** `{ "applicant_id": "string", "language": "string", "transcript_en": "string" }` from Phase 1.
**Output:** `JobSearchProfile` object (see §0.1) — hand this to Phase 3.

### Prompt (system/instruction prompt for the LLM call)

```
You are extracting a structured job-search profile from a blue-collar job applicant's
spoken self-description. The transcript may be unstructured, rambling, or missing
information — extract only what is stated or clearly implied. Do not invent details.

Return ONLY valid JSON matching this exact schema, no other text:

{
  "applicant_id": "<passed through unchanged>",
  "language": "<passed through unchanged>",
  "skills": ["<string>", ...],
  "years_experience": <number or null>,
  "location": {
    "raw_text": "<verbatim location phrase from transcript>",
    "area": "<string or null>",
    "city": "<string or null>"
  },
  "age": <number or null>,
  "physical_capability_notes": ["<string>", ...],
  "availability": "<string or null>",
  "min_pay_expectation": <number or null>,
  "pay_unit": "<string or null, e.g. 'per day', 'per month'>",
  "notes": "<string or null, anything relevant that doesn't fit above fields>"
}

Rules:
- "skills" should be normalized job/trade terms (e.g. "driving", "electrical work",
  "construction labor", "plumbing", "painting", "cooking") — infer the standard trade
  name even if the applicant used casual phrasing.
- "physical_capability_notes" should stay strictly job-relevant and factual
  (e.g. "comfortable with standing shifts", "can lift up to 25kg") — do not include
  or infer any health/medical/disability information beyond what is explicitly stated
  as a job-relevant capability.
- If a field is not mentioned, use null (or empty array for list fields). Do not guess.
- Output must be valid JSON only — no markdown formatting, no commentary.

Transcript:
"""
{{transcript_en}}
"""

applicant_id: {{applicant_id}}
language: {{language}}
```

### Build steps
1. Wire this prompt into an LLM API call (Claude or GPT — team's choice, keep consistent).
2. Parse the returned JSON, validate against the schema (check all keys present).
3. Add a retry/repair step: if JSON parsing fails, re-prompt with the raw output and "Fix this to be valid JSON matching the schema, return only JSON."
4. Test against at least 3 varied sample transcripts: a clean structured one, a rambling unstructured one, and one missing several fields (e.g. no pay mentioned) — confirm nulls are used correctly rather than hallucinated values.

---

## 3. Phase 3 — Live Job Search & Scrape (Anakin.io)

**Owner's job:** take the structured profile and retrieve real, current job postings matching it.

**Input:** `JobSearchProfile` from Phase 2.
**Output:** `RawPosting[]` array — hand this to Phase 4.

### Build steps
1. Confirm and lock in your job portal source(s) — do this in pre-build prep, not live. Test manually with Anakin.io's Search API or URL Scraper against the target site(s) first.
2. Build the query construction logic: map `skills` + `location.city`/`location.area` (+ optionally `min_pay_expectation`) into a search query string or Anakin Wire/Search API parameters.
   - Example (pseudocode):
     ```
     query = f"{profile.skills[0]} jobs in {profile.location.city or profile.location.area}"
     ```
   - If multiple skills, run one query per skill (or a combined query) — decide based on what the source supports; simplest for MVP is one query using the primary/first skill.
3. Call Anakin.io:
   - If the target site is in Anakin's Wire catalog (940+ sites): use the relevant Wire action (e.g. a `jobs.search`-style op if available for your chosen source).
   - Otherwise: use Anakin's **Search API** (`/v1/search`) for a general query, or **URL Scraper** (`/v1/scrape`) against a specific listings page URL, requesting Markdown/JSON output.
4. From the raw response, extract individual postings. Each becomes a `RawPosting`:
   - `posting_id`: generate a stable ID (hash of source_url or an index)
   - `source_url`: the specific posting's URL if available, else the listings page URL
   - `raw_title`: best-effort title extraction
   - `raw_text`: the full text block for that posting (don't over-clean — Phase 4's LLM will extract structure)
   - `scraped_at`: current timestamp
5. Cap the number of raw postings retrieved to a reasonable number (e.g. top 10-15) before handing to Phase 4, which will narrow to top N.

### Notes
- This phase has the highest external-dependency risk. Build a fallback: a small local JSON file of 8-10 realistic mock postings (varied pay/location/title) in the `RawPosting` shape, so Phases 4-6 can be built/tested in parallel without waiting on live scraping to work.
- Don't filter/rank here — that's Phase 4's job with the summarizer LLM. Phase 3 just retrieves and passes through.

---

## 4. Phase 4 — Posting Summarization & Shortlist (LLM)

**Owner's job:** turn raw scraped postings into a clean, spoken-friendly Top-N shortlist.

**Input:** `RawPosting[]` from Phase 3, plus `JobSearchProfile` from Phase 2 (needed for relevance ranking).
**Output:** `ShortlistPosting[]` (length N, default N=5) — hand this to Phase 5.

### Prompt

```
You are helping a blue-collar job applicant by summarizing scraped job postings into
a short, clear shortlist. You are given the applicant's profile and a list of raw
scraped postings. Select the TOP {{N}} postings most relevant to the applicant's
skills, location, and pay expectations, and summarize each clearly.

Return ONLY valid JSON: an array of exactly {{N}} objects (or fewer if fewer than
{{N}} postings are genuinely relevant — do not pad with irrelevant postings),
each matching this schema:

[
  {
    "posting_id": "<from the raw posting>",
    "title": "<clean job title>",
    "employer": "<string or null if not stated>",
    "location": "<string>",
    "pay": "<human-readable pay, e.g. '₹600/day' — or null if not stated>",
    "requirements": ["<string>", ...],
    "contact_method": "<phone number, application link, or instructions — extract
                         exactly as given in the source text>",
    "source_url": "<from the raw posting>",
    "summary": "<1-2 sentence plain-language summary of this posting, written for
                 someone who will hear it read aloud>"
  },
  ...
]

Ranking guidance:
- Prioritize postings matching the applicant's stated skill(s) and location.
- If pay is stated on a posting, weigh postings meeting or exceeding the applicant's
  min_pay_expectation more highly, but do not exclude postings with unstated pay
  if otherwise a strong match.
- Do not fabricate details not present in the raw text — use null where information
  is genuinely missing.

Applicant profile:
{{job_search_profile_json}}

Raw postings:
{{raw_postings_json}}

Output must be valid JSON only — no markdown formatting, no commentary.
```

### Build steps
1. Wire this prompt into an LLM call, passing both the profile and raw postings JSON as context.
2. Parse and validate output array against the `ShortlistPosting` schema.
3. Test with your Phase 3 mock postings file first (don't wait on live scraping) — confirm ranking behaves sensibly (e.g. a driving job ranks above a painting job for a driver profile).
4. Add the same JSON-repair retry pattern as Phase 2 if parsing fails.

---

## 5. Phase 5 — Voice Readback & Conversational Follow-Up

**Owner's job:** read the shortlist aloud, then handle a multi-turn voice conversation where the applicant asks questions about the postings.

**Input:** `ShortlistPosting[]` from Phase 4.
**Output:** updated conversation state + (feeds into Phase 6) a running list of postings the applicant has expressed interest in.

### Step 5a — Spoken-style rewrite (LLM, before TTS)
Shortlist JSON isn't naturally speakable — do a lightweight rewrite pass first.

**Prompt:**
```
Convert this list of job postings into a short, natural spoken introduction, as if
a helpful assistant is reading them aloud one by one to someone over the phone.
Keep it concise — one short paragraph per posting, in the same order as given.
Number them ("First,", "Second,", ...) so the listener can refer back to a number
in a question. Do not add information not present in the postings.

Postings:
{{shortlist_json}}

Output plain spoken text only, no markdown, no JSON.
```
Feed this output directly to Sarvam TTS.

### Step 5b — Conversational Q&A loop
For each applicant follow-up turn:

1. Capture spoken question → Sarvam STT+Translate → English text.
2. Call the LLM with this prompt:

```
You are a helpful voice assistant helping a job applicant review a shortlist of
job postings he just heard read aloud. Answer his question using ONLY the
information in the postings below — do not use outside knowledge or invent details.
If the answer isn't in the postings, say so plainly rather than guessing.

If the applicant expresses interest in, or asks to shortlist, a specific posting,
include its posting_id in "referenced_posting_ids" and note the interest in your
answer.

Postings:
{{shortlist_json}}

Conversation so far:
{{conversation_history_json}}

Applicant's latest question:
"{{question_text}}"

Return ONLY valid JSON:
{
  "answer_text": "<spoken-style answer, concise, natural>",
  "referenced_posting_ids": ["<posting_id>", ...],
  "applicant_expressed_interest": true | false
}
```

3. Parse response, append to conversation history as a `ConversationTurn`.
4. Send `answer_text` to Sarvam TTS, play back to applicant.
5. If `applicant_expressed_interest` is true, pass the referenced posting_id(s) to Phase 6's shortlist tracker.

### Build steps
1. Build the spoken-style rewrite step first, test full readback with your Phase 4 output (mock or live).
2. Build the Q&A loop: STT → LLM (with full postings + history as context) → TTS.
3. Test with realistic follow-up questions: "which one pays more," "read the second one again," "is the [employer] one full time," "I'm interested in that one."
4. Confirm the LLM doesn't hallucinate posting details not present in the shortlist — this is the most important failure mode to test for.

---

## 6. Phase 6 — Shortlist Tracking & Final Output

**Owner's job:** track which postings the applicant has expressed interest in during the Phase 5 conversation, and present a clean final output he can use to make outreach calls.

**Input:** stream of `referenced_posting_ids` + `applicant_expressed_interest` flags from Phase 5, plus the full `ShortlistPosting[]` from Phase 4.
**Output:** `FinalOutput` object (see §0.5), rendered in the UI.

### Build steps
1. Maintain a simple state object: `shortlisted_ids: Set<string>`. On each Phase 5 turn where `applicant_expressed_interest` is true, add the referenced posting_id(s) to the set.
2. At end of conversation (applicant says something like "that's all" / "I'm done", or via an explicit UI "finish" action), resolve the set of IDs against the full `ShortlistPosting[]` to build `shortlisted_postings`.
3. Render final output clearly in the UI: for each shortlisted posting, show employer, location, pay, contact_method prominently (this is literally what the applicant will use to make his outreach call), plus the summary and source link.
4. Stamp `shortlisted_at` with current timestamp, package as `FinalOutput`.

### Notes
- Keep the UI focused on **actionability** — the contact_method field is the single most important thing to make visible and easy to read/copy, since it's what the applicant uses next.
- If Phase 5's conversational interest-detection isn't reliable yet, provide a manual fallback in the UI: simple "shortlist this" buttons next to each posting, so Phase 6 doesn't block on Phase 5 being perfect.

---

## 7. Integration Checklist (before demo)

- [ ] Phase 1 → 2: confirm `transcript_en` + `applicant_id` + `language` pass cleanly.
- [ ] Phase 2 → 3: confirm `JobSearchProfile` has usable `skills` and `location` even on sparse transcripts.
- [ ] Phase 3 → 4: confirm `RawPosting[]` isn't empty; test Phase 4 against the mock postings file independently of live scraping.
- [ ] Phase 4 → 5: confirm `ShortlistPosting[]` length matches N and every posting has a non-empty `summary`.
- [ ] Phase 5 → 6: confirm `referenced_posting_ids` actually correspond to real IDs in the shortlist (no hallucinated IDs).
- [ ] Phase 6 output: confirm `contact_method` is populated and legible for every shortlisted posting.
- [ ] Run the full pipeline end to end with one real spoken input before the demo, not just phase-by-phase.

## 8. Team Coordination Notes

- Agree on **one LLM provider** (Claude or GPT) across all phases to avoid inconsistent JSON formatting behavior between prompts.
- Agree on **applicant_id** generation up front (even a hardcoded `"demo_applicant_1"` is fine) so every phase can be tested independently without waiting on Phase 1.
- Whoever owns Phase 3 should share the mock `raw_postings.json` fallback file with Phases 4-6 owners as early as possible, so those phases aren't blocked waiting on live scraping to work.
- Keep all prompts and schemas in this doc as the source of truth — if a phase owner needs to deviate from a schema, flag it to the team before changing it, since downstream phases depend on the exact shape.