// Talks to three backends. Locally, the Phase 1/2 Node server is reached via
// the Vite dev proxy at /api/* (vite.config.js) since it sends no CORS headers
// of its own -- that proxy doesn't exist in a deployed static build, so
// VITE_INTAKE_API_BASE must be set to that service's real URL for prod
// (see render.yaml). The other two set their own CORS headers and are always
// called by absolute URL.
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8005'
const SEARCH_API_BASE = import.meta.env.VITE_SEARCH_API_BASE || 'http://localhost:8003'
const INTAKE_API_BASE = import.meta.env.VITE_INTAKE_API_BASE || ''

async function asJson(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      // FastAPI (Phase 5) uses {detail}, the Node server (Phase 1/2) uses {error}.
      detail = body.detail || body.error || detail
    } catch {
      // response wasn't JSON; fall back to statusText
    }
    throw new Error(detail)
  }
  return res.json()
}

// Phase 1: raw recorded audio -> { applicant_id, language, transcript_en }
export function transcribeAudio(applicantId, audioBlob) {
  return fetch(`${INTAKE_API_BASE}/api/transcribe`, {
    method: 'POST',
    headers: {
      'Content-Type': audioBlob.type || 'audio/webm',
      'X-Applicant-Id': applicantId,
    },
    body: audioBlob,
  }).then(asJson)
}

// Phase 2: { applicant_id, language, transcript_en } -> full JobSearchProfile
export function extractProfile({ applicant_id, language, transcript_en }) {
  return fetch(`${INTAKE_API_BASE}/api/extract-profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ applicant_id, language, transcript_en }),
  }).then(asJson)
}

// Phase 3 + 4: JobSearchProfile -> { postings: ShortlistPosting[], raw_postings, benchmark }
export function searchJobs(profile, useLlm = true) {
  return fetch(`${SEARCH_API_BASE}/api/job-search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile, use_llm: useLlm }),
  }).then(asJson)
}

export function startSession(postings, languageCode = 'en-IN') {
  return fetch(`${API_BASE}/session/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ postings, language_code: languageCode }),
  }).then(asJson)
}

export function askText(sessionId, questionText) {
  return fetch(`${API_BASE}/session/${sessionId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_text: questionText }),
  }).then(asJson)
}

export function askAudio(sessionId, audioBlob) {
  const form = new FormData()
  form.append('audio', audioBlob, 'question.webm')
  return fetch(`${API_BASE}/session/${sessionId}/ask-audio`, {
    method: 'POST',
    body: form,
  }).then(asJson)
}

export function setShortlisted(sessionId, postingId, shortlisted) {
  return fetch(`${API_BASE}/session/${sessionId}/shortlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ posting_id: postingId, shortlisted }),
  }).then(asJson)
}

export function getSessionState(sessionId) {
  return fetch(`${API_BASE}/session/${sessionId}/state`).then(asJson)
}
