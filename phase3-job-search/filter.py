"""Title gate: decide keep / flag / reject against the applicant's own stated
skills, with the reason recorded.

A job-portal text search matches loosely, so a search for one trade still
returns adjacent or unrelated roles (managers, field officers, other trades,
generic corporate postings that happen to share a keyword). This gate is what
makes the downstream ranking trustworthy.
"""

import re

from sources import title_terms_for_skill

# Seniority markers. A title carrying one of these is not an entry-level post
# even when it also matches the applicant's skill (e.g. "Electrical Supervisor").
SENIOR = [
    "supervisor", "manager", "management", "officer", "executive", "specialist",
    "lead", "head", "incharge", "in charge", "in-charge", "coordinator",
    "operation", "operations", "admin", "recruiter", "consultant", "counsel",
]

# Generic non-blue-collar corporate/tech roles that keyword-overlap can pull
# in regardless of which trade was searched (e.g. "driver" inside a software
# job title). Not trade-specific -- this is deliberately a short, safe list.
UNRELATED = [
    "software", "developer", "data protection", "cyber security",
    "information security", "network security", "data analyst", "business analyst",
]


def classify(title: str, skills: list[str], has_experience: bool = False) -> tuple[str, str]:
    """Return (verdict, reason). Verdict is keep / flag / reject."""
    t = re.sub(r"\s+", " ", (title or "").strip().lower())

    for term in UNRELATED:
        if term in t:
            return "reject", f"unrelated role: matched {term!r}"

    matched_skill = next(
        (skill for skill in skills if any(term in t for term in title_terms_for_skill(skill))),
        None,
    )
    senior = next((s for s in SENIOR if s in t), None)

    if matched_skill and not senior:
        return "keep", f"matches applicant skill {matched_skill!r}"
    if matched_skill and senior:
        if has_experience:
            return "flag", f"{matched_skill!r} title, senior marker {senior!r}; applicant has experience"
        return "reject", f"{matched_skill!r} title, senior marker {senior!r}; no relevant experience"
    if senior:
        return "reject", f"supervisory/managerial role: matched {senior!r}"
    return "reject", "no matching skill signal in title"


def apply(rows: list[dict], skills: list[str], has_experience: bool = False) -> tuple[list[dict], list[dict]]:
    """Split rows into (kept, dropped); each row gains _verdict and _reason."""
    kept, dropped = [], []
    for row in rows:
        verdict, reason = classify(row.get("title", ""), skills, has_experience)
        row["_verdict"], row["_reason"] = verdict, reason
        (kept if verdict in ("keep", "flag") else dropped).append(row)
    return kept, dropped
