"""Title gate: decide guard / supervisory / unrelated, with the reason recorded.

The live Indeed query for "security guard" in Bengaluru returns mostly non-guard
roles (managers, field officers, and outright unrelated postings), so this gate is
what makes the downstream ranking trustworthy.
"""

import re

GUARD = [
    "security guard", "securityguard", "watchman", "lady guard", "lady security",
    "security personnel", "gunman", "armed security", "security staff",
    "guard cum", "gate keeper", "gatekeeper", "bouncer",
]

# Seniority markers. A title carrying one of these is not an entry-level guard post
# even when it also contains "security guard" (e.g. "Security Guard Supervisor").
SENIOR = [
    "supervisor", "manager", "management", "officer", "executive", "specialist",
    "lead", "head", "incharge", "in charge", "in-charge", "coordinator",
    "operation", "operations", "admin", "recruiter", "consultant", "counsel",
]

UNRELATED = [
    "data protection", "cyber", "information security", "infosec", "network security",
    "driver", "safety executive", "software", "engineer", "developer", "analyst",
]


def classify(title: str, has_experience: bool = False) -> tuple[str, str]:
    """Return (verdict, reason). Verdict is keep / flag / reject."""
    t = re.sub(r"\s+", " ", (title or "").strip().lower())

    for term in UNRELATED:
        if term in t:
            return "reject", f"unrelated role: matched {term!r}"

    is_guard = any(term in t for term in GUARD)
    senior = next((s for s in SENIOR if s in t), None)

    if is_guard and not senior:
        return "keep", "entry-level guard title"
    if is_guard and senior:
        if has_experience:
            return "flag", f"guard title, senior marker {senior!r}; applicant has experience"
        return "reject", f"guard title, senior marker {senior!r}; no relevant experience"
    if senior:
        return "reject", f"supervisory/managerial role: matched {senior!r}"
    return "reject", "no guard-role signal in title"


def apply(rows: list[dict], has_experience: bool = False) -> tuple[list[dict], list[dict]]:
    """Split rows into (kept, dropped); each row gains _verdict and _reason."""
    kept, dropped = [], []
    for row in rows:
        verdict, reason = classify(row.get("title", ""), has_experience)
        row["_verdict"], row["_reason"] = verdict, reason
        (kept if verdict in ("keep", "flag") else dropped).append(row)
    return kept, dropped
