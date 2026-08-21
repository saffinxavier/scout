from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..models import Job

SOURCE_ID = "infopark"
BASE = "https://infopark.in"
DEFAULT_URL = "https://infopark.in/companies-job"
# Infopark paginates ~20 jobs/page; Empay Java was on page 3, board has 20+ pages.
MAX_PAGES = 30


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    base_url = (source_cfg.get("search_url") or DEFAULT_URL).split("?")[0]
    max_pages = int(source_cfg.get("max_pages") or MAX_PAGES)
    jobs: list[Job] = []
    seen: set[str] = set()

    for page in range(1, max_pages + 1):
        url = base_url if page == 1 else f"{base_url}?page={page}"
        r = client.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table")
        if not table:
            break

        page_jobs = 0
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 4:
                continue
            posted_raw = cells[0].get_text(" ", strip=True)
            title = cells[1].get_text(" ", strip=True)
            company = cells[2].get_text(" ", strip=True)
            if not title:
                continue
            link = tr.find("a", href=True)
            href = link["href"] if link else url
            full = href if href.startswith("http") else urljoin(BASE, href)
            key = full.split("?")[0].lower()
            if key in seen:
                continue
            seen.add(key)
            page_jobs += 1
            jobs.append(
                Job(
                    title=title,
                    company=company or "Infopark company",
                    location="Infopark, Kochi",
                    url=full,
                    source=SOURCE_ID,
                    region="infopark",
                    sponsorship=False,
                    posted_at=_parse_infopark_date(posted_raw),
                    description=title,
                )
            )

        if page_jobs == 0:
            break

    return jobs


def _parse_infopark_date(raw: str) -> str | None:
    raw = (raw or "").strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None
