"""Grounded summaries via gemini-3.7-flash.

The model receives only the already-ranked jobs plus computed facts. It writes
prose; it never selects, reorders, or adds a job.
"""

import json
import os
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = "gemini-3.7-flash"
_client = None

SYSTEM = """You explain already-shortlisted job listings to a blue-collar worker in India.

Rules, without exception:
- Use ONLY the facts given to you. Never invent or infer an employer, salary, shift,
  benefit, contact detail, phone number, or URL.
- Do not reorder, add, or drop jobs. Return exactly one object per job given, in the
  same order, with the same posting_id.
- If something is missing, say "not stated" — never guess and never call a listing a scam.
- Write plainly, for someone who will HEAR this read aloud. Short sentences. No markdown.

Return ONLY a JSON array, one object per job:
[{"posting_id": "<unchanged>", "summary": "<1-2 spoken sentences>",
  "match_reasons": ["<short grounded reason>", "<second reason>"]}]"""


def client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _brief(s: dict, comparison: str) -> dict:
    f = s["facts"]
    return {
        "posting_id": s["posting"]["posting_id"],
        "title": s["posting"]["raw_title"],
        "employer": f["employer"],
        "location": f["location"],
        "pay": (f"₹{f['salary_min']:,.0f}"
                + (f" to ₹{f['salary_max']:,.0f}" if f["salary_max"] != f["salary_min"] else "")
                + (f" per {f['salary_unit']}" if f["salary_unit"] else "")) if f["salary_min"] else None,
        "shift": f["shift"],
        "benefits": f["benefits"],
        "pay_vs_market": comparison,
        "match_score": s["match_score"],
        "why_it_scored": s["reasons"],
        "not_stated": s["missing_fields"],
    }


def summarize(scored: list[dict], comparisons: list[str]) -> list[dict]:
    payload = [_brief(s, c) for s, c in zip(scored, comparisons)]
    resp = client().models.generate_content(
        model=MODEL,
        contents=json.dumps(payload, ensure_ascii=False, indent=2),
        config={"system_instruction": SYSTEM, "temperature": 0.2,
                "response_mime_type": "application/json"},
    )
    return _parse(resp.text, payload)


def _parse(text: str, payload: list[dict]) -> list[dict]:
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    try:
        out = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            raise
        out = json.loads(m.group(0))
    by_id = {o.get("posting_id"): o for o in out}
    return [by_id.get(p["posting_id"], {}) for p in payload]
