// Hardcoded per structure.md ground rule 6: every phase can be tested/demoed
// standalone using this id until Phase 1 (real voice intake) is wired in.
export const APPLICANT_ID = 'demo_applicant_1'

export function emptyProfile() {
  return {
    applicant_id: APPLICANT_ID,
    language: 'en-IN',
    skills: [],
    years_experience: null,
    location: { raw_text: '', area: null, city: null },
    age: null,
    physical_capability_notes: [],
    availability: null,
    min_pay_expectation: null,
    pay_unit: null,
    notes: null,
  }
}
