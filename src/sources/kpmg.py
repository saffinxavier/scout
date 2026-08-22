from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import httpx

from ..models import Job

SOURCE_ID = "kpmg"
HOST = "ejgk.fa.em2.oraclecloud.com"
SITES = ("CX_3001", "CX_3")
PAGE_SIZE = 50
DETAIL = (
    "https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{job_id}"
)
DETAIL_API = (
    "https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails"
    "?onlyData=true&finder=ById;Id={job_id},siteNumber={site}"
)
API = (
    "https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
    "?onlyData=true&expand=requisitionList.secondaryLocations,flexFieldsFacet.values"
    "&finder=findReqs;siteNumber={site},facetsList=LOCATIONS%3BTITLE,limit={limit},"
    "offset={offset},keyword={keyword}"
)

_INDIA = re.compile(
    r"\b(India|Bengaluru|Bangalore|Hyderabad|Pune|Mumbai|Chennai|Delhi|"
    r"Gurgaon|Gurugram|Noida|Kolkata|Kochi|Karnataka|Maharashtra|Telangana|"
    r"Haryana|Tamil Nadu|Uttar Pradesh)\b",
    re.I,
)


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    keyword = quote(source_cfg.get("keyword") or "Java", safe="")
    host = (source_cfg.get("oracle") or {}).get("host") or HOST
    sites = (source_cfg.get("oracle") or {}).get("sites") or list(SITES)
    jobs: list[Job] = []
    seen: set[str] = set()
    for site in sites:
        jobs.extend(_fetch_site(client, source_cfg, host, str(site), keyword, seen))
    return jobs


def _fetch_site(
    client: httpx.Client,
    source_cfg: dict[str, Any],
    host: str,
    site: str,
    keyword: str,
    seen: set[str],
) -> list[Job]:
    jobs: list[Job] = []
    offset = 0
    total = None
    while True:
        url = API.format(host=host, site=site, limit=PAGE_SIZE, offset=offset, keyword=keyword)
        data = client.get(url).json()
        items = data.get("items") or []
        if not items:
            break
        head = items[0]
        if total is None:
            total = int(head.get("TotalJobsCount") or 0)
        reqs = head.get("requisitionList") or []
        if not reqs:
            break
        for row in reqs:
            job = _row_to_job(row, source_cfg, host, site)
            if not job:
                continue
            key = job.url.split("?")[0].lower()
            if key in seen:
                continue
            seen.add(key)
            jobs.append(job)
        offset += PAGE_SIZE
        if total is not None and offset >= total:
            break
        if len(reqs) < PAGE_SIZE:
            break
    for job in jobs:
        _fill_description(client, job, host, site)
    return jobs


def _row_to_job(row: dict[str, Any], source_cfg: dict[str, Any], host: str, site: str) -> Job | None:
    title = (row.get("Title") or "").strip()
    job_id = str(row.get("Id") or "").strip()
    if not title or not job_id:
        return None
    location = (row.get("PrimaryLocation") or "").strip() or "India"
    if not _INDIA.search(f"{title} {location}"):
        return None
    extra = " ".join(
        str(row.get(k) or "")
        for k in (
            "ShortDescriptionStr",
            "ExternalDescriptionStr",
            "JobDescription",
            "Category",
            "JobFamily",
        )
    )
    posted = (row.get("PostedDate") or "")[:10] or None
    return Job(
        title=title,
        company=source_cfg.get("company") or "KPMG",
        location=location,
        url=DETAIL.format(host=host, site=site, job_id=job_id),
        source=SOURCE_ID,
        region="india",
        sponsorship=False,
        posted_at=posted,
        description=f"{title} {location} {extra}".strip(),
    )


def _fill_description(client: httpx.Client, job: Job, host: str, site: str) -> None:
    # ponytail: one extra GET per requisition (boards are small); drop this if we paginate to hundreds.
    job_id = job.url.rstrip("/").split("/")[-1]
    url = DETAIL_API.format(host=host, site=site, job_id=job_id)
    try:
        data = client.get(url).json()
    except Exception:
        return
    items = data.get("items") or []
    if not items:
        return
    row = items[0]
    parts = [
        job.title,
        job.location,
        row.get("ShortDescriptionStr") or "",
        row.get("ExternalDescriptionStr") or "",
        row.get("ExternalQualificationsStr") or "",
        row.get("ExternalResponsibilitiesStr") or "",
    ]
    job.description = " ".join(p for p in parts if p).strip()
    loc = (row.get("PrimaryLocation") or "").strip()
    if loc:
        job.location = loc
