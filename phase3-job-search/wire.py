"""Anakin REST client: Wire actions (Indeed) and the generic scraper (Apna)."""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api.anakin.io/v1"
_KEY = os.environ["ANAKIN_API_KEY"]
_HEADERS = {"X-API-Key": _KEY, "Content-Type": "application/json"}


class AnakinError(RuntimeError):
    pass


def run_action(action_id: str, params: dict, timeout: int = 120) -> dict:
    """Submit a Wire action, poll to completion, return its data payload."""
    r = requests.post(
        f"{BASE}/wire/task",
        json={"action_id": action_id, "params": params},
        headers=_HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    submitted = r.json()
    job_id = submitted.get("job_id") or submitted.get("id") or submitted.get("task_id")
    if not job_id:
        raise AnakinError(f"no job id in submit response: {submitted}")

    deadline = time.time() + timeout
    while time.time() < deadline:
        j = requests.get(f"{BASE}/wire/jobs/{job_id}", headers=_HEADERS, timeout=30)
        j.raise_for_status()
        job = j.json()
        status = job.get("status")
        if status in ("completed", "succeeded", "success"):
            return job
        if status in ("failed", "error"):
            raise AnakinError(f"{action_id} failed: {job.get('error')}")
        time.sleep(2)
    raise AnakinError(f"{action_id} timed out after {timeout}s")


def scrape(url: str, use_browser: bool = False, country: str = "in") -> dict:
    """Fetch one URL as markdown via Anakin's inline scraper.

    Path is /v1/url-scraper/scrape — note detailed-build-plan.md documents this as
    /v1/scrape, which 404s.
    """
    r = requests.post(
        f"{BASE}/url-scraper/scrape",
        json={"url": url, "useBrowser": use_browser, "country": country},
        headers=_HEADERS,
        timeout=60,
    )
    r.raise_for_status()
    job = r.json()
    if job.get("markdown"):
        return job

    job_id = job.get("id") or job.get("jobId")
    deadline = time.time() + 240
    while time.time() < deadline:
        time.sleep(3)
        g = requests.get(f"{BASE}/url-scraper/{job_id}", headers=_HEADERS, timeout=30)
        g.raise_for_status()
        job = g.json()
        if job.get("status") in ("completed", "succeeded", "success"):
            return job
        if job.get("status") in ("failed", "error"):
            raise AnakinError(f"scrape failed for {url}: {job.get('error')}")
    raise AnakinError(f"scrape timed out for {url}")


if __name__ == "__main__":
    import json
    import sys

    if sys.argv[1:] == ["scrape"]:
        out = scrape("https://example.com")
        print(json.dumps(out, indent=2)[:600])
    else:
        out = run_action(
            "in_salary_search",
            {"title": "security guard", "location": "Bengaluru",
             "country": "IN", "locale": "en-IN"},
        )
        print(json.dumps(out, indent=2)[:1500])
