import { matchColor, MATCH_COLOR_LABEL, PAY_COMPARISON_LABEL } from '../utils/matchColor.js'

export default function PostingCard({ posting, shortlisted, highlighted, isNarrating, onToggleShortlist }) {
  const color = matchColor(posting.match_score)
  const payNote = PAY_COMPARISON_LABEL[posting.pay_comparison]

  return (
    <article
      className={`posting-card${highlighted ? ' posting-card--highlighted' : ''}${
        isNarrating ? ' posting-card--narrating' : ''
      }`}
    >
      <header className="posting-card__header">
        {onToggleShortlist && (
          <button
            type="button"
            className={`match-swatch match-swatch--${color}${isNarrating ? ' match-swatch--active' : ''}`}
            onClick={() => onToggleShortlist(posting.posting_id, !shortlisted)}
            aria-pressed={shortlisted}
            aria-label={`${MATCH_COLOR_LABEL[color]}. Tap to ${
              shortlisted ? 'remove from' : 'add to'
            } your shortlist.`}
            title={MATCH_COLOR_LABEL[color]}
          >
            {shortlisted && <span className="match-swatch__check">✓</span>}
          </button>
        )}
        <div className="posting-card__title">
          <h3>{posting.title}</h3>
          {posting.pay && <span className="pay-chip">{posting.pay}</span>}
        </div>
      </header>

      <p className="posting-card__employer">
        {posting.employer || 'Employer not stated'} · {posting.location || 'Location not stated'}
      </p>

      <p className="posting-card__summary">{posting.summary}</p>

      {payNote && <p className="hint">{payNote}</p>}

      {posting.match_reasons?.length > 0 && (
        <ul className="posting-card__tags posting-card__tags--good">
          {posting.match_reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}

      {(posting.shift || posting.benefits?.length > 0) && (
        <p className="posting-card__meta">
          {posting.shift && <span className="chip">{posting.shift} shift</span>}
          {posting.benefits?.map((b) => (
            <span className="chip" key={b}>
              {b}
            </span>
          ))}
        </p>
      )}

      {posting.requirements?.length > 0 && (
        <ul className="posting-card__requirements">
          {posting.requirements.map((req) => (
            <li key={req}>{req}</li>
          ))}
        </ul>
      )}

      {posting.warnings?.length > 0 && (
        <ul className="posting-card__tags posting-card__tags--warning">
          {posting.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}

      {posting.missing_fields?.length > 0 && (
        <p className="hint">Couldn't confirm: {posting.missing_fields.join(', ')}</p>
      )}

      {posting.questions_to_ask?.length > 0 && (
        <details className="posting-card__questions">
          <summary>Good questions to ask</summary>
          <ul>
            {posting.questions_to_ask.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </details>
      )}

      <p className="posting-card__contact">
        <strong>Contact:</strong> {posting.contact_method || 'Not stated — see source link'}
      </p>
      <a className="posting-card__link" href={posting.source_url} target="_blank" rel="noreferrer">
        View source
      </a>

      {onToggleShortlist && (
        <button
          type="button"
          className={`btn btn--small ${shortlisted ? 'btn--accent' : 'btn--ghost'}`}
          onClick={() => onToggleShortlist(posting.posting_id, !shortlisted)}
        >
          {shortlisted ? '✓ Shortlisted' : 'Shortlist this'}
        </button>
      )}
    </article>
  )
}
