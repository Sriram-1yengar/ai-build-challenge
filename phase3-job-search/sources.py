"""Job sources. Indeed goes through Anakin Wire; Apna through the generic scraper."""

import re

from wire import run_action, scrape

QUERY = "security guard"
CITY = "Bengaluru, Karnataka"


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
