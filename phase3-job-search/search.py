"""Phase 3 entry point: profile -> raw_postings.json + salary_benchmark.json."""

import json
import pathlib
import sys
from datetime import datetime, timezone

import filter as title_gate
import sources

OUT = pathlib.Path(__file__).parent / "out"
MAX_DETAILS = 6


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def collect(profile: dict) -> tuple[list[dict], list[dict]]:
    """Search every source, gate by title, keep Bengaluru only."""
    has_exp = (profile.get("years_experience") or 0) >= 1
    skills = [s for s in (profile.get("skills") or []) if s and s.strip()] or [sources.QUERY]
    primary_skill = sources.primary_skill(profile)
    query = sources.search_query_for_skill(primary_skill)
    slug = sources.apna_slug(primary_skill)
    print(f"  searching skill={primary_skill!r} -> query={query!r} apna_slug={slug!r}")

    rows = []
    for name, fn in (
        ("indeed", lambda: sources.indeed_search(query=query)),
        ("apna", lambda: sources.apna_search(slug=slug)),
    ):
        try:
            got = fn()
            print(f"  {name}: {len(got)} rows")
            rows += got
        except Exception as e:                      # one dead source must not kill the run
            print(f"  {name}: FAILED ({e})")

    blr = [r for r in rows if sources.in_bengaluru(r)]
    kept, dropped = title_gate.apply(blr, skills=skills, has_experience=has_exp)

    seen, deduped = set(), []
    for r in kept:
        key = r.get("source_job_id") or r.get("url")
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped, dropped


def to_raw_postings(rows: list[dict]) -> list[dict]:
    """RawPosting[] per shared/schemas/raw_posting.schema.json."""
    out = []
    for r in rows[:MAX_DETAILS]:
        text = r["snippet"]
        if r["source"] == "indeed":
            try:                                    # detail is the source of truth
                d = sources.indeed_details(r["source_job_id"])
                text = d.get("description") or d.get("full_text") or text
            except Exception as e:
                print(f"  detail failed for {r['source_job_id']}: {e}")
        out.append({
            "posting_id": f"{r['source']}-{r['source_job_id']}",
            "source": r["source"],
            "source_job_id": r["source_job_id"],
            "source_url": r["url"],
            "raw_title": r["title"],
            "raw_text": "\n".join(x for x in [
                f"Employer: {r['employer']}" if r.get("employer") else None,
                f"Location: {r['location']}" if r.get("location") else None,
                f"Pay: {r['salary']}" if r.get("salary") else None,
                f"Posted: {r['posted']}" if r.get("posted") else None,
                text,
            ] if x),
            "scraped_at": now(),
        })
    return out


def to_benchmark(profile: dict) -> dict:
    """SalaryBenchmark per shared/schemas/salary_benchmark.schema.json."""
    query = sources.search_query_for_skill(sources.primary_skill(profile))
    s = sources.indeed_salary(title=query)
    monthly = next((x for x in s.get("salaries", []) if x.get("type") == "MONTHLY"), {})
    return {
        "role": s.get("title") or query,
        "location": (s.get("location") or {}).get("name") or "Bengaluru",
        "median_monthly_inr": round(monthly.get("median")) if monthly.get("median") else None,
        "source": "Indeed via Anakin Wire",
        "retrieved_at": now(),
    }


def main() -> int:
    profile_path = pathlib.Path(__file__).parent.parent / "shared/fixtures/sample_profile.json"
    profile = json.loads(profile_path.read_text())

    print("searching sources...")
    kept, dropped = collect(profile)

    print(f"\ntitle gate: kept={len(kept)} dropped={len(dropped)}")
    for r in kept:
        print(f"  KEEP [{r['source']}] {r['title'][:40]:40s} | {r['_reason']}")
    for r in dropped[:6]:
        print(f"   .   [{r['source']}] {r['title'][:40]:40s} | {r['_reason']}")
    if len(dropped) > 6:
        print(f"   .   ...and {len(dropped) - 6} more rejected")

    print(f"\nfetching details for up to {MAX_DETAILS}...")
    postings = to_raw_postings(kept)
    benchmark = to_benchmark(profile)

    OUT.mkdir(exist_ok=True)
    (OUT / "raw_postings.json").write_text(
        json.dumps(postings, ensure_ascii=False, indent=2) + "\n")
    (OUT / "salary_benchmark.json").write_text(
        json.dumps(benchmark, ensure_ascii=False, indent=2) + "\n")

    print(f"\nwrote {len(postings)} postings -> out/raw_postings.json")
    print(f"benchmark median = Rs {benchmark['median_monthly_inr']}/month")
    for p in postings:
        print(f"  {p['posting_id']:28s} raw_text={len(p['raw_text']):5d} chars  {p['raw_title'][:32]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
