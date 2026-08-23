from __future__ import annotations

import re
from typing import Any

import httpx

from ..models import Job

SOURCE_ID = "remotive"
REMOTIVE_API = "https://remotive.com/api/remote-jobs?category=software-dev&search=java"
# Remotive.com JSON ignores search and only returns ~20 mixed jobs. Jobicy's public
# Java feed is the working remote-JSON we can actually filter.
JOBICY_API = "https://jobicy.com/api/v2/remote-jobs?tag=java&count=100"

_EU_HINT = re.compile(
    r"\b(europe|eu|netherlands|germany|ireland|spain|portugal|sweden|denmark|"
    r"belgium|france|poland|austria|finland|italy|worldwide|anywhere|utc|emea)\b",
    re.I,
)
_JAVA_TITLE = re.compile(r"(?<![a-z])java(?![a-z])|spring\s*boot|springboot", re.I)
_JAVASCRIPT = re.compile(r"javascript|java\s*script", re.I)


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    last_err: Exception | None = None

    try:
        r = client.get(REMOTIVE_API)
        r.raise_for_status()
        add_remotive_rows(r.json(), jobs, seen)
    except Exception as e:
        last_err = e

    try:
        r = client.get(JOBICY_API)
        r.raise_for_status()
        add_jobicy_rows(r.json(), jobs, seen)
    except Exception as e:
        last_err = e

    if not jobs and last_err is not None and not seen:
        # Both GETs failed — real transport problem.
        raise last_err
    return jobs


def add_remotive_rows(data: dict[str, Any], jobs: list[Job], seen: set[str]) -> None:
    for row in data.get("jobs") or []:
        title = row.get("title") or ""
        if not is_java_title(title):
            continue
        loc = row.get("candidate_required_location") or row.get("location") or "Remote"
        desc = row.get("description") or ""
        if not _eu_ok(str(loc), desc):
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
        )


def add_jobicy_rows(data: dict[str, Any], jobs: list[Job], seen: set[str]) -> None:
    for row in data.get("jobs") or []:
        title = row.get("jobTitle") or ""
        if not is_java_title(title):
            continue
        loc = row.get("jobGeo") or "Remote"
        desc = row.get("jobDescription") or row.get("jobExcerpt") or ""
        if not _eu_ok(str(loc), desc):
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
            source=SOURCE_ID,
            region="eu",
            sponsorship=False,
            posted_at=posted,
            description=description,
        )
    )


def _eu_ok(loc: str, desc: str) -> bool:
    return bool(_EU_HINT.search(loc) or _EU_HINT.search(desc))


def is_java_title(title: str) -> bool:
    if _JAVASCRIPT.search(title) and not re.search(r"(?<![a-z])java(?![a-z])", title, re.I):
        return False
    return bool(_JAVA_TITLE.search(title))
