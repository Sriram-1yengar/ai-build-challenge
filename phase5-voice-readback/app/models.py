from typing import Optional

from pydantic import BaseModel


class ShortlistPosting(BaseModel):
    posting_id: str
    title: str
    employer: Optional[str] = None
    location: Optional[str] = None
    pay: Optional[str] = None
    requirements: list[str] = []
    benefits: list[str] = []
    shift: Optional[str] = None  # "day" | "night" | "rotational" | "flexible" | None
    contact_method: Optional[str] = None
    source_url: str
    summary: str
    match_score: float
    match_reasons: list[str] = []
    pay_comparison: str  # "above_market" | "near_market" | "below_market" | "unknown"
    missing_fields: list[str] = []
    warnings: list[str] = []
    questions_to_ask: list[str] = []


class ConversationTurn(BaseModel):
    role: str  # "applicant" | "agent"
    text: str
    referenced_posting_ids: list[str] = []


class StartSessionRequest(BaseModel):
    postings: Optional[list[ShortlistPosting]] = None
    language_code: str = "en-IN"


class PostingReadback(BaseModel):
    posting_id: str
    text: str
    audio_base64: list[str]


class StartSessionResponse(BaseModel):
    session_id: str
    guide_text: str
    guide_audio_base64: list[str]
    postings: list[PostingReadback]


class AskRequest(BaseModel):
    question_text: str


class ShortlistToggleRequest(BaseModel):
    posting_id: str
    shortlisted: bool = True


class AskResponse(BaseModel):
    question_text: str
    answer_text: str
    answer_audio_base64: list[str]
    referenced_posting_ids: list[str]
    applicant_expressed_interest: bool
    shortlisted_ids: list[str]


class SessionState(BaseModel):
    session_id: str
    postings: list[ShortlistPosting]
    history: list[ConversationTurn]
    shortlisted_ids: list[str]
