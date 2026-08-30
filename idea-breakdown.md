# Build Plan

Voice-first blue-collar job matching assistant. Applicant speaks his profile → LLM structures it → Anakin scrapes/searches job portals → LLM summarizes top N postings → Sarvam voice agent reads them back and answers follow-up questions → applicant shortlists and calls employers directly.

## 0. Demo Narrative (design every task around proving this)

1. **Voice intake**: Applicant speaks freely about himself (experience, location, age, physical ability, skills) — no form filling.
2. **Structured profile**: LLM turns that into a clean, structured job-search profile doc.
3. **Live grounded search**: Anakin uses the profile to scrape/search real blue-collar job portals and shortlists top N postings.
4. **Digestible summary**: LLM turns raw postings into a short context doc — key facts per posting only.
5. **Conversational shortlisting**: Sarvam voice agent reads the summary back, and the applicant can ask questions ("which one pays more," "is the Whitefield one still available," "read that one again") to narrow down his shortlist.
6. **Actionable output**: Applicant walks away with shortlisted postings' key info (employer, contact/apply method, pay, location) ready to use for outreach calls.

If time runs short, the app is still a demo as long as beats 1–4 work end to end — beat 5 (multi-turn follow-up conversation) is the stretch layer.

## 1. Architecture

```
[Applicant speaks profile] 
        │
        ▼
[Sarvam STT+Translate] → raw English transcript of applicant's spoken self-description
        │
        ▼
[LLM: Profile Extractor] → structured Job Search Profile doc
        (fields: skill(s)/trade, years experience, location, age, physical constraints,
         availability, pay expectation, language)
        │
        ▼
[Anakin: Search/Crawl/Wire] → query blue-collar job portal(s) using profile fields
        │
        ▼
[Raw scraped postings: N results]
        │
        ▼
[LLM: Posting Summarizer] → Top-N Shortlist Context Doc
        (per posting: title, employer, location, pay, requirements, how to apply/contact, source link)
        │
        ▼
[Sarvam TTS] → reads shortlist summary aloud to applicant
        │
        ▼
[Applicant asks follow-up questions] → Sarvam STT+Translate → English question
        │
        ▼
[LLM: Conversational Agent over Shortlist Doc] → answers using only the shortlist doc as context
        │
        ▼
[Sarvam TTS] → spoken answer
        │
        ▼
[Applicant marks postings as shortlisted] → final output: shortlisted postings w/ contact info, 
        displayed in UI for the applicant to use when calling employers
```

## 2. Components

| Component | Tool | Purpose |
|---|---|---|
| Voice intake capture | Sarvam STT+Translate (WS or REST) | Converts applicant's spoken self-description to English text |
| Profile Extractor | LLM call | Structures freeform transcript into a fielded Job Search Profile doc |
| Job portal search | Anakin.io Search API / Crawl / Wire | Queries live blue-collar job listing source(s) using profile fields |
| Posting Summarizer | LLM call | Condenses raw scraped postings into a clean top-N shortlist doc |
| Voice readback | Sarvam TTS (WS) | Reads the shortlist doc aloud to the applicant |
| Conversational Q&A agent | LLM call, scoped to shortlist doc as context | Answers applicant's follow-up questions about the postings |
| Shortlist tracker | Simple state (session var or JSON) | Tracks which postings the applicant has shortlisted during the conversation |
| Frontend | Minimal UI | Mic button, live transcript, shortlist doc display, final shortlisted-postings output panel |

## 3. Pre-Build Prep (before the clock starts)

- [ ] Get Sarvam API key, test STT+Translate and TTS endpoints individually with sample audio.
- [ ] Get Anakin.io API key, test a Search/Scrape call against your chosen job portal source.
- [ ] **Pick and hard-test the exact job portal/source.** Highest-risk unknown — confirm Anakin can return structured, usable listing data (title, location, pay, requirements, contact/apply method) from it. Have a backup source or a controlled mock listings page ready if the primary source scrapes poorly.
- [ ] Draft the Profile Extractor prompt and test it against 2-3 sample spoken self-descriptions (write these out as if transcribed) to confirm it reliably produces the fields you need.
- [ ] Draft the Posting Summarizer prompt and test it against sample raw scraped listing text.
- [ ] Decide top N (start with N=5 — enough to be useful, short enough to read aloud without losing the applicant).

