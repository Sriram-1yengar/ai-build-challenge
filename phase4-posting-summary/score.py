"""Deterministic 100-point score (VERIFIED_MVP_SPEC.md step 8).

Code picks the winners. The LLM only explains them afterwards, so ranking is
reproducible and cannot be silently reordered by a model.
"""

import parse as P

SENIOR_WORDS = ("supervisor", "officer", "manager", "lead", "incharge")

# Mirrors phase3-job-search/sources.py's SKILL_TITLE_TERMS -- kept duplicated
# rather than imported so phase4 stays testable standalone against fixtures
# (structure.md rule 3) without depending on phase3's package being on
# sys.path. Job-title vocabulary for each Phase 2 normalized skill; falls
# back to the raw skill text for anything not listed here.
SKILL_TITLE_TERMS = {
    "driving": ("driver", "driving"),
    "electrical work": ("electrician", "electrical"),
    "construction labor": ("construction", "labour", "laborer", "labourer"),
    "construction": ("construction", "labour", "laborer", "labourer"),
    "plumbing": ("plumber", "plumbing"),
    "painting": ("painter", "painting"),
    "cooking": ("cook", "chef", "kitchen"),
    "delivery": ("delivery", "rider", "courier"),
    "carpentry": ("carpenter", "carpentry"),
    "masonry": ("mason", "masonry"),
    "security": ("security guard", "watchman", "security", "gunman", "gatekeeper"),
    "housekeeping": ("housekeeping", "housekeeper", "maid", "domestic help"),
    "welding": ("welder", "welding"),
}


def _title_terms(skill: str) -> tuple[str, ...]:
    return SKILL_TITLE_TERMS.get((skill or "").strip().lower(), ((skill or "").strip().lower(),))


def role_points(title: str, skills: list[str], has_experience: bool) -> tuple[int, str]:
    t = (title or "").lower()
    senior = any(w in t for w in SENIOR_WORDS)
    matched = next((s for s in skills if any(term in t for term in _title_terms(s))), None)
    if matched and not senior:
        return 35, f"exact match for {matched!r}"
    if matched and senior and has_experience:
        return 15, f"adjacent supervisory role matching {matched!r}, applicant has experience"
    return 0, "not a matching role"


def location_points(loc: str | None, preferred_area: str | None) -> tuple[int, str]:
    l = (loc or "").lower()
    if preferred_area and preferred_area.lower() in l:
        return 25, f"in preferred area {preferred_area}"
    has_locality = "," in (loc or "") or any(
        c not in l for c in ("bengaluru", "bangalore"))
    if any(c in l for c in ("bengaluru", "bangalore")):
        if has_locality and l.strip() not in ("bengaluru", "bangalore"):
            return 18, "Bengaluru with a usable locality"
        return 10, "Bengaluru but no locality given"
    return 0, "location not usable"


def pay_points(monthly: float | None, expectation: float | None) -> tuple[int, str]:
    if monthly is None:
        return 6, "pay not stated"
    if expectation is None:
        return 14, "pay stated, no expectation to compare"
    if monthly >= expectation:
        return 20, "meets or exceeds pay expectation"
    if monthly >= expectation * 0.9:
        return 14, "within 10% of pay expectation"
    return 0, "clearly below pay expectation"


def shift_points(shift: str | None, preference: str | None) -> tuple[int, str]:
    if shift and preference and preference != "either":
        if shift == preference:
            return 10, "shift matches preference"
        if shift in ("rotational", "flexible"):
            return 5, "rotational/flexible shift"
        return 0, "shift conflicts with preference"
    if shift:
        return 5, "shift stated, applicant flexible"
    return 5, "shift not stated"


def terms_points(f: dict) -> tuple[int, list[str]]:
    """2 points each for salary, shift/hours, location, employer, apply path."""
    checks = {
        "salary": f["salary_min"] is not None,
        "shift_hours": f["shift"] is not None or f["hours_per_shift"] is not None,
        "location": bool(f["location"]),
        "employer": bool(f["employer"]),
        "apply_path": bool(f["apply_path"]),
    }
    missing = [k for k, ok in checks.items() if not ok]
    return sum(2 for ok in checks.values() if ok), missing


def score(posting: dict, profile: dict) -> dict:
    f = P.parse(posting)
    has_exp = (profile.get("years_experience") or 0) >= 1
    area = (profile.get("location") or {}).get("area")
    skills = profile.get("skills") or []

    r, r_why = role_points(posting.get("raw_title"), skills, has_exp)
    l, l_why = location_points(f["location"] or posting.get("raw_title"), area)
    m = P.monthly(f["salary_min"], f["salary_unit"])
    p, p_why = pay_points(m, profile.get("min_pay_expectation"))
    s, s_why = shift_points(f["shift"], profile.get("shift_preference"))
    t, missing = terms_points(f)

    return {
        "posting": posting,
        "facts": f,
        "monthly_pay": m,
        "breakdown": {"role": r, "location": l, "pay": p, "shift": s, "terms": t},
        "reasons": [r_why, l_why, p_why, s_why, f"{t}/10 terms stated"],
        "missing_fields": missing,
        "match_score": r + l + p + s + t,
    }


def rank(postings: list[dict], profile: dict, top: int = 3) -> list[dict]:
    scored = [score(p, profile) for p in postings]
    scored = [s for s in scored if s["breakdown"]["role"] > 0]   # never rank non-guards
    scored.sort(key=lambda s: (
        -s["match_score"],
        len(s["missing_fields"]),                 # tie-break 1: completeness
        s["posting"]["posting_id"],               # tie-break 4: stable id
    ))
    return scored[:top]
