from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable

from .models import Job

_JAVA_RE = re.compile(r"\bjava\b", re.I)
_SPRING_BOOT_RE = re.compile(r"spring\s*boot|springboot", re.I)

# Experience patterns — we care about the *minimum* years implied.
_RANGE_YEARS = re.compile(
    r"(\d+)\s*[-–to]+\s*(\d+)\s*\+?\s*(?:years?|yrs?)",
    re.I,
)
_PLUS_YEARS = re.compile(
    r"(\d+)\s*\+\s*(?:years?|yrs?|yoe|exp\.?)",
    re.I,
)
_BARE_PLUS = re.compile(r"\((\d+)\+\)|(\d+)\+\s*(?:years?|yrs?)", re.I)
_MIN_YEARS = re.compile(
    r"(?:minimum|min\.?|at\s+least|over|more\s+than)\s+(\d+)\s*\+?\s*(?:years?|yrs?)",
    re.I,
)
_PLAIN_YEARS = re.compile(
    r"(?:with|having|requires?|requiring|need(?:s|ed)?|experience(?:\s+of)?)\s+(\d+)\s*(?:years?|yrs?)",
    re.I,
)
_TITLE_YEARS = re.compile(
    r"\((\d+)\+?\)|(?:^|\s)(\d+)\+\s*(?:years?|yrs?|exp)",
    re.I,
)

# Masters / postgraduate as a hard requirement (not preferred-only soft mentions alone).
_MASTERS_REQ = re.compile(
    r"(?:"
    r"(?:master'?s?|masters|m\.?\s*tech|mtech|m\.?\s*e(?:ng)?\b|mba|m\.?\s*s\b|msc|post[- ]?grad(?:uate)?)"
    r".{0,40}(?:required|mandatory|must|need(?:ed)?|compulsory)"
    r"|"
    r"(?:required|mandatory|must\s+have|needs?\s+a?)\s+"
    r"(?:a\s+)?(?:master'?s?|masters|m\.?\s*tech|mtech|mba|m\.?\s*s\b|msc|post[- ]?grad(?:uate)?)"
    r"|"
    r"(?:master'?s?|masters|m\.?\s*tech|mtech|mba)\s+degree\s+required"
    r")",
    re.I,
)


def _blob(job: Job) -> str:
    return f"{job.title} {job.description} {job.location} {job.company}"


def matches_keywords(job: Job, keywords: Iterable[str]) -> bool:
    """Match if any configured keyword appears (OR)."""
    text = _blob(job)
    kws = [str(k).strip() for k in keywords if k and str(k).strip()]
    if not kws:
        return bool(_JAVA_RE.search(text) or _SPRING_BOOT_RE.search(text))
    for kw in kws:
        k = kw.lower()
        if " " in k:
            pat = re.escape(k).replace(r"\ ", r"[\s\-]*")
            if re.search(pat, text, re.I):
                return True
        elif re.search(rf"\b{re.escape(k)}\b", text, re.I):
            return True
    return False


def is_excluded_level(job: Job, exclude_terms: Iterable[str]) -> bool:
    title = job.title.lower()
    for term in exclude_terms:
        t = term.lower().strip()
        if not t:
            continue
        if re.search(rf"\b{re.escape(t)}\b", title):
            return True
    return False


def has_sponsorship_signal(job: Job, sponsorship_keywords: Iterable[str]) -> bool:
    text = _blob(job).lower()
    for kw in sponsorship_keywords:
        if kw.lower() in text:
            return True
    return False


