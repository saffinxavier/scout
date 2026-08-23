from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup

from ..models import Job

SOURCE_ID = "relocate_me"
BASE = "https://relocate.me"
# /search?query= redirects to the unfiltered board and drops the query.
SEARCH_URL = "https://relocate.me/international-jobs?query=java"
MAX_PAGES = 8

_JOB_PATH = re.compile(
    r"^/(?P<country>[a-z-]+)/(?P<city>[a-z0-9-]+)/(?P<company>[a-z0-9-]+)/(?P<slug>.+)-(?P<id>\d+)$",
    re.I,
)
_AD_TITLE = re.compile(r"curated|paid option|the global move", re.I)
_EU_COUNTRIES = {
    "netherlands",
    "germany",
    "ireland",
    "spain",
    "portugal",
    "sweden",
    "denmark",
    "belgium",
    "france",
    "poland",
    "austria",
    "finland",
    "italy",
    "lithuania",
    "estonia",
    "latvia",
    "czechia",
    "czech republic",
    "slovakia",
    "hungary",
    "romania",
    "bulgaria",
    "greece",
    "croatia",
    "slovenia",
    "cyprus",
    "malta",
    "luxembourg",
    "switzerland",
    "norway",
    "united kingdom",
    "uk",
    "england",
    "scotland",
    "iceland",
    "remote",
}


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    search_url = source_cfg.get("search_url") or SEARCH_URL
    max_pages = int(source_cfg.get("max_pages") or MAX_PAGES)
    source_id = str(source_cfg.get("id") or SOURCE_ID)
    region = str(source_cfg.get("region") or "eu")
    country_slug = (source_cfg.get("country_slug") or "").strip().lower() or None
    jobs: list[Job] = []
    seen: set[str] = set()
    empty_streak = 0
    last_err: Exception | None = None

    for page in range(1, max_pages + 1):
        url = search_url if page <= 1 else _with_page(search_url, page)
        try:
            r = client.get(url)
            r.raise_for_status()
        except Exception as e:
            last_err = e
            break
        before = len(seen)
        parse_listing(
            r.text,
            jobs,
            seen,
            source_id=source_id,
            region=region,
            country_slug=country_slug,
        )
        if len(seen) == before:
            empty_streak += 1
            if empty_streak >= 2:
                break
        else:
            empty_streak = 0

    if not jobs and last_err is not None:
        raise last_err
    return jobs


def parse_listing(
    html: str,
    jobs: list[Job],
    seen: set[str],
    *,
    source_id: str = SOURCE_ID,
    region: str = "eu",
    country_slug: str | None = None,
) -> None:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("div.jobs-list__job, div.jobs-list__job")
    if cards:
        for card in cards:
            a = card.find("a", href=True)
            if not a:
                continue
            title_el = card.select_one(".job__title, .job__title")
            preview_el = card.select_one(".job__preview, .job__preview")
            title = _clean_title(title_el.get_text(" ", strip=True) if title_el else "")
            preview = preview_el.get_text(" ", strip=True) if preview_el else ""
            _add_job(
                a["href"],
                jobs,
                seen,
                title=title,
                extra=preview,
                source_id=source_id,
                region=region,
                country_slug=country_slug,
            )
        return
    for a in soup.find_all("a", href=True):
        _add_job(
            a["href"],
            jobs,
            seen,
            title=a.get_text(" ", strip=True),
            extra="",
            source_id=source_id,
            region=region,
            country_slug=country_slug,
        )


def _add_job(
    href: str,
    jobs: list[Job],
    seen: set[str],
    *,
    title: str,
    extra: str,
    source_id: str = SOURCE_ID,
    region: str = "eu",
    country_slug: str | None = None,
) -> None:
    path = href.replace(BASE, "") if href.startswith("http") else href
    m = _JOB_PATH.match(path.split("?")[0])
    if not m:
        return
    slug_country = m.group("country").lower()
    if country_slug:
        if slug_country != country_slug:
            return
    elif slug_country.replace("-", " ") not in _EU_COUNTRIES:
        return
    full = urljoin(BASE, path.split("?")[0])
    if full in seen:
        return

    city = m.group("city").replace("-", " ").title()
    company = m.group("company").replace("-", " ").title()
    slug = m.group("slug").replace("-", " ").strip()
    title = _clean_title(title) or slug.title()
    if _AD_TITLE.search(title) or _AD_TITLE.search(company):
        return
    seen.add(full)
    blob = f"{title} {extra}".strip()
    jobs.append(
        Job(
            title=title,
            company=company,
            location=f"{city}, {m.group('country').replace('-', ' ').title()}",
            url=full,
            source=source_id,
            region=region,
            sponsorship=True,
            posted_at=None,
            description=blob,
        )
    )


def _clean_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\s+in\s+[A-Z][A-Za-z\- ]+$", "", title)
    return title.strip()


def _with_page(url: str, page: int) -> str:
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q["page"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))
