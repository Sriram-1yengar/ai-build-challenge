const STEPS = [
  'Tell us about yourself',
  'Confirm your profile',
  'Job search',
  'Hear & discuss shortlist',
  'Your shortlist',
]

export default function StepIndicator({ current }) {
  return (
    <ol className="stepper">
      {STEPS.map((label, i) => {
        const state = i < current ? 'done' : i === current ? 'active' : 'upcoming'
        return (
          <li key={label} className={`stepper__item stepper__item--${state}`}>
            <span className="stepper__dot">{i < current ? '✓' : i + 1}</span>
            <span className="stepper__label">{label}</span>
          </li>
        )
      })}
    </ol>
  )
}
