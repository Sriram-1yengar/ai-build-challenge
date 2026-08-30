import { useEffect, useState } from 'react'
import { searchJobs } from '../api.js'
import PhaseBadge from './PhaseBadge.jsx'
import PostingCard from './PostingCard.jsx'

export default function SearchStep({ profile, onFound, onBack, onNext }) {
  const [phase, setPhaseState] = useState('loading') // loading | done | error
  const [postings, setPostings] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setPhaseState('loading')
    setError(null)

    searchJobs(profile)
      .then((result) => {
        if (cancelled) return
        setPostings(result.postings)
        onFound(result.postings)
        setPhaseState('done')
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setPhaseState('error')
        }
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <section className="card">
      <div className="card__header">
        <h2>Job search</h2>
        <PhaseBadge kind="live">Phase 3/4 — live backend</PhaseBadge>
      </div>

      {phase === 'loading' && (
        <div className="loading-row">
          <span className="spinner" aria-hidden />
          Searching job portals for {profile.skills.join(', ') || 'matching roles'} near{' '}
          {profile.location.area || profile.location.city || 'your area'}...
        </div>
      )}

      {phase === 'error' && <p className="hint hint--error">Couldn't search for jobs: {error}</p>}

      {phase === 'done' && postings.length === 0 && (
        <p className="muted">No matching postings were found for this profile right now.</p>
      )}

      {phase === 'done' && postings.length > 0 && (
        <>
          <p className="muted">Found {postings.length} postings that look like a good fit.</p>
          <div className="posting-grid">
            {postings.map((p) => (
              <PostingCard key={p.posting_id} posting={p} />
            ))}
          </div>
        </>
      )}

      <div className="actions">
        <button className="btn btn--ghost" onClick={onBack}>
          Back
        </button>
        <button className="btn btn--primary" disabled={phase !== 'done' || postings.length === 0} onClick={onNext}>
          Hear the shortlist
        </button>
      </div>
    </section>
  )
}
