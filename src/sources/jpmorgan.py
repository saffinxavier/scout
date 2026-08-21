from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from ..models import Job

SOURCE_ID = "jpmorgan"
API = (
    "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
    "?onlyData=true&expand=requisitionList.secondaryLocations,flexFieldsFacet.values"
    "&finder=findReqs;siteNumber=CX_1001,facetsList=LOCATIONS%3BWORK_LOCATIONS%3BWORK_LOCATIONS_CIRCLE"
    "%3BWORK_LEVEL%3BTITLE%3BJOB_FAMILY%3BJOB_FUNCTION%3BORGANIZATION%3BDISTANCE%3BPOSTING_DATES"
    "%3BHOT_JOB%3BJOB_NUMBER,limit={limit},offset={offset},keyword={keyword},location=India"
)
DETAIL = (
    "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/{job_id}"
)
PAGE_SIZE = 50


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    keyword = quote(source_cfg.get("keyword") or "Java", safe="")
    jobs: list[Job] = []
    seen: set[str] = set()
    offset = 0
    total = None

    while True:
        url = API.format(limit=PAGE_SIZE, offset=offset, keyword=keyword)
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
            title = row.get("Title") or ""
            job_id = str(row.get("Id") or "")
            if not job_id or job_id in seen:
                continue
            seen.add(job_id)
            location = row.get("PrimaryLocation") or "India"
            posted = (row.get("PostedDate") or "")[:10] or None
            jobs.append(
                Job(
                    title=title,
                    company=source_cfg.get("company") or "JPMorgan Chase",
                    location=location,
                    url=DETAIL.format(job_id=job_id),
                    source=SOURCE_ID,
                    region="india",
                    sponsorship=False,
                    posted_at=posted,
                    description=title,
                )
            )
        offset += PAGE_SIZE
        if total is not None and offset >= total:
            break
        if len(reqs) < PAGE_SIZE:
            break

    return jobs
