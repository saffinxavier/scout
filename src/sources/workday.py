from __future__ import annotations

from typing import Any

import httpx

from ..filters import parse_relative_posted
from ..models import Job


def fetch_workday(
    client: httpx.Client,
    source_cfg: dict[str, Any],
    *,
    source_id: str,
    default_tenant: str,
    default_shard: str,
    default_site: str,
) -> list[Job]:
    wd = source_cfg.get("workday") or {}
    tenant = wd.get("tenant", default_tenant)
    shard = wd.get("shard", default_shard)
    site = wd.get("site", default_site)
    keyword = wd.get("keyword") or source_cfg.get("keyword") or "Java"
    location_substr = [x.lower() for x in (wd.get("location_substr") or ["india"])]
    # Walk enough of the global Java search that India rows aren't stranded past page 1.
    max_results = int(wd.get("max_results", 500))

    api = f"https://{tenant}.{shard}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    base = f"https://{tenant}.{shard}.myworkdayjobs.com/{site}"

    jobs: list[Job] = []
    seen: set[str] = set()
    offset = 0
    limit = 20
    total = None
    while True:
        body = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": keyword,
        }
        data = client.post(api, json=body).json()
        if total is None:
            total = int(data.get("total") or 0)
        postings = data.get("jobPostings") or []
        if not postings:
            break
        for p in postings:
            loc = p.get("locationsText") or ""
            loc_l = loc.lower()
            title = p.get("title") or ""
            if location_substr:
                loc_ok = any(s in loc_l for s in location_substr)
                title_ok = any(s in title.lower() for s in location_substr) or title.startswith("IN_")
                if not (loc_ok or title_ok):
                    continue
            path = p.get("externalPath") or ""
            url = f"{base}{path}" if path.startswith("/") else path
            key = url.split("?")[0].lower()
            if not key or key in seen:
                continue
            seen.add(key)
            jobs.append(
                Job(
                    title=title,
                    company=source_cfg.get("company") or source_id,
                    location=loc or "India",
                    url=url,
                    source=source_id,
                    region=source_cfg.get("region") or "india",
                    sponsorship=False,
                    posted_at=parse_relative_posted(p.get("postedOn")),
                    description=title,
                )
            )
        offset += limit
        if offset >= min(total or 0, max_results):
            break
        if len(postings) < limit:
            break
    return jobs
