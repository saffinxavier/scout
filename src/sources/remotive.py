from __future__ import annotations

import re
from typing import Any

import httpx

from ..models import Job

REMOTIVE_API = "https://remotive.com/api/remote-jobs?category=software-dev&search=java"
# Remotive.com JSON ignores search and only returns ~20 mixed jobs. Jobicy's public
# Java feed is the working remote-JSON we can actually filter.
JOBICY_API = "https://jobicy.com/api/v2/remote-jobs?tag=java&count=100"

_EU_HINT = re.compile(
    r"\b(europe|eu|netherlands|germany|ireland|spain|portugal|sweden|denmark|"
    r"belgium|france|poland|austria|finland|italy|worldwide|anywhere|utc|emea)\b",
    re.I,
)
# India-eligible remote: India / APAC / Asia / worldwide — not US- or Europe-only.
_INDIA_ELIGIBLE = re.compile(
    r"\b(india|indian|apac|asia|asian|worldwide|anywhere|utc|global)\b",
    re.I,
)
_JAVA_TITLE = re.compile(r"(?<![a-z])java(?![a-z])|spring\s*boot|springboot", re.I)
_JAVASCRIPT = re.compile(r"javascript|java\s*script", re.I)


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    last_err: Exception | None = None
    region = source_cfg.get("region") or "eu"
    geo = source_cfg.get("geo") or ("india_eligible" if region == "remote" else "eu")
    source_id = source_cfg.get("id") or "remotive"

    try:
        r = client.get(REMOTIVE_API)
        r.raise_for_status()
        add_remotive_rows(r.json(), jobs, seen, region=region, geo=geo, source_id=source_id)
    except Exception as e:
        last_err = e

    try:
        r = client.get(JOBICY_API)
        r.raise_for_status()
        add_jobicy_rows(r.json(), jobs, seen, region=region, geo=geo, source_id=source_id)
    except Exception as e:
        last_err = e

    if not jobs and last_err is not None and not seen:
        # Both GETs failed — real transport problem.
        raise last_err
    return jobs


def add_remotive_rows(
    data: dict[str, Any],
    jobs: list[Job],
    seen: set[str],
    *,
    region: str,
    geo: str,
    source_id: str,
) -> None:
    for row in data.get("jobs") or []:
        title = row.get("title") or ""
        if not is_java_title(title):
            continue
        loc = row.get("candidate_required_location") or row.get("location") or "Remote"
        desc = row.get("description") or ""
        if not geo_ok(str(loc), desc, geo):
            continue
        url = row.get("url") or ""
        _append(
            jobs,
            seen,
            title=title,
            company=row.get("company_name") or "Unknown",
            location=f"Remote ({loc})",
            url=url,
            posted=(row.get("publication_date") or "")[:10] or None,
            description=desc,
            region=region,
            source_id=source_id,
        )


def add_jobicy_rows(
    data: dict[str, Any],
    jobs: list[Job],
    seen: set[str],
    *,
    region: str,
    geo: str,
    source_id: str,
) -> None:
    for row in data.get("jobs") or []:
        title = row.get("jobTitle") or ""
        if not is_java_title(title):
            continue
        loc = row.get("jobGeo") or "Remote"
        desc = row.get("jobDescription") or row.get("jobExcerpt") or ""
        if not geo_ok(str(loc), desc, geo):
            continue
        url = row.get("url") or ""
        posted = (row.get("pubDate") or "")[:10] or None
        _append(
            jobs,
            seen,
            title=title,
            company=row.get("companyName") or "Unknown",
            location=f"Remote ({loc})",
            url=url,
            posted=posted,
            description=desc,
            region=region,
            source_id=source_id,
        )


def _append(
    jobs: list[Job],
    seen: set[str],
    *,
    title: str,
    company: str,
    location: str,
    url: str,
    posted: str | None,
    description: str,
    region: str,
    source_id: str,
) -> None:
    if not url:
        return
    key = url.split("?")[0].lower()
    if key in seen:
        return
    seen.add(key)
    jobs.append(
        Job(
            title=title,
            company=company,
            location=location,
            url=url,
            source=source_id,
            region=region,
            sponsorship=False,
            posted_at=posted,
            description=description,
        )
    )


def geo_ok(loc: str, desc: str, geo: str) -> bool:
    if geo == "india_eligible":
        return india_eligible_ok(loc, desc)
    return _eu_ok(loc, desc)


def _eu_ok(loc: str, desc: str) -> bool:
    return bool(_EU_HINT.search(loc) or _EU_HINT.search(desc))


def india_eligible_ok(loc: str, desc: str = "") -> bool:
    """Keep India / APAC / Asia / worldwide; drop US- or Europe-only geos."""
    loc = (loc or "").strip()
    if not loc or loc.lower() in ("remote", "n/a", "none", "-", "null"):
        return True
    if _INDIA_ELIGIBLE.search(loc):
        return True
    # Light desc check only for explicit worldwide/India signals (avoid false positives).
    if _INDIA_ELIGIBLE.search(desc[:800] or ""):
        return True
    return False


def india_eligible_countries(countries: list[str] | None) -> bool:
    """Himalayas-style locationRestrictions: empty = worldwide; must allow India/APAC/Asia."""
    if not countries:
        return True
    blob = ", ".join(str(c) for c in countries if c)
    return india_eligible_ok(blob, "")


def is_java_title(title: str) -> bool:
    if _JAVASCRIPT.search(title) and not re.search(r"(?<![a-z])java(?![a-z])", title, re.I):
        return False
    return bool(_JAVA_TITLE.search(title))
