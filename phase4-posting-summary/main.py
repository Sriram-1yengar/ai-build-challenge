"""Phase 4 entry point: RawPosting[] + profile + benchmark -> ShortlistPosting[]."""

import json
import pathlib
import sys

import analyze
import score as scoring
import summarize
import validate

ROOT = pathlib.Path(__file__).parent.parent
OUT = pathlib.Path(__file__).parent / "out"


def build(postings, profile, benchmark, use_llm=True):
    top = scoring.rank(postings, profile, top=3)
    median = (benchmark or {}).get("median_monthly_inr")
    comparisons = [analyze.pay_comparison(s["monthly_pay"], median) for s in top]

    written = [{}] * len(top)
    if use_llm and top:
        try:
            written = summarize.summarize(top, comparisons)
        except Exception as e:
            print(f"  LLM failed ({e}); falling back to deterministic cards")

    shortlist = []
    for s, comp, w in zip(top, comparisons, written):
        f, p = s["facts"], s["posting"]
        problems = validate.check({**w, "posting_id": p["posting_id"]},
                                  {**summarize._brief(s, comp)})
        if problems:
            print(f"  ! {p['posting_id']} summary rejected: {problems}")
            w = {}
        pay = None
        if f["salary_min"]:
            pay = f"₹{f['salary_min']:,.0f}"
            if f["salary_max"] and f["salary_max"] != f["salary_min"]:
                pay += f" - ₹{f['salary_max']:,.0f}"
            if f["salary_unit"]:
                pay += f" per {f['salary_unit']}"

        shortlist.append({
            "posting_id": p["posting_id"],
            "title": p["raw_title"],
            "employer": f["employer"],
            "location": f["location"],
            "pay": pay,
            "requirements": [],
            "benefits": f["benefits"],
            "shift": f["shift"],
            "contact_method": f["apply_path"],
            "source_url": p["source_url"],
            "summary": w.get("summary") or _fallback(p, f, comp),
            "match_score": s["match_score"],
            "match_reasons": w.get("match_reasons") or s["reasons"][:3],
            "pay_comparison": comp,
            "missing_fields": analyze.missing_labels(s),
            "warnings": analyze.warnings(s),
            "questions_to_ask": analyze.questions(s),
        })
    return shortlist


def _fallback(p, f, comp):
    bits = [p["raw_title"]]
    if f["employer"]:
        bits.append(f"at {f['employer']}")
    if f["location"]:
        bits.append(f"in {f['location']}")
    pay = f"₹{f['salary_min']:,.0f} per {f['salary_unit']}" if f["salary_min"] and f["salary_unit"] else "Pay not stated"
    return " ".join(bits) + ". " + pay + "."


def main():
    p3 = ROOT / "phase3-job-search/out"
    postings = json.loads((p3 / "raw_postings.json").read_text())
    benchmark = json.loads((p3 / "salary_benchmark.json").read_text())
    profile = json.loads((ROOT / "shared/fixtures/sample_profile.json").read_text())

    use_llm = "--no-llm" not in sys.argv
    print(f"ranking {len(postings)} postings (median ₹{benchmark['median_monthly_inr']:,}/month)\n")
    shortlist = build(postings, profile, benchmark, use_llm)

    OUT.mkdir(exist_ok=True)
    (OUT / "shortlist.json").write_text(json.dumps(shortlist, ensure_ascii=False, indent=2) + "\n")

    for s in shortlist:
        print(f"  [{s['match_score']:3d}] {s['title'][:34]:34s} {s['pay'] or 'pay not stated':28s} {s['pay_comparison']}")
        print(f"        {s['summary'][:96]}")
        for w in s["warnings"]:
            print(f"        ! {w[:92]}")
    print(f"\nwrote {len(shortlist)} -> out/shortlist.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
