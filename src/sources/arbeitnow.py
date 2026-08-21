from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from ..models import Job

SOURCE_ID = "arbeitnow"
API = "https://www.arbeitnow.com/api/job-board-api"
MAX_PAGES = 8  # further pages often hit Cloudflare 429


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    max_pages = int(source_cfg.get("max_pages") or MAX_PAGES)
    url: str | None = API
    jobs: list[Job] = []
    seen: set[str] = set()
    pages = 0

    while url and pages < max_pages:
        r = client.get(url)
        pages += 1
        ctype = (r.headers.get("content-type") or "").lower()
        if r.status_code == 429 or "application/json" not in ctype:
            # Rate-limited / challenged — keep what we already have.
            break
        try:
            data = r.json()
        except Exception:
            break
        for row in data.get("data") or []:
            title = row.get("title") or ""
            company = row.get("company_name") or "Unknown"
            location = row.get("location") or "Europe"
            job_url = row.get("url") or ""
            if not job_url:
                slug = row.get("slug") or ""
                job_url = f"https://www.arbeitnow.com/jobs/{slug}" if slug else ""
            if not job_url:
                continue
            key = job_url.split("?")[0].lower()
            if key in seen:
                continue
            seen.add(key)
            desc = row.get("description") or ""
            tags = " ".join(row.get("tags") or [])
            posted = _epoch_to_date(row.get("created_at"))
            jobs.append(
                Job(
                    title=title,
                    company=company,
                    location=location,
                    url=job_url,
                    source=SOURCE_ID,
                    region="eu",
                    sponsorship=False,
                    posted_at=posted,
                    description=f"{desc} {tags}",
                )
            )
        url = (data.get("links") or {}).get("next")

    return jobs


def _epoch_to_date(value: Any) -> str | None:
    if value is None:
        return None
    try:
        ts = int(value)
        if ts > 10_000_000_000:
            ts //= 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    except Exception:
        return None
