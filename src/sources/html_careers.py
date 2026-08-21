"""Generic HTML careers page scraper for India employers without a public JSON API."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from ..models import Job

_JOBISH = re.compile(
    r"(job|career|requisition|vacanc|opportunity|position|/roles/|/search/)",
    re.I,
)


def fetch_html_jobs(
    client: httpx.Client,
    *,
    source_id: str,
    company: str,
    search_url: str,
    region: str = "india",
) -> list[Job]:
    r = client.get(search_url)
    if r.status_code == 404:
        raise RuntimeError(
            f"{source_id}: careers URL returned 404. Update search_url in config.yaml "
            f"(current: {search_url})"
        )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    jobs: list[Job] = []
    seen: set[str] = set()
    host = urlparse(search_url).netloc

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = href if href.startswith("http") else urljoin(search_url, href)
        if urlparse(full).netloc and host not in urlparse(full).netloc and "myworkdayjobs" not in full:
            # allow workday redirects
            if not any(x in full for x in ("workday", "oraclecloud", "taleo", "successfactors", "phenom")):
                continue
        if not _JOBISH.search(full):
            continue
        title = a.get_text(" ", strip=True)
        if not title or len(title) < 5:
            continue
        skip = {"learn more", "read more", "apply", "view job", "search", "home", "cookies"}
        if title.lower() in skip:
            continue
        # Prefer titles that look like roles
        if not re.search(r"(engineer|developer|java|spring|software|analyst|architect)", title, re.I):
            if not re.search(r"(engineer|developer|java|spring|software)", full, re.I):
                continue
        key = full.split("?")[0].lower()
        if key in seen:
            continue
        seen.add(key)

        parent = a.find_parent(["article", "li", "tr", "div"])
        location = "India"
        if parent:
            text = parent.get_text(" ", strip=True)
            loc_m = re.search(
                r"\b(India|Mumbai|Bengaluru|Bangalore|Hyderabad|Pune|Chennai|"
                r"Gurgaon|Gurugram|Noida|Remote)\b",
                text,
                re.I,
            )
            if loc_m:
                location = loc_m.group(1)

        jobs.append(
            Job(
                title=title[:180],
                company=company,
                location=location,
                url=full,
                source=source_id,
                region=region,
                sponsorship=False,
                description=title,
            )
        )
    return jobs


def make_html_fetcher(source_id: str):
    def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
        url = source_cfg.get("search_url")
        if not url:
            raise RuntimeError(f"{source_id}: search_url missing in config")
        company = source_cfg.get("company") or source_id
        return fetch_html_jobs(
            client,
            source_id=source_id,
            company=company,
            search_url=url,
            region=source_cfg.get("region") or "india",
        )

    fetch.__name__ = f"fetch_{source_id}"
    return fetch
