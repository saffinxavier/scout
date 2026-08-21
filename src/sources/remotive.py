from __future__ import annotations

import re
from typing import Any

import httpx

from ..models import Job

SOURCE_ID = "remotive"
API = "https://remotive.com/api/remote-jobs?category=software-dev&search=java"

_EU_HINT = re.compile(
    r"\b(europe|eu|netherlands|germany|ireland|spain|portugal|sweden|denmark|"
    r"belgium|france|poland|austria|finland|italy|worldwide|anywhere|utc)\b",
    re.I,
)


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    data = client.get(API).json()
    rows = data.get("jobs") or []
    jobs: list[Job] = []
    for row in rows:
        loc = row.get("candidate_required_location") or row.get("location") or "Remote"
        if not _EU_HINT.search(str(loc)) and not _EU_HINT.search(row.get("description") or ""):
            # still allow if description mentions sponsorship/relocation for EU move
            desc = (row.get("description") or "").lower()
            if not any(x in desc for x in ("visa", "sponsorship", "relocation", "europe", "eu ")):
                continue
        url = row.get("url") or ""
        if not url:
            continue
        posted = (row.get("publication_date") or "")[:10] or None
        jobs.append(
            Job(
                title=row.get("title") or "",
                company=row.get("company_name") or "Unknown",
                location=f"Remote ({loc})",
                url=url,
                source=SOURCE_ID,
                region="eu",
                sponsorship=False,
                posted_at=posted,
                description=row.get("description") or "",
            )
        )
    return jobs
