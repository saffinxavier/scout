from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..models import Job

SOURCE_ID = "relocate_me"
BASE = "https://relocate.me"
# Search SSR ignores ?page=; international-jobs paginates for real.
INTL_URL = "https://relocate.me/international-jobs"
MAX_INTL_PAGES = 8

_JOB_PATH = re.compile(
    r"^/(?P<country>[a-z-]+)/(?P<city>[a-z0-9-]+)/(?P<company>[a-z0-9-]+)/(?P<slug>.+)-(?P<id>\d+)$",
    re.I,
)


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    search_url = source_cfg.get("search_url") or "https://relocate.me/search?query=java%20spring"
    max_intl = int(source_cfg.get("max_pages") or MAX_INTL_PAGES)
    jobs: list[Job] = []
    seen: set[str] = set()

    # Keyword-scoped search (single SSR page — paging param is a no-op on this route).
    try:
        r = client.get(search_url)
        r.raise_for_status()
        _parse_page(r.text, jobs, seen)
    except Exception:
        pass

    # Full board pages that actually change results.
    empty_streak = 0
    for page in range(1, max_intl + 1):
        url = INTL_URL if page == 1 else f"{INTL_URL}?page={page}"
        try:
            r = client.get(url)
            r.raise_for_status()
        except Exception:
            break
        before = len(seen)
        _parse_page(r.text, jobs, seen)
        if len(seen) == before:
            empty_streak += 1
            if empty_streak >= 2:
                break
        else:
            empty_streak = 0

    return jobs


def _parse_page(html: str, jobs: list[Job], seen: set[str]) -> None:
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        path = href.replace(BASE, "") if href.startswith("http") else href
        m = _JOB_PATH.match(path.split("?")[0])
        if not m:
            continue
        full = urljoin(BASE, path.split("?")[0])
        if full in seen:
            continue
        seen.add(full)

        country = m.group("country").replace("-", " ").title()
        city = m.group("city").replace("-", " ").title()
        company = m.group("company").replace("-", " ").title()
        slug = m.group("slug").replace("-", " ").strip()
        title = a.get_text(" ", strip=True) or slug.title()
        if len(title) < 3:
            title = slug.title()

        jobs.append(
            Job(
                title=title,
                company=company,
                location=f"{city}, {country}",
                url=full,
                source=SOURCE_ID,
                region="eu",
                sponsorship=True,
                posted_at=None,
                description=f"{title} java spring boot {slug}",
            )
        )
