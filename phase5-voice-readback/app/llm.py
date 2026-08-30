import json
import os

from google import genai
from google.genai import types

from app.models import ConversationTurn, ShortlistPosting

_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=api_key)
    return _client


def _generate_json(prompt: str, retries: int = 1) -> dict | list:
    client = _get_client()
    response = client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    text = response.text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if retries <= 0:
            raise
        repair_prompt = (
            "The following text was supposed to be valid JSON but failed to parse. "
            "Fix it to be valid JSON matching the same intended structure. "
            "Return ONLY the corrected JSON, no other text.\n\n"
            f"{text}"
        )
        return _generate_json(repair_prompt, retries=retries - 1)


GUIDE_TEXT = (
    "Before I start, here's how this works. I'll read out each job one at a time. "
    "Every job also has a colour on your screen: green means it looks like a strong "
    "match for you, yellow means it's worth a look, and red means it may not be the "
    "best fit. While I'm talking about a job, its colour will light up on screen -- "
    "if it sounds good to you, just tap that colour."
)

SEGMENT_PROMPT_TEMPLATE = """\
Convert each of these job postings into a short, natural spoken blurb, as if a
helpful assistant is describing it aloud to someone over the phone, one at a time.
Keep each blurb to one short paragraph, in plain everyday language -- no jargon,
no field names like "match_score" or "pay_comparison". Weave in anything that
stands out as a good reason to consider it, or anything worth double-checking,
using the match_reasons/warnings/missing_fields on each posting, without naming
those fields directly. Do not add information not present in the posting.

Postings:
{postings_json}

Return ONLY valid JSON: a list of objects, one per posting, in the same order given:
[{{"posting_id": "<id>", "text": "<spoken-style blurb for that posting>"}}, ...]
"""

QA_PROMPT_TEMPLATE = """\
You are a helpful voice assistant helping a job applicant review a shortlist of
job postings he just heard read aloud. Answer his question using ONLY the
information in the postings below -- do not use outside knowledge or invent details.
If the answer isn't in the postings, say so plainly rather than guessing.

If the applicant expresses interest in, or asks to shortlist, a specific posting,
include its posting_id in "referenced_posting_ids" and note the interest in your
answer.

Postings:
{postings_json}

Conversation so far:
{history_json}

Applicant's latest question:
"{question_text}"

Return ONLY valid JSON:
{{
  "answer_text": "<spoken-style answer, concise, natural>",
  "referenced_posting_ids": ["<posting_id>", ...],
  "applicant_expressed_interest": true | false
}}
"""


def rewrite_segments_for_speech(postings: list[ShortlistPosting]) -> list[dict]:
    """Returns one spoken blurb per posting, in the same order as `postings`, so
    the caller can synthesize + play them one at a time and know which posting
    is being narrated at any given moment (falls back to the posting's own
    summary if the model drops an id or returns malformed JSON).
    """
    postings_json = json.dumps([p.model_dump() for p in postings], ensure_ascii=False, indent=2)
    prompt = SEGMENT_PROMPT_TEMPLATE.format(postings_json=postings_json)
    result = _generate_json(prompt)
    by_id = {
        item.get("posting_id"): item.get("text", "")
        for item in result
        if isinstance(item, dict)
    }
    return [
        {"posting_id": p.posting_id, "text": by_id.get(p.posting_id) or p.summary}
        for p in postings
    ]


def answer_question(
    postings: list[ShortlistPosting],
    history: list[ConversationTurn],
    question_text: str,
) -> dict:
    postings_json = json.dumps([p.model_dump() for p in postings], ensure_ascii=False, indent=2)
    history_json = json.dumps([t.model_dump() for t in history], ensure_ascii=False, indent=2)
    prompt = QA_PROMPT_TEMPLATE.format(
        postings_json=postings_json,
        history_json=history_json,
        question_text=question_text,
    )
    result = _generate_json(prompt)

    valid_ids = {p.posting_id for p in postings}
    referenced = [pid for pid in result.get("referenced_posting_ids", []) if pid in valid_ids]

    return {
        "answer_text": result.get("answer_text", ""),
        "referenced_posting_ids": referenced,
        "applicant_expressed_interest": bool(result.get("applicant_expressed_interest", False)),
    }
