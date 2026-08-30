import { useState } from 'react'
import { extractProfile, transcribeAudio } from '../api.js'
import { APPLICANT_ID } from '../data/profile.js'
import { useMicRecorder } from '../utils/useMicRecorder.js'
import PhaseBadge from './PhaseBadge.jsx'

const PROMPT =
  'Please tell me about yourself — your work experience, your skills, where ' +
  "you're located, your age, any physical limitations, when you're available " +
  'to start, and what pay you are looking for.'

export default function IntakeStep({ transcript, onChange, onNext }) {
  const [touched, setTouched] = useState(false)
  const [language, setLanguage] = useState('en-IN')
  const [busy, setBusy] = useState(false)
  const [busyLabel, setBusyLabel] = useState('')
  const [error, setError] = useState(null)
  const mic = useMicRecorder()
  const canContinue = transcript.trim().length > 0 && !busy

  const handleMicClick = async () => {
    if (busy) return
    if (!mic.recording) {
      setError(null)
      await mic.start()
      return
    }
    const blob = await mic.stop()
    if (!blob || blob.size === 0) return
    setBusy(true)
    setBusyLabel('Transcribing your recording...')
    setError(null)
    try {
      const result = await transcribeAudio(APPLICANT_ID, blob)
      onChange(result.transcript_en)
      setLanguage(result.language || 'en-IN')
      setTouched(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const handleContinue = async () => {
    if (!canContinue) return
    setBusy(true)
    setBusyLabel('Building your job-search profile...')
    setError(null)
    try {
      const profile = await extractProfile({
        applicant_id: APPLICANT_ID,
        language,
        transcript_en: transcript,
      })
      onNext(profile)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <div className="card__header">
        <h2>Tell us about yourself</h2>
        <PhaseBadge kind="live">Phase 1/2 — live backend</PhaseBadge>
      </div>
      <p className="prompt-box">{PROMPT}</p>

      <div className="ask-row">
        <button
          type="button"
          className={`btn btn--mic ${mic.recording ? 'btn--mic-active' : ''}`}
          onClick={handleMicClick}
          disabled={busy}
        >
          {mic.recording ? '⏹ Stop & transcribe' : '🎤 Record your answer'}
        </button>
      </div>

      <textarea
        className="textarea"
        rows={7}
        placeholder="e.g. I've been doing electrical work on construction sites for about four years, based in Marathahalli, Bangalore. I'm 29, can handle standing shifts, available immediately, looking for at least ₹800 a day..."
        value={transcript}
        onChange={(e) => onChange(e.target.value)}
        onBlur={() => setTouched(true)}
        disabled={busy}
      />
      {busy && (
        <div className="loading-row">
          <span className="spinner" aria-hidden />
          {busyLabel}
        </div>
      )}
      {touched && !canContinue && !busy && (
        <p className="hint hint--error">Say a little about yourself to continue.</p>
      )}
      {error && <p className="hint hint--error">{error}</p>}
      {mic.error && <p className="hint hint--error">{mic.error}</p>}

      <div className="actions">
        <button className="btn btn--primary" disabled={!canContinue} onClick={handleContinue}>
          Continue
        </button>
      </div>
    </section>
  )
}
