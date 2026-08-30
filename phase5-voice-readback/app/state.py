from app.models import ConversationTurn, ShortlistPosting


class Session:
    def __init__(self, session_id: str, postings: list[ShortlistPosting]):
        self.session_id = session_id
        self.postings = postings
        self.history: list[ConversationTurn] = []
        self.shortlisted_ids: set[str] = set()


_sessions: dict[str, Session] = {}


def create_session(session_id: str, postings: list[ShortlistPosting]) -> Session:
    session = Session(session_id, postings)
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Session | None:
    return _sessions.get(session_id)
