"""Pull structured facts out of RawPosting.raw_text. Never guess — None means absent."""

import re

# "₹20,000 - ₹25,000 a month", "Rs 600/day", "₹18,000 per month"
_NUM = r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)"
_UNIT = {
    "hour": "hour", "hr": "hour", "day": "day", "daily": "day",
    "week": "week", "month": "month", "monthly": "month", "year": "year",
    "annum": "year", "yearly": "year",
}

_SHIFT = {
    "rotational": "rotational", "rotating": "rotational",
    "night": "night", "day shift": "day", "flexible": "flexible",
}

_BENEFIT = ["pf", "provident fund", "esi", "food", "meal", "accommodation",
            "uniform", "insurance", "bonus"]

# Evidence-based fraud/risk wording (VERIFIED_MVP_SPEC.md step 9).
_FEE_TERMS = ["registration fee", "application fee", "security deposit", "deposit",
              "paid training", "training fee", "uniform charge", "uniform deduction",
              "pay to apply", "processing fee", "aadhaar", "otp", "bank details"]


def _money(text: str) -> tuple[float | None, float | None, str | None]:
    """Read pay from the 'Pay:' line only.

    The unit must be adjacent to the amount. Scanning the whole posting picks up
    stray words ("day shift", "per day" in a duty list) and mislabels a monthly
    wage as daily, which then inflates the market comparison ~26x.
    """
    m = re.search(r"^Pay:\s*(.+)$", text, re.M)
    span = m.group(1) if m else text

    nums = [float(n.replace(",", "")) for n in re.findall(_NUM, span)]
    if not nums:
        return None, None, None

    tail = span[span.rfind(str(int(max(nums)))[0]):][:40] if span else ""
    unit = None
    for k, v in sorted(_UNIT.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"(?:per\s*|/|a\s+){k}\b", tail, re.I):
            unit = v
            break
    return min(nums), max(nums), unit


def parse(posting: dict) -> dict:
    t = posting.get("raw_text", "")
    low = t.lower()
    lo, hi, unit = _money(t)

    shift = next((v for k, v in _SHIFT.items() if k in low), None)
    benefits = sorted({b for b in _BENEFIT if b in low})

    employer = None
    m = re.search(r"^Employer:\s*(.+)$", t, re.M)
    if m:
        employer = m.group(1).strip()

    location = None
    m = re.search(r"^Location:\s*(.+)$", t, re.M)
    if m:
        location = m.group(1).strip()

    return {
        "salary_min": lo,
        "salary_max": hi,
        "salary_unit": unit,
        "shift": shift,
        "hours_per_shift": _hours(low),
        "benefits": benefits,
        "employer": employer,
        "location": location,
        "apply_path": _apply(t),
        "fee_terms": [f for f in _FEE_TERMS if f in low],
    }


def _hours(low: str) -> float | None:
    m = re.search(r"(\d{1,2})\s*(?:hour|hr)s?\s*(?:shift|duty|per day)", low)
    return float(m.group(1)) if m else None


def _apply(text: str) -> str | None:
    m = re.search(r"(\+?\d[\d\s-]{8,14}\d)", text)          # phone
    if m:
        return m.group(1).strip()
    if re.search(r"https?://", text):
        return "apply via source link"
    return None


def monthly(lo: float | None, unit: str | None) -> float | None:
    """Normalize stated pay to a monthly figure so it can be compared to benchmark."""
    if lo is None or unit is None:
        return None
    return {"hour": lo * 8 * 26, "day": lo * 26, "week": lo * 4.33,
            "month": lo, "year": lo / 12}.get(unit)
