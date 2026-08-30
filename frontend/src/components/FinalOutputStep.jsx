import { useEffect, useState } from 'react'
import { getSessionState } from '../api.js'
import { matchColor, MATCH_COLOR_LABEL, PAY_COMPARISON_LABEL } from '../utils/matchColor.js'
import PhaseBadge from './PhaseBadge.jsx'

export default function FinalOutputStep({ applicantId, sessionId, onStartOver }) {
  const [status, setStatus] = useState('loading') // loading | done | error
  const [error, setError] = useState(null)
  const [finalOutput, setFinalOutput] = useState(null)

  useEffect(() => {
    let cancelled = false
    getSessionState(sessionId)
      .then((state) => {
        if (cancelled) return
        const byId = new Map(state.postings.map((p) => [p.posting_id, p]))
        const shortlisted_postings = state.shortlisted_ids
          .map((id) => byId.get(id))
          .filter(Boolean)
        setFinalOutput({
          applicant_id: applicantId,
          shortlisted_postings,
          shortlisted_at: new Date().toISOString(),
        })
        setStatus('done')
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
  }, [sessionId, applicantId])

  if (status === 'loading') {
    return (
      <section className="card">
        <div className="loading-row">
          <span className="spinner" aria-hidden />
          Building your final shortlist...
        </div>
      </section>
    )
  }

  if (status === 'error') {
    return (
      <section className="card">
        <p className="hint hint--error">Couldn't load your shortlist: {error}</p>
      </section>
    )
  }

  const { shortlisted_postings, shortlisted_at } = finalOutput

  return (
    <section className="card card--wide">
      <div className="card__header">
        <h2>Your shortlist</h2>
        <PhaseBadge kind="live">Phase 6 — built from live Phase 5 session</PhaseBadge>
      </div>

      {shortlisted_postings.length === 0 ? (
        <p className="muted">
          You didn't mark any postings as interesting yet. Go back and say "shortlist that one"
          or tap "Shortlist this" on a posting you like.
        </p>
      ) : (
        <>
          <p className="muted">
            Ready at {new Date(shortlisted_at).toLocaleString()} — call these employers directly.
          </p>
          <div className="final-list">
            {shortlisted_postings.map((p) => {
              const color = matchColor(p.match_score)
              const payNote = PAY_COMPARISON_LABEL[p.pay_comparison]
              return (
                <article key={p.posting_id} className="final-card">
                  <div className="final-card__title">
                    <span
                      className={`match-swatch match-swatch--${color}`}
                      title={MATCH_COLOR_LABEL[color]}
                      aria-label={MATCH_COLOR_LABEL[color]}
                    />
                    <h3>{p.title}</h3>
                  </div>
                  <p className="final-card__employer">
                    {p.employer || 'Employer not stated'} · {p.location || 'Location not stated'}
                  </p>
                  <div className="final-card__grid">
                    <div>
                      <span className="final-card__label">Pay</span>
                      <span className="final-card__value">{p.pay || 'Not stated'}</span>
                    </div>
                    <div className="final-card__contact">
                      <span className="final-card__label">Contact / apply</span>
                      <span className="final-card__value final-card__value--contact">
                        {p.contact_method || 'Not stated — see source link'}
                      </span>
                    </div>
                  </div>
                  {payNote && <p className="hint">{payNote}</p>}
                  <p className="final-card__summary">{p.summary}</p>
                  {(p.shift || p.benefits?.length > 0) && (
                    <p className="posting-card__meta">
                      {p.shift && <span className="chip">{p.shift} shift</span>}
                      {p.benefits?.map((b) => (
                        <span className="chip" key={b}>
                          {b}
                        </span>
                      ))}
                    </p>
                  )}
                  {p.match_reasons?.length > 0 && (
                    <ul className="posting-card__tags posting-card__tags--good">
                      {p.match_reasons.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>
                  )}
                  {p.warnings?.length > 0 && (
                    <ul className="posting-card__tags posting-card__tags--warning">
                      {p.warnings.map((w) => (
                        <li key={w}>{w}</li>
                      ))}
                    </ul>
                  )}
                  {p.questions_to_ask?.length > 0 && (
                    <details className="posting-card__questions">
                      <summary>Good questions to ask</summary>
                      <ul>
                        {p.questions_to_ask.map((q) => (
                          <li key={q}>{q}</li>
                        ))}
                      </ul>
                    </details>
                  )}
                  <a href={p.source_url} target="_blank" rel="noreferrer">
                    View original posting
                  </a>
                </article>
              )
            })}
          </div>
        </>
      )}

      <div className="actions">
        <button className="btn btn--primary" onClick={onStartOver}>
          Start over
        </button>
      </div>
    </section>
  )
}