def inferred_min_years(text: str) -> int | None:
    """Lowest experience floor found in text, or None if nothing parsed."""
    mins: list[int] = []
    for m in _RANGE_YEARS.finditer(text):
        a, b = int(m.group(1)), int(m.group(2))
        mins.append(min(a, b))
    for m in _PLUS_YEARS.finditer(text):
        mins.append(int(m.group(1)))
    for m in _BARE_PLUS.finditer(text):
        n = m.group(1) or m.group(2)
        if n:
            mins.append(int(n))
    for m in _MIN_YEARS.finditer(text):
        mins.append(int(m.group(1)))
    for m in _PLAIN_YEARS.finditer(text):
        mins.append(int(m.group(1)))
    for m in _TITLE_YEARS.finditer(text):
        n = m.group(1) or m.group(2)
        if n:
            mins.append(int(n))
    if not mins:
        return None
    # If multiple signals, use the highest floor (strictest requirement).
    # Ignore absurd parses (e.g. "890+ Clients" before the years-required fix).
    sane = [n for n in mins if 0 < n <= 40]
    return max(sane) if sane else None


def is_excluded_seniority(job: Job, patterns: Iterable[str]) -> bool:
    title = job.title.lower()
    for term in patterns:
        t = term.lower().strip()
        if not t:
            continue
        # Word-ish bounds so "architect" does not match "architecture".
        if re.search(rf"(?<![\w]){re.escape(t)}(?![\w])", title):
            return True
    return False


def exceeds_max_years(job: Job, max_years: int) -> bool:
    """True when posting requires more years than max_years."""
    if max_years <= 0:
        return False
    floor = inferred_min_years(_blob(job))
    if floor is None:
        return False
    return floor > max_years


def requires_excluded_education(job: Job, exclude_education: Iterable[str]) -> bool:
    """Drop Masters/MBA/etc. when requirement-like phrasing is present."""
    text = _blob(job)
    if _MASTERS_REQ.search(text):
        return True
    # Also drop blunt keyword hits from config when clearly degree-oriented.
    lower = text.lower()
    for term in exclude_education:
        t = term.lower().strip()
        if not t:
            continue
        if t in lower and re.search(
            rf"{re.escape(t)}.{{0,30}}(?:required|mandatory|must|degree)",
            lower,
        ):
            return True
        if re.search(rf"(?:required|mandatory|must\s+have).{{0,30}}{re.escape(t)}", lower):
            return True
    return False


def passes_filters(
    job: Job,
    *,
    keywords: list[str],
    exclude_levels: list[str],
    sponsorship_keywords: list[str],
    sponsorship_board_ids: set[str],
    max_years: int = 4,
    exclude_education: list[str] | None = None,
    exclude_seniority: list[str] | None = None,
) -> Job | None:
    if is_excluded_level(job, exclude_levels):
        return None
    # Infopark = local Kochi board: show listings without Java/Spring or Lead/Architect gates.
    if job.region != "infopark":
        if is_excluded_seniority(job, exclude_seniority or []):
            return None
        if not matches_keywords(job, keywords):
            return None
    if exceeds_max_years(job, max_years):
        return None
    if requires_excluded_education(job, exclude_education or []):
        return None

    if job.region in ("eu", "uae"):
        board_ok = job.source in sponsorship_board_ids
        kw_ok = has_sponsorship_signal(job, sponsorship_keywords)
        if not (board_ok or kw_ok):
            return None
        job.sponsorship = True
    else:
        # India / Infopark / Remote: no sponsorship gate
        job.sponsorship = False

    return job


def dedupe_by_url(jobs: list[Job]) -> list[Job]:
    seen: set[str] = set()
    out: list[Job] = []
    for j in jobs:
        key = (j.url or "").strip().lower().split("?")[0]
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


def parse_relative_posted(text: str | None) -> str | None:
    """Best-effort: 'Posted Yesterday' / 'Posted 3 Days Ago' -> YYYY-MM-DD."""
    if not text:
        return None
    t = text.strip().lower()
    today = datetime.now(timezone.utc).date()
    if "today" in t or "just now" in t or "hours ago" in t or "hour ago" in t:
        return today.isoformat()
    if "yesterday" in t:
        return (today.fromordinal(today.toordinal() - 1)).isoformat()
    m = re.search(r"(\d+)\s+days?\s+ago", t)
    if m:
        days = int(m.group(1))
        return (today.fromordinal(today.toordinal() - days)).isoformat()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return None
