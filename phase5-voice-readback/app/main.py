import json
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import llm, state, stt, tts
from app.models import (
    AskRequest,
    AskResponse,
    ConversationTurn,
    PostingReadback,
    SessionState,
    ShortlistPosting,
    ShortlistToggleRequest,
    StartSessionRequest,
    StartSessionResponse,
)
from app.state import Session

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")

app = FastAPI(title="Kaam Sahayak - Phase 5: Voice Readback & Follow-Up")

# Dev-only: allow the Vite frontend (localhost:5173) to call this API directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


_FIXTURE_PATH = _REPO_ROOT / "shared" / "fixtures" / "shortlist.json"


def _load_fixture_postings() -> list[ShortlistPosting]:
    data = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return [ShortlistPosting(**item) for item in data]


@app.post("/session/start", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest) -> StartSessionResponse:
    postings = req.postings if req.postings is not None else _load_fixture_postings()
    if not postings:
        raise HTTPException(status_code=400, detail="No postings provided or found in fixture")

    session_id = str(uuid.uuid4())
    session = state.create_session(session_id, postings)

    try:
        guide_audio = tts.synthesize(llm.GUIDE_TEXT, language_code=req.language_code)
        segments = llm.rewrite_segments_for_speech(postings)
        readbacks = [
            PostingReadback(
                posting_id=seg["posting_id"],
                text=seg["text"],
                audio_base64=tts.synthesize(seg["text"], language_code=req.language_code),
            )
            for seg in segments
        ]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream voice/LLM API error: {e}") from e

    full_text = llm.GUIDE_TEXT + "\n\n" + "\n\n".join(r.text for r in readbacks)
    session.history.append(ConversationTurn(role="agent", text=full_text, referenced_posting_ids=[]))

    return StartSessionResponse(
        session_id=session_id,
        guide_text=llm.GUIDE_TEXT,
        guide_audio_base64=guide_audio,
        postings=readbacks,
    )


def _process_question(session: Session, question_text: str) -> AskResponse:
    session.history.append(
        ConversationTurn(role="applicant", text=question_text, referenced_posting_ids=[])
    )

    result = llm.answer_question(session.postings, session.history, question_text)

    session.history.append(
        ConversationTurn(
            role="agent",
            text=result["answer_text"],
            referenced_posting_ids=result["referenced_posting_ids"],
        )
    )

    if result["applicant_expressed_interest"]:
        session.shortlisted_ids.update(result["referenced_posting_ids"])

    answer_audio = tts.synthesize(result["answer_text"])

    return AskResponse(
        question_text=question_text,
        answer_text=result["answer_text"],
        answer_audio_base64=answer_audio,
        referenced_posting_ids=result["referenced_posting_ids"],
        applicant_expressed_interest=result["applicant_expressed_interest"],
        shortlisted_ids=sorted(session.shortlisted_ids),
    )


@app.post("/session/{session_id}/ask", response_model=AskResponse)
def ask(session_id: str, req: AskRequest) -> AskResponse:
    session = state.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return _process_question(session, req.question_text)


@app.post("/session/{session_id}/ask-audio", response_model=AskResponse)
async def ask_audio(session_id: str, audio: UploadFile = File(...)) -> AskResponse:
    """Same as /ask, but takes the applicant's spoken follow-up question as an
    audio recording and transcribes+translates it via Sarvam STT first. This is
    the real voice-native path; /ask (typed text) remains for debugging.
    """
    session = state.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio upload")

    question_text = stt.transcribe(
        audio_bytes,
        filename=audio.filename or "audio.webm",
        content_type=audio.content_type,
    )
    return _process_question(session, question_text)


@app.post("/session/{session_id}/shortlist", response_model=SessionState)
def toggle_shortlist(session_id: str, req: ShortlistToggleRequest) -> SessionState:
    """Manual shortlist fallback (per build plan §6 note): lets the UI mark/unmark
    a posting directly, independent of the LLM's conversational interest-detection.
    """
    session = state.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    valid_ids = {p.posting_id for p in session.postings}
    if req.posting_id not in valid_ids:
        raise HTTPException(status_code=400, detail="Unknown posting_id")

    if req.shortlisted:
        session.shortlisted_ids.add(req.posting_id)
    else:
        session.shortlisted_ids.discard(req.posting_id)

    return SessionState(
        session_id=session.session_id,
        postings=session.postings,
        history=session.history,
        shortlisted_ids=sorted(session.shortlisted_ids),
    )


@app.get("/session/{session_id}/state", response_model=SessionState)
def get_state(session_id: str) -> SessionState:
    session = state.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionState(
        session_id=session.session_id,
        postings=session.postings,
        history=session.history,
        shortlisted_ids=sorted(session.shortlisted_ids),
    )
