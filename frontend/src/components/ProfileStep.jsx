import PhaseBadge from './PhaseBadge.jsx'

function updatePath(profile, path, value) {
  const next = { ...profile, location: { ...profile.location } }
  if (path[0] === 'location') {
    next.location[path[1]] = value
  } else {
    next[path[0]] = value
  }
  return next
}

function toListValue(text) {
  return text
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

export default function ProfileStep({ profile, onChange, onBack, onNext }) {
  const set = (path, value) => onChange(updatePath(profile, path, value))

  return (
    <section className="card">
      <div className="card__header">
        <h2>Confirm your profile</h2>
        <PhaseBadge kind="live">Phase 2 — live backend</PhaseBadge>
      </div>
      <p className="muted">
        Here's what we understood from what you said. Fix anything that's wrong or missing
        before we search for jobs.
      </p>

      <div className="form-grid">
        <label className="field">
          <span>Skills / trade (comma separated)</span>
          <input
            className="input"
            value={profile.skills.join(', ')}
            onChange={(e) => set(['skills'], toListValue(e.target.value))}
            placeholder="driving, construction labor"
          />
        </label>

        <label className="field">
          <span>Years of experience</span>
          <input
            className="input"
            type="number"
            min="0"
            value={profile.years_experience ?? ''}
            onChange={(e) => set(['years_experience'], e.target.value === '' ? null : Number(e.target.value))}
          />
        </label>

        <label className="field">
          <span>Age</span>
          <input
            className="input"
            type="number"
            min="0"
            value={profile.age ?? ''}
            onChange={(e) => set(['age'], e.target.value === '' ? null : Number(e.target.value))}
          />
        </label>

        <label className="field">
          <span>Location (area / neighborhood)</span>
          <input
            className="input"
            value={profile.location.area ?? ''}
            onChange={(e) => set(['location', 'area'], e.target.value || null)}
            placeholder="Whitefield"
          />
        </label>

        <label className="field">
          <span>City</span>
          <input
            className="input"
            value={profile.location.city ?? ''}
            onChange={(e) => set(['location', 'city'], e.target.value || null)}
            placeholder="Bangalore"
          />
        </label>

        <label className="field">
          <span>Availability</span>
          <input
            className="input"
            value={profile.availability ?? ''}
            onChange={(e) => set(['availability'], e.target.value || null)}
            placeholder="Immediately"
          />
        </label>

        <label className="field">
          <span>Minimum pay expected</span>
          <input
            className="input"
            type="number"
            min="0"
            value={profile.min_pay_expectation ?? ''}
            onChange={(e) =>
              set(['min_pay_expectation'], e.target.value === '' ? null : Number(e.target.value))
            }
          />
        </label>

        <label className="field">
          <span>Pay unit</span>
          <select
            className="input"
            value={profile.pay_unit ?? ''}
            onChange={(e) => set(['pay_unit'], e.target.value || null)}
          >
            <option value="">Not sure</option>
            <option value="per day">per day</option>
            <option value="per month">per month</option>
          </select>
        </label>

        <label className="field field--wide">
          <span>Physical capability notes (comma separated, job-relevant only)</span>
          <input
            className="input"
            value={profile.physical_capability_notes.join(', ')}
            onChange={(e) => set(['physical_capability_notes'], toListValue(e.target.value))}
            placeholder="comfortable with standing shifts, can lift up to 25kg"
          />
        </label>

        <label className="field field--wide">
          <span>What you told us (kept as-is)</span>
          <textarea
            className="textarea"
            rows={3}
            value={profile.notes ?? ''}
            onChange={(e) => set(['notes'], e.target.value || null)}
          />
        </label>
      </div>

      <div className="actions">
        <button className="btn btn--ghost" onClick={onBack}>
          Back
        </button>
        <button className="btn btn--primary" onClick={onNext}>
          Search for jobs
        </button>
      </div>
    </section>
  )
}
