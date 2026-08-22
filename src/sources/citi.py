from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..models import Job

SOURCE_ID = "citi"
# Public Citi board is Phenom (jobs.citi.com), not the Workday CXS host.
RESULTS = "https://jobs.citi.com/search-jobs/results"
MAX_PAGES = 20


def _parse_results_html(html: str) -> tuple[list[tuple[str, str, str]], int]:
    soup = BeautifulSoup(html or "", "html.parser")
    root = soup.select_one("#search-results")
    total_pages = 1
    if root and root.get("data-total-pages"):
        try:
            total_pages = int(root["data-total-pages"])
        except ValueError:
            total_pages = 1
    rows: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for item in soup.select("li.sr-job-item"):
        a = item.select_one("a.sr-job-item__link[href]")
        if not a:
            continue
        title = a.get_text(" ", strip=True)
        href = a["href"]
        loc_el = item.select_one(".sr-job-location")
        loc = loc_el.get_text(" ", strip=True) if loc_el else "India"
        if not title or not href:
            continue
        key = href.split("?")[0].lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append((title, href, loc))
    return rows, total_pages


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    keyword = source_cfg.get("keyword") or (source_cfg.get("workday") or {}).get("keyword") or "Java"
    jobs: list[Job] = []
    seen: set[str] = set()
    total_pages = 1
    page = 1
    while page <= min(total_pages, MAX_PAGES):
        r = client.get(
            RESULTS,
            params={
                "ActiveFacetID": "0",
                "CurrentPage": str(page),
                "RecordsPerPage": "15",
                "Distance": "50",
                "RadiusUnitType": "0",
                "Keywords": keyword,
                "Location": "India",
                "Latitude": "12",
                "Longitude": "",
                "ShowRadius": "False",
                "SearchResultsModuleName": "Search Results",
                "SearchFiltersModuleName": "Search Filters",
                "SortCriteria": "5",
                "SortDirection": "1",
                "SearchType": "1",
                "LocationType": "2",
                "LocationPath": "1269750",
                "OrganizationIds": "287",
                "ResultsType": "0",
            },
            headers={
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://jobs.citi.com/search-jobs",
            },
        )
        r.raise_for_status()
        html = (r.json() or {}).get("results") or ""
        rows, total_pages = _parse_results_html(html)
        if not rows:
            break
        for title, href, loc in rows:
            url = urljoin("https://jobs.citi.com/", href)
            key = url.split("?")[0].lower()
            if key in seen:
                continue
            seen.add(key)
            jobs.append(
                Job(
                    title=title,
                    company=source_cfg.get("company") or "Citi",
                    location=loc or "India",
                    url=url,
                    source=SOURCE_ID,
                    region=source_cfg.get("region") or "india",
                    sponsorship=False,
                    posted_at=None,
                    description=title,
                )
            )
        page += 1
    return jobs
