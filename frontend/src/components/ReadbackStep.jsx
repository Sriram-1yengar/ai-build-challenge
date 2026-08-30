import { useEffect, useRef, useState } from 'react'
import { askAudio, askText, setShortlisted, startSession } from '../api.js'
import { playBase64WavChunks, playReadbackSequence } from '../utils/audio.js'
import { useMicRecorder } from '../utils/useMicRecorder.js'
import PhaseBadge from './PhaseBadge.jsx'
import PostingCard from './PostingCard.jsx'

export default function ReadbackStep({ profile, postings, onBack, onDone }) {
  const [status, setStatus] = useState('starting') // starting | ready | error
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [turns, setTurns] = useState([])
  const [shortlistedIds, setShortlistedIds] = useState(new Set())
  const [referencedIds, setReferencedIds] = useState([])
  const [narratingId, setNarratingId] = useState(null)
  const [questionText, setQuestionText] = useState('')
  const [busy, setBusy] = useState(false)
  const mic = useMicRecorder()
  const logEndRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    setStatus('starting')
    startSession(postings, profile.language)
      .then(async (res) => {
        if (cancelled) return
        setSessionId(res.session_id)
        setTurns([{ role: 'agent', text: res.guide_text }])
        setStatus('ready')
        try {
          await playBase64WavChunks(res.guide_audio_base64)
          if (cancelled) return
          await playReadbackSequence(res.postings, (segment) => {
            if (cancelled) return
            setNarratingId(segment.posting_id)
            setTurns((t) => [...t, { role: 'agent', text: segment.text }])
          })
        } catch {
          // autoplay can be blocked without a user gesture — the text is already
          // shown, and there's no replay control for the readback yet
        } finally {
          if (!cancelled) setNarratingId(null)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setStatus('error')
        }
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [turns])

  const applyResult = (result) => {
    setTurns((t) => [
      ...t,
      { role: 'applicant', text: result.question_text },
      { role: 'agent', text: result.answer_text },
    ])
    setReferencedIds(result.referenced_posting_ids)
    setShortlistedIds(new Set(result.shortlisted_ids))
    playBase64WavChunks(result.answer_audio_base64).catch(() => {})
  }

  const handleSendText = async () => {
    const text = questionText.trim()
    if (!text || busy) return
    setBusy(true)
    setError(null)
    setQuestionText('')
    try {
      const result = await askText(sessionId, text)
      applyResult(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const handleMicClick = async () => {
    if (busy) return
    if (!mic.recording) {
      await mic.start()
      return
    }
    const blob = await mic.stop()
    if (!blob || blob.size === 0) return
    setBusy(true)
    setError(null)
    try {
      const result = await askAudio(sessionId, blob)
      applyResult(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const handleToggleShortlist = async (postingId, shortlisted) => {
    try {
      const state = await setShortlisted(sessionId, postingId, shortlisted)
      setShortlistedIds(new Set(state.shortlisted_ids))
    } catch (err) {
      setError(err.message)
    }
  }

  if (status === 'starting') {
    return (
      <section className="card">
        <div className="loading-row">
          <span className="spinner" aria-hidden />
          Starting the voice session and generating the readback...
        </div>
      </section>
    )
  }

  if (status === 'error') {
    return (
      <section className="card">
        <p className="hint hint--error">
          Couldn't start the voice session: {error}. Check the Phase 5 backend is running on
          port 8005 and <code>GEMINI_API_KEY</code> / <code>SARVAM_API_KEY</code> are set in the
          root <code>.env</code>.
        </p>
        <div className="actions">
          <button className="btn btn--ghost" onClick={onBack}>
            Back
          </button>
        </div>
      </section>
    )
  }

  return (
    <section className="card card--wide">
      <div className="card__header">
        <h2>Hear & discuss your shortlist</h2>
        <PhaseBadge kind="live">Phase 5 — live backend</PhaseBadge>
      </div>

      <div className="readback-layout">
        <div className="chat-panel">
          <div className="chat-log">
            {turns.map((turn, i) => (
              <div key={i} className={`chat-turn chat-turn--${turn.role}`}>
                <span className="chat-turn__role">
                  {turn.role === 'applicant' ? 'You' : 'Assistant'}
                </span>
                <p>{turn.text}</p>
              </div>
            ))}
            {busy && (
              <div className="chat-turn chat-turn--agent chat-turn--pending">
                <span className="chat-turn__role">Assistant</span>
                <p>Thinking...</p>
              </div>
            )}
            <div ref={logEndRef} />
          </div>

          {error && <p className="hint hint--error">{error}</p>}
          {mic.error && <p className="hint hint--error">{mic.error}</p>}

          <div className="ask-row">
            <button
              type="button"
              className={`btn btn--mic ${mic.recording ? 'btn--mic-active' : ''}`}
              onClick={handleMicClick}
              disabled={busy}
            >
              {mic.recording ? '⏹ Stop & ask' : '🎤 Ask by voice'}
            </button>
          </div>

          <div className="ask-row">
            <input
              className="input"
              placeholder="Debug: type a question instead (e.g. which one pays more)"
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendText()}
              disabled={busy}
            />
            <button className="btn btn--ghost" onClick={handleSendText} disabled={busy}>
              Send
            </button>
          </div>
        </div>

        <div className="postings-panel">
          <p className="muted">
            Green means a strong match, yellow is worth a look, red may not fit — tap the
            colour to shortlist a job, any time.
          </p>
          <div className="posting-grid posting-grid--stacked">
            {postings.map((p) => (
              <PostingCard
                key={p.posting_id}
                posting={p}
                shortlisted={shortlistedIds.has(p.posting_id)}
                highlighted={referencedIds.includes(p.posting_id)}
                isNarrating={p.posting_id === narratingId}
                onToggleShortlist={handleToggleShortlist}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="actions">
        <button className="btn btn--ghost" onClick={onBack}>
          Back
        </button>
        <button className="btn btn--primary" onClick={() => onDone(sessionId)}>
          I'm done — show my shortlist
        </button>
      </div>
    </section>
  )
}
