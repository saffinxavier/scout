from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..models import Job

SOURCE_ID = "deloitte"
BASE = "https://southasiacareers.deloitte.com"
RSS = "https://southasiacareers.deloitte.com/services/rss/job/?locale=en_US&keywords=(Java)"
SEARCH = "https://southasiacareers.deloitte.com/search/?q=Java&startrow={start}"
MAX_PAGES = 8
PAGE_SIZE = 25


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    by_url: dict[str, Job] = {}
    for job in _from_rss(client, source_cfg):
        by_url[job.url.split("?")[0].lower()] = job
    for job in _from_search_pages(client, source_cfg):
        key = job.url.split("?")[0].lower()
        if key not in by_url:
            by_url[key] = job
    return list(by_url.values())


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
        key = link.split("?")[0].lower()
        if key in seen:
            continue
        seen.add(key)
        jobs.append(
            Job(
                title=title,
                company=source_cfg.get("company") or "Deloitte",
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
    jobs: list[Job] = []
    seen: set[str] = set()
    for page in range(max_pages):
        start = page * PAGE_SIZE
        r = client.get(SEARCH.format(start=start))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        before = len(seen)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/job/" not in href:
                continue
            full = urljoin(BASE, href).split("?")[0]
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
                    company=source_cfg.get("company") or "Deloitte",
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
        r"Noida|Kolkata|Ahmedabad|Kochi|India)\b",
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
