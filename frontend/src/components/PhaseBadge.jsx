// Marks which parts of the demo hit a real backend vs. a client-side stand-in,
// so it stays honest about what's wired vs. mocked while the team builds in parallel.
export default function PhaseBadge({ kind, children }) {
  return <span className={`phase-badge phase-badge--${kind}`}>{children}</span>
}
