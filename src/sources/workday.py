from __future__ import annotations

from typing import Any

import httpx

from ..filters import parse_relative_posted
from ..models import Job


def _cxs_json(client: httpx.Client, api: str, body: dict[str, Any]) -> dict[str, Any]:
    # Per-request: a 303 to community.workday.com/maintenance-page has an empty body;
    # following it yields HTML and json() raises "Expecting value: line 1 column 1".
    r = client.post(
        api,
        json=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        follow_redirects=False,
    )
    loc = r.headers.get("location") or ""
    if r.status_code in (301, 302, 303, 307, 308):
        if "maintenance" in loc.lower() or "community.workday.com" in loc.lower():
            raise RuntimeError("Workday careers API is in maintenance. Try again later.")
        raise RuntimeError(f"Workday redirected ({r.status_code}) to {loc}")
    if not r.content:
        raise RuntimeError(f"Workday returned empty body (HTTP {r.status_code})")
    ctype = (r.headers.get("content-type") or "").lower()
    if "application/json" not in ctype:
        if "unavailable" in r.text.lower() or "maintenance" in r.text.lower():
            raise RuntimeError("Workday careers API is in maintenance. Try again later.")
        raise RuntimeError(f"Workday returned non-JSON ({r.status_code} {ctype or 'unknown'})")
    r.raise_for_status()
    return r.json()


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
        data = _cxs_json(client, api, body)
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
