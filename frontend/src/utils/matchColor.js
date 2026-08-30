// Buckets a 0-100 match_score into the same green/yellow/red bands the spoken
// guide describes, so a non-reading applicant can act on colour alone.
export function matchColor(score) {
  if (score == null) return 'yellow'
  if (score >= 75) return 'green'
  if (score >= 50) return 'yellow'
  return 'red'
}

export const MATCH_COLOR_LABEL = {
  green: 'Strong match',
  yellow: 'Worth a look',
  red: 'May not fit',
}

export const PAY_COMPARISON_LABEL = {
  above_market: 'Pay looks above average for this area',
  near_market: 'Pay looks about average for this area',
  below_market: 'Pay looks below average for this area',
  unknown: null,
}
