"""Pay comparison, warnings, and questions (VERIFIED_MVP_SPEC.md step 9).

Missing information is never called fraud. Wording stays "not stated" or
"verify before applying".
"""

_LABEL = {
    "salary": "salary", "shift_hours": "shift hours", "location": "exact location",
    "employer": "employer name", "apply_path": "how to apply",
}


def pay_comparison(monthly: float | None, median: float | None) -> str:
    if monthly is None or not median:
        return "unknown"
    if monthly >= median * 1.1:
        return "above_market"
    if monthly >= median * 0.9:
        return "near_market"
    return "below_market"


def warnings(scored: dict) -> list[str]:
    f, out = scored["facts"], []

    if f["fee_terms"]:
        out.append(
            "Listing mentions " + ", ".join(f["fee_terms"])
            + ". A genuine employer does not ask for money, Aadhaar, OTP or bank "
              "details before you are hired. Verify before applying.")

    lo, hi, unit = f["salary_min"], f["salary_max"], f["salary_unit"]
    if lo and hi and hi > lo * 3:
        out.append(
            f"Pay range is very wide (₹{lo:,.0f} to ₹{hi:,.0f}). Ask what you would "
            "actually be paid.")
    if lo and not unit:
        out.append("A pay figure is given but not the period. Ask if it is per day or per month.")
    if not lo:
        out.append("Pay is not stated. Ask before applying.")

    if len(scored["missing_fields"]) >= 3:
        out.append("This listing leaves out several key details. Confirm them before applying.")
    if not f["employer"]:
        out.append("Employer name is not stated; identity could not be confirmed from the listing.")
    return out


def questions(scored: dict) -> list[str]:
    qs = []
    for m in scored["missing_fields"]:
        if m == "salary":
            qs.append("What is the pay, and is it per day or per month?")
        elif m == "shift_hours":
            qs.append("How many hours is each shift, and is it day or night?")
        elif m == "location":
            qs.append("Where exactly is the workplace?")
        elif m == "employer":
            qs.append("Which company would I be working for?")
        elif m == "apply_path":
            qs.append("How do I apply, and who do I contact?")
    if scored["facts"]["fee_terms"]:
        qs.insert(0, "Is any payment or deposit required from me at any stage?")
    return qs[:3]


def missing_labels(scored: dict) -> list[str]:
    return [_LABEL.get(m, m) for m in scored["missing_fields"]]
