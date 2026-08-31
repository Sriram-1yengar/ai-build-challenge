"""Integration layer: chains Phase 3 (job search) -> Phase 4 (posting summary)
behind one HTTP endpoint, so the frontend makes a single call instead of
juggling two separate phase services. Imports their modules directly (in
process) rather than duplicating their logic -- neither phase3-job-search/ nor
phase4-posting-summary/ is modified by this file.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PHASE3_DIR = ROOT / "phase3-job-search"
PHASE4_DIR = ROOT / "phase4-posting-summary"
sys.path.insert(0, str(PHASE3_DIR))
sys.path.insert(0, str(PHASE4_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import search as phase3_search  # phase3-job-search/search.py  # noqa: E402
import main as phase4_main  # phase4-posting-summary/main.py  # noqa: E402

app = FastAPI(title="Kaam Sahayak - Job Search (Phase 3 + Phase 4)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobSearchRequest(BaseModel):
    profile: dict
    use_llm: bool = True


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/job-search")
def job_search(req: JobSearchRequest):
    try:
        kept, _dropped = phase3_search.collect(req.profile)
        raw_postings = phase3_search.to_raw_postings(kept)
        benchmark = phase3_search.to_benchmark(req.profile)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Job search failed: {e}") from e

    if not raw_postings:
        return {"postings": [], "raw_postings": [], "benchmark": benchmark}

    try:
        shortlist = phase4_main.build(raw_postings, req.profile, benchmark, req.use_llm)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Posting summary failed: {e}") from e

    return {"postings": shortlist, "raw_postings": raw_postings, "benchmark": benchmark}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8003)
