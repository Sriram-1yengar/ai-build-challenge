"""Groundedness guard. Any number, URL or phone the model produced that is not in
its input means the summary is discarded rather than spoken to a job seeker."""

import re

_NUM = re.compile(r"\d[\d,]*")


def _nums(s: str) -> set[str]:
    return {n.replace(",", "").lstrip("0") or "0" for n in _NUM.findall(s or "")}


def check(written: dict, source: dict) -> list[str]:
    text = " ".join([written.get("summary") or ""] + (written.get("match_reasons") or []))
    problems = []

    allowed = _nums(str(source))
    invented = {n for n in _nums(text) if n not in allowed}
    if invented:
        problems.append(f"invented number(s): {sorted(invented)}")

    if re.search(r"https?://|www\.", text):
        problems.append("contains a URL")
    if re.search(r"\+?\d[\d\s-]{8,}\d", text):
        problems.append("contains a phone number")
    if re.search(r"\bscam\b|\bfraud\b|\bfake\b", text, re.I):
        problems.append("accuses the listing of fraud")
    if written.get("posting_id") != source.get("posting_id"):
        problems.append("posting_id mismatch")
    return problems
