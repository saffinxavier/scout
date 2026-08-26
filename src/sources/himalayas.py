from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from ..models import Job
from .remotive import india_eligible_countries, is_java_title

SOURCE_ID = "himalayas"
SEARCH_URL = "https://himalayas.app/jobs/api/search"
PAGE_SIZE = 20


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    region = source_cfg.get("region") or "remote"
    max_pages = int(source_cfg.get("max_pages") or 4)
    queries = source_cfg.get("queries") or ["java", "spring boot"]
    jobs: list[Job] = []
    seen: set[str] = set()

    search_passes: list[dict[str, Any]] = [{"q": q} for q in queries]
    # Extra India-country pass catches India-restricted remote roles.
    search_passes.append({"q": "java", "country": "IN"})

    for params_base in search_passes:
        for page in range(max_pages):
            offset = page * PAGE_SIZE
            params = {**params_base, "limit": PAGE_SIZE, "offset": offset}
            r = client.get(
                SEARCH_URL,
                params=params,
                headers={"User-Agent": "scout/1.0 (personal job aggregator)"},
            )
            r.raise_for_status()
            data = r.json()
            rows = data.get("jobs") or []
            if not rows:
                break
            for row in rows:
                _maybe_append(jobs, seen, row, region=region)
            total = int(data.get("totalCount") or 0)
            if offset + len(rows) >= total:
                break

    return jobs


def _maybe_append(
    jobs: list[Job],
    seen: set[str],
    row: dict[str, Any],
    *,
    region: str,
) -> None:
    title = row.get("title") or ""
    if not is_java_title(title):
        return
    countries = row.get("locationRestrictions")
    if isinstance(countries, list):
        if not india_eligible_countries(countries):
            return
        loc = "Remote (" + ", ".join(str(c) for c in countries) + ")" if countries else "Remote (Worldwide)"
    else:
        if not india_eligible_countries(None):
            return
        loc = "Remote (Worldwide)"

    url = row.get("applicationLink") or ""
    if not url:
        return
    key = url.split("?")[0].lower()
    if key in seen:
        return
    seen.add(key)

    posted = _pub_date(row.get("pubDate"))
    desc = row.get("description") or row.get("excerpt") or ""
    jobs.append(
        Job(
            title=title,
            company=row.get("companyName") or "Unknown",
            location=loc,
            url=url,
            source=SOURCE_ID,
            region=region,
            sponsorship=False,
            posted_at=posted,
            description=desc if isinstance(desc, str) else "",
        )
    )


def _pub_date(raw: Any) -> str | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        # Himalayas returns unix seconds
        try:
            return datetime.fromtimestamp(int(raw), tz=timezone.utc).strftime("%Y-%m-%d")
        except (OverflowError, OSError, ValueError):
            return None
    s = str(raw)
    return s[:10] if len(s) >= 10 else None
