export const jobSearchProfileSchema = {
  type: "object", additionalProperties: false,
  required: ["applicant_id", "language", "skills", "years_experience", "location", "age", "physical_capability_notes", "availability", "min_pay_expectation", "pay_unit", "notes"],
  properties: {
    applicant_id: { type: "string" }, language: { type: "string" },
    skills: { type: "array", items: { type: "string" } },
    years_experience: { anyOf: [{ type: "number" }, { type: "null" }] },
    location: { type: "object", additionalProperties: false, required: ["raw_text", "area", "city"], properties: {
      raw_text: { type: "string" }, area: { anyOf: [{ type: "string" }, { type: "null" }] }, city: { anyOf: [{ type: "string" }, { type: "null" }] },
    } },
    age: { anyOf: [{ type: "number" }, { type: "null" }] },
    physical_capability_notes: { type: "array", items: { type: "string" } },
    availability: { anyOf: [{ type: "string" }, { type: "null" }] },
    min_pay_expectation: { anyOf: [{ type: "number" }, { type: "null" }] },
    pay_unit: { anyOf: [{ type: "string" }, { type: "null" }] },
    notes: { anyOf: [{ type: "string" }, { type: "null" }] },
  },
};

const profileKeys = jobSearchProfileSchema.required;

export function validateInput(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) return ["body must be an object"];
  const errors = [];
  for (const key of ["applicant_id", "language", "transcript_en"]) if (typeof input[key] !== "string" || !input[key].trim()) errors.push(`${key} must be a non-empty string`);
  if (typeof input.applicant_id === "string" && input.applicant_id.length > 100) errors.push("applicant_id must be at most 100 characters");
  if (typeof input.transcript_en === "string" && input.transcript_en.length > 20_000) errors.push("transcript_en must be at most 20000 characters");
  return errors;
}

export function validateProfile(profile, source) {
  if (!profile || typeof profile !== "object" || Array.isArray(profile)) return ["output must be an object"];
  const errors = [];
  const extras = Object.keys(profile).filter((key) => !profileKeys.includes(key));
  const missing = profileKeys.filter((key) => !(key in profile));
  if (extras.length) errors.push(`unexpected fields: ${extras.join(", ")}`);
  if (missing.length) errors.push(`missing fields: ${missing.join(", ")}`);
  if (profile.applicant_id !== source.applicant_id) errors.push("applicant_id was not passed through unchanged");
  if (profile.language !== source.language) errors.push("language was not passed through unchanged");
  if (!Array.isArray(profile.skills) || profile.skills.some((item) => typeof item !== "string" || !item.trim())) errors.push("skills must be an array of non-empty strings");
  if (!Array.isArray(profile.physical_capability_notes) || profile.physical_capability_notes.some((item) => typeof item !== "string" || !item.trim())) errors.push("physical_capability_notes must be an array of non-empty strings");
  for (const key of ["years_experience", "age", "min_pay_expectation"]) if (profile[key] !== null && (typeof profile[key] !== "number" || !Number.isFinite(profile[key]) || profile[key] < 0)) errors.push(`${key} must be a non-negative number or null`);
  for (const key of ["availability", "pay_unit", "notes"]) if (profile[key] !== null && typeof profile[key] !== "string") errors.push(`${key} must be a string or null`);
  const location = profile.location;
  if (!location || typeof location !== "object" || Array.isArray(location)) errors.push("location must be an object");
  else {
    const locationKeys = ["raw_text", "area", "city"];
    if (Object.keys(location).some((key) => !locationKeys.includes(key)) || locationKeys.some((key) => !(key in location))) errors.push("location must contain exactly raw_text, area, and city");
    if (typeof location.raw_text !== "string") errors.push("location.raw_text must be a string");
    for (const key of ["area", "city"]) if (location[key] !== null && typeof location[key] !== "string") errors.push(`location.${key} must be a string or null`);
  }
  return errors;
}
