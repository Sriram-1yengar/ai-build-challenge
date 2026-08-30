import assert from "node:assert/strict";
import test from "node:test";
import { extractProfile } from "../src/profile-extraction.js";

function mockClient(...outputs) {
  const calls = [];
  return { calls, models: { async generateContent(request) { calls.push(request); return { text: outputs[calls.length - 1] }; } } };
}

function profile(overrides = {}) {
  return {
    applicant_id: "worker-42", language: "hi-IN", skills: [], years_experience: null,
    location: { raw_text: "", area: null, city: null }, age: null,
    physical_capability_notes: [], availability: null, min_pay_expectation: null,
    pay_unit: null, notes: null, ...overrides,
  };
}

test("extracts a clean structured transcript with Gemini 3.6 Flash", async () => {
  const expected = profile({ skills: ["electrical work"], years_experience: 5, location: { raw_text: "Koramangala, Bangalore", area: "Koramangala", city: "Bangalore" }, age: 31, availability: "next Monday", min_pay_expectation: 900, pay_unit: "per day" });
  const client = mockClient(JSON.stringify(expected));
  assert.deepEqual(await extractProfile({ applicant_id: "worker-42", language: "hi-IN", transcript_en: "I am 31, an electrician with five years experience in Koramangala, Bangalore. I can start next Monday and need 900 rupees daily." }, { client }), expected);
  assert.equal(client.calls[0].model, "gemini-3.6-flash");
});

test("handles a rambling transcript", async () => {
  const expected = profile({ skills: ["cooking", "kitchen assistance"], years_experience: 2, location: { raw_text: "over in Dharavi, Mumbai", area: "Dharavi", city: "Mumbai" }, physical_capability_notes: ["comfortable with standing shifts"], availability: "immediately" });
  const client = mockClient(JSON.stringify(expected));
  assert.deepEqual(await extractProfile({ applicant_id: "worker-42", language: "hi-IN", transcript_en: "Well, I helped in a restaurant for maybe two years, making food. I stay over in Dharavi, Mumbai. Standing all shift is okay and I can join right now." }, { client }), expected);
});

test("uses nulls for a sparse transcript", async () => {
  const expected = profile({ skills: ["painting"], location: { raw_text: "Pune", area: null, city: "Pune" } });
  const client = mockClient(JSON.stringify(expected));
  const actual = await extractProfile({ applicant_id: "worker-42", language: "hi-IN", transcript_en: "I do painting work in Pune." }, { client });
  assert.deepEqual(actual, expected);
  assert.equal(actual.min_pay_expectation, null);
});

test("repairs malformed JSON once", async () => {
  const expected = profile({ skills: ["driving"] });
  const client = mockClient("not json", JSON.stringify(expected));
  assert.deepEqual(await extractProfile({ applicant_id: "worker-42", language: "hi-IN", transcript_en: "I am a driver." }, { client }), expected);
  assert.equal(client.calls.length, 2);
});

test("rejects changed applicant IDs", async () => {
  const wrong = profile({ applicant_id: "invented" });
  const client = mockClient(JSON.stringify(wrong), JSON.stringify(wrong));
  await assert.rejects(extractProfile({ applicant_id: "worker-42", language: "hi-IN", transcript_en: "I am a driver." }, { client }), /passed through unchanged/);
});
