from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..models import Job

SOURCE_ID = "ey"
BASE = "https://careers.ey.com"
RSS = "https://careers.ey.com/services/rss/job/?locale=en_US&keywords=(Java)%20AND%20locationSearch:(India)"
SEARCH = "https://careers.ey.com/ey/search/?q=Java&location=India&startrow={start}"
MAX_PAGES = 8
PAGE_SIZE = 25

_INDIA_LOC = re.compile(
    r"\b(Bengaluru|Bangalore|Hyderabad|Pune|Mumbai|Chennai|Delhi|Gurgaon|Gurugram|"
    r"Noida|Kolkata|Ahmedabad|Kochi|India|IN)\b",
    re.I,
)
_US_BLOCK = re.compile(
    r"\b(United States|USA|New York|Texas|California|Chicago|Atlanta|Boston|Seattle|"
    r"San Francisco|Dallas|Austin|Remote - US|US-only)\b",
    re.I,
)


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    by_url: dict[str, Job] = {}
    for job in _from_rss(client, source_cfg):
        if _is_india_job(job):
            by_url[job.url.split("?")[0].lower()] = job
    for job in _from_search_pages(client, source_cfg):
        key = job.url.split("?")[0].lower()
        if key not in by_url and _is_india_job(job):
            by_url[key] = job
    return list(by_url.values())


def _is_india_job(job: Job) -> bool:
    url = (job.url or "").lower()
    if "careers.ey.com" not in url:
        return False
    blob = f"{job.title} {job.description} {job.location} {job.url}"
    if _US_BLOCK.search(blob) and not _INDIA_LOC.search(blob):
        return False
    return bool(_INDIA_LOC.search(blob))


def _from_rss(client: httpx.Client, source_cfg: dict[str, Any]) -> list[Job]:
    url = source_cfg.get("rss_url") or RSS
    r = client.get(url)
    r.raise_for_status()
    try:
        root = ET.fromstring(r.text)
    except ET.ParseError:
        return []

    jobs: list[Job] = []
    seen: set[str] = set()
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        if not title or not link:
            continue
        if "careers.ey.com" not in link.lower():
            continue
        key = link.split("?")[0].lower()
        if key in seen:
            continue
        seen.add(key)
        jobs.append(
            Job(
                title=title,
                company=source_cfg.get("company") or "EY",
                location=_location_from(title, desc, link),
                url=link,
                source=SOURCE_ID,
                region="india",
                sponsorship=False,
                posted_at=_rss_date(pub),
                description=f"{title} {desc}",
            )
        )
    return jobs


def _from_search_pages(client: httpx.Client, source_cfg: dict[str, Any]) -> list[Job]:
    max_pages = int(source_cfg.get("max_pages") or MAX_PAGES)
    search_tpl = (
        source_cfg.get("search_url")
        or "https://careers.ey.com/ey/search/?q=Java&location=India"
    )
    if "startrow=" not in search_tpl:
        sep = "&" if "?" in search_tpl else "?"
        search_tpl = f"{search_tpl}{sep}startrow={{start}}"
    elif "{start}" not in search_tpl:
        search_tpl = re.sub(r"startrow=\d+", "startrow={start}", search_tpl)

    jobs: list[Job] = []
    seen: set[str] = set()
    for page in range(max_pages):
        start = page * PAGE_SIZE
        r = client.get(search_tpl.format(start=start))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        before = len(seen)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/job/" not in href:
                continue
            full = urljoin(BASE, href).split("?")[0]
            if "careers.ey.com" not in full.lower():
                continue
            key = full.lower()
            if key in seen:
                continue
            title = a.get_text(" ", strip=True)
            if not title or len(title) < 5:
                continue
            seen.add(key)
            jobs.append(
                Job(
                    title=title,
                    company=source_cfg.get("company") or "EY",
                    location=_location_from(title, "", full),
                    url=full,
                    source=SOURCE_ID,
                    region="india",
                    sponsorship=False,
                    description=title,
                )
            )
        if len(seen) == before:
            break
    return jobs


def _location_from(title: str, desc: str, url: str) -> str:
    blob = f"{title} {desc} {url}"
    m = re.search(
        r"\b(Bengaluru|Bangalore|Hyderabad|Pune|Mumbai|Chennai|Delhi|Gurgaon|Gurugram|"
        r"Noida|Kolkata|Ahmedabad|Kochi)\b",
        blob,
        re.I,
    )
    return m.group(1) if m else "India"


def _rss_date(raw: str) -> str | None:
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except Exception:
        return None
