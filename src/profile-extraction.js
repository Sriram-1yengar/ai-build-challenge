import { jobSearchProfileSchema, validateInput, validateProfile } from "./profile-schema.js";

export const DEFAULT_MODEL = "gemini-3.6-flash";

const SYSTEM_PROMPT = `You extract a structured job-search profile from a blue-collar job applicant's spoken self-description. The transcript may be unstructured, rambling, or missing information. Extract only what is stated or clearly implied. Do not invent details.

Rules:
- Normalize skills to job/trade terms such as driving, electrical work, construction labor, plumbing, painting, or cooking.
- Keep physical_capability_notes strictly job-relevant and factual. Never infer health, medical, or disability information.
- Use null for an unmentioned scalar field and an empty array for an unmentioned list.
- Preserve applicant_id and language exactly as supplied.
- location.raw_text must be the verbatim location phrase, or an empty string when no location was stated.
- Return JSON only.`;

function responseText(response) {
  const text = typeof response?.text === "function" ? response.text() : response?.text;
  if (typeof text !== "string" || !text.trim()) throw new Error("Gemini returned an empty response");
  return text.trim();
}

function parseAndValidate(raw, input) {
  let profile;
  try { profile = JSON.parse(raw); }
  catch { throw Object.assign(new Error("Gemini returned invalid JSON"), { repairable: true }); }
  const errors = validateProfile(profile, input);
  if (errors.length) throw Object.assign(new Error(`Gemini output failed validation: ${errors.join("; ")}`), { repairable: true });
  return profile;
}

export async function extractProfile(input, { client, model = DEFAULT_MODEL } = {}) {
  const errors = validateInput(input);
  if (errors.length) throw Object.assign(new Error(errors.join("; ")), { status: 400 });
  if (!client) throw new Error("A Gemini client is required");
  const config = { responseMimeType: "application/json", responseJsonSchema: jobSearchProfileSchema, temperature: 0 };
  const contents = `${SYSTEM_PROMPT}\n\nTranscript:\n\"\"\"\n${input.transcript_en}\n\"\"\"\n\napplicant_id: ${JSON.stringify(input.applicant_id)}\nlanguage: ${JSON.stringify(input.language)}`;
  const first = await client.models.generateContent({ model, contents, config });
  const raw = responseText(first);
  try { return parseAndValidate(raw, input); }
  catch (error) {
    if (!error.repairable) throw error;
    const repair = await client.models.generateContent({ model, contents: `${SYSTEM_PROMPT}\n\nFix the following output to be valid JSON matching the required schema. Preserve applicant_id and language exactly. Return JSON only.\n\nInvalid output:\n${raw}`, config });
    return parseAndValidate(responseText(repair), input);
  }
}