## 4. Task Breakdown (2-hour build window)

### Phase 1 — Voice intake → structured profile (0:00–0:25)
- [ ] Build Sarvam STT+Translate relay: capture mic audio, stream to Sarvam, get English transcript back.
- [ ] Write Profile Extractor prompt: transcript → structured Job Search Profile JSON (skill, experience, location, age, physical ability/constraints, availability, pay expectation, language).
- [ ] Test: speak a sample self-description, confirm clean structured profile output in console/UI.

### Phase 2 — Live job search + shortlist (0:25–0:55)
- [ ] Build query construction: map profile fields → Anakin search/scrape parameters (skill + location as primary filters).
- [ ] Call Anakin.io Search/Crawl/Wire against chosen job portal, retrieve raw postings.
- [ ] Write Posting Summarizer prompt: raw postings → Top-N Shortlist Context Doc (structured, one block per posting).
- [ ] Test: run profile from Phase 1 through this pipeline, confirm shortlist doc is accurate and complete.

### Phase 3 — Voice readback (0:55–1:15)
- [ ] Feed shortlist doc into Sarvam TTS, confirm it reads naturally (may need to reformat doc into more spoken-friendly phrasing before TTS — consider a lightweight LLM "spoken-style rewrite" pass).
- [ ] Test full loop: spoken profile in → shortlist read back out, no follow-up yet. **Demo-safe checkpoint.**

### Phase 4 — Conversational follow-up (1:15–1:45)
- [ ] Build Q&A agent: takes applicant's follow-up question (via Sarvam STT+Translate) + shortlist doc as context, answers using only that doc (avoid hallucinating details not in the postings).
- [ ] Wire spoken question → answer → Sarvam TTS response loop.
- [ ] Add shortlisting mechanism: let applicant say "shortlist that one" / "I'm interested in the second one" and track it in state.
- [ ] Test: ask 2-3 follow-up questions ("which pays more," "read the Whitefield one again," "shortlist that one") and confirm correct, grounded answers + tracking.

### Phase 5 — Final output + polish (1:45–2:00)
- [ ] Display final shortlisted postings clearly in UI: employer, contact/apply method, pay, location — ready for the applicant to use for outreach calls.
- [ ] Rehearse full demo narrative (beats 1–5) once end to end.
- [ ] Record a backup clip of the full flow in case of live demo issues (WiFi/API flakiness).

## 5. Cut List (if behind schedule)

- Drop the conversational follow-up layer (Phase 4) — a working profile → shortlist → voice readback loop (Phases 1–3) is still a complete, demoable product.
- Drop live TTS readback of the *entire* shortlist — read back just the top 2-3 postings if TTS pacing/length becomes an issue.
- If Anakin scraping of the real job portal is unreliable under time pressure, fall back to a small set of realistic mock postings you control, and be upfront with judges that the scraping layer is swapped to a static source for demo reliability — the pipeline (search → summarize → voice) is still real.
- If shortlist state-tracking is fiddly, skip explicit "shortlist that one" commands — just let the applicant verbally note interest, and manually read it back at the end as "confirmed" for the demo.

## 6. What to Say to Judges

Frame the three-part differentiation clearly: this isn't a chatbot reciting job titles from memory — it's grounded in live-scraped real postings, it builds a structured applicant profile from unstructured speech (no forms), and it lets the applicant have an actual back-and-forth conversation to narrow down his shortlist before ever making a call. That combination — voice-native intake, live data grounding, and conversational shortlisting — isn't something a generic ChatGPT/Claude voice session does out of the box.

## 7. Open Questions to Resolve Before/During Build

- Which specific blue-collar job portal/source will Anakin scrape? (Needs to be locked in during pre-build prep.)
- What are the exact profile fields the Extractor should capture — is "physical ability" sensitive enough to need careful prompt framing (e.g., focus on job-relevant capability, not health details)?
- Language: does the full loop need to support multiple applicant languages for the demo, or is one language sufficient to prove the concept?
- N (shortlist size): confirm 5 is the right balance of usefulness vs. TTS readback length.