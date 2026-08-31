"""Job sources. Indeed goes through Anakin Wire; Apna through the generic scraper."""

import re

from wire import run_action, scrape

QUERY = "security guard"
CITY = "Bengaluru, Karnataka"

# Phase 2 normalizes applicant skills to descriptive trade phrases (see
# detailed-build-plan.md's Profile Extractor prompt), but job portals match
# and title-gate on actual job-title vocabulary -- "electrical work" won't
# text-match a posting titled "Electrician". This maps each known skill to
# the terms a real posting title would use; first term is also what we search
# portals with. Falls back to the raw skill text for anything not listed here.
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


def title_terms_for_skill(skill: str) -> tuple[str, ...]:
    return SKILL_TITLE_TERMS.get((skill or "").strip().lower(), ((skill or "").strip().lower(),))


def search_query_for_skill(skill: str) -> str:
    """The term to search job portals with -- portals match job-title
    vocabulary better than Phase 2's descriptive phrasing."""
    return title_terms_for_skill(skill)[0]


def apna_slug(skill: str, city: str = "bangalore") -> str:
    term = re.sub(r"[^a-z0-9]+", "-", search_query_for_skill(skill)).strip("-")
    return f"{term}-jobs-in-{city}"


def primary_skill(profile: dict) -> str:
    skills = [s for s in (profile.get("skills") or []) if s and s.strip()]
    return skills[0] if skills else QUERY


def _payload(job: dict) -> dict:
    return job.get("data", {}).get("data", {})


def indeed_search(query: str = QUERY, location: str = CITY, start: int = 0,
                  sort: str = "date") -> list[dict]:
    """One Indeed search page, normalized to common row shape."""
    job = run_action("in_search_jobs", {
        "query": query, "location": location, "start": start,
        "sort": sort, "country_domain": "in",
    })
    rows = []
    for j in _payload(job).get("jobs", []):
        rows.append({
            "source": "indeed",
            "source_job_id": j.get("job_key"),
            "url": j.get("url"),
            "title": j.get("title"),
            "employer": j.get("company"),
            "location": j.get("location"),
            "salary": j.get("salary"),
            "posted": j.get("date_posted"),
            "snippet": _strip_html(j.get("snippet") or ""),
        })
    return rows


def indeed_details(job_key: str) -> dict:
    """Full listing detail — the source of truth for requirements and apply path."""
    return _payload(run_action("in_job_details",
                               {"job_key": job_key, "country_domain": "in"}))


def indeed_salary(title: str = QUERY, location: str = "Bengaluru") -> dict:
    job = run_action("in_salary_search", {
        "title": title, "location": location, "country": "IN", "locale": "en-IN",
    })
    return _payload(job)


# Apna listing rows look like:
#   [**Title** Employer\ \ Locality\ \ ₹20,000 - ₹25,000\ ...](https://apna.co/job/<city>/<slug>-<id>)
APNA_ROW = re.compile(
    r"\*\*(?P<title>[^*]+)\*\*(?P<rest>(?:(?!\*\*).)*?)\]\("
    r"(?P<url>https://apna\.co/job/[^)]+)\)",
    re.S,
)


def apna_search(slug: str = "security-guard-jobs-in-bangalore") -> list[dict]:
    """Scrape one Apna listing page. Needs the headless browser — it is an SPA."""
    md = scrape(f"https://apna.co/jobs/{slug}", use_browser=True).get("markdown", "")
    rows = []
    for m in APNA_ROW.finditer(md):
        parts = [p.strip() for p in re.split(r"\\+\s*", m.group("rest")) if p.strip()]
        salary = next((p for p in parts if p.startswith("₹")), None)
        rows.append({
            "source": "apna",
            "source_job_id": m.group("url").rsplit("-", 1)[-1],
            "url": m.group("url"),
            "title": m.group("title").strip(),
            "employer": parts[0] if parts else None,
            "location": parts[1] if len(parts) > 1 else None,
            "salary": salary,
            "posted": None,
            "snippet": " | ".join(parts),
        })
    return rows


def _strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


BENGALURU = ("bengaluru", "bangalore")


def in_bengaluru(row: dict) -> bool:
    loc = (row.get("location") or "").lower()
    return any(c in loc for c in BENGALURU)
