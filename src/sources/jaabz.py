from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup

from ..models import Job

SOURCE_ID = "jaabz"
BASE = "https://jaabz.com"
MAX_PAGES = 10


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    base_url = source_cfg.get("search_url") or "https://jaabz.com/jobs?q=java+spring&visa=1"
    max_pages = int(source_cfg.get("max_pages") or MAX_PAGES)
    jobs: list[Job] = []
    seen: set[str] = set()
    empty_streak = 0

    for page in range(1, max_pages + 1):
        url = _with_page(base_url, page)
        try:
            r = client.get(url)
            r.raise_for_status()
        except Exception:
            break
        before = len(seen)
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not re.search(r"/jobs/\d+-", href):
                continue
            full = href if href.startswith("http") else urljoin(BASE, href)
            key = full.split("?")[0].lower()
            if key in seen:
                continue
            seen.add(key)

            title = a.get_text(" ", strip=True)
            if not title or len(title) < 3:
                slug = full.rstrip("/").split("/")[-1]
                slug = re.sub(r"^\d+-", "", slug).replace("-", " ")
                title = slug.title()

            parent = a.find_parent(["article", "div", "li", "tr"])
            company = "Unknown"
            location = "Europe"
            if parent:
                text = parent.get_text(" ", strip=True)
                company = _guess_company(text, title) or company
                loc_m = re.search(
                    r"\b(Netherlands|Germany|Ireland|Spain|Portugal|Sweden|Denmark|"
                    r"Belgium|France|Poland|Austria|Finland|Italy|Remote)\b",
                    text,
                    re.I,
                )
                if loc_m:
                    location = loc_m.group(1)

            jobs.append(
                Job(
                    title=title,
                    company=company,
                    location=location,
                    url=full,
                    source=SOURCE_ID,
                    region="eu",
                    sponsorship=True,
                    description=f"{title} java spring boot visa sponsorship",
                )
            )
        if len(seen) == before:
            empty_streak += 1
            if empty_streak >= 2:
                break
        else:
            empty_streak = 0

    return jobs


def _with_page(url: str, page: int) -> str:
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    if page <= 1:
        q.pop("page", None)
    else:
        q["page"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def _guess_company(blob: str, title: str) -> str | None:
    rest = blob.replace(title, "", 1).strip()
    if not rest:
        return None
    part = re.split(r"\b(?:Netherlands|Germany|Remote|Visa|Full|Part)\b", rest, maxsplit=1, flags=re.I)[0]
    part = part.strip(" -\u2013|,")
    if 2 <= len(part) <= 80:
        return part
    return None
