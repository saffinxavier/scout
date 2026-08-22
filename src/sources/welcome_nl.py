from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..models import Job

SOURCE_ID = "welcome_nl"
# Config currently has this source disabled. Official board is Nuxt (welcome-to-nl.nl).
BASE = "https://www.welcome-to-nl.nl"


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    url = source_cfg.get("search_url") or f"{BASE}/jobs/"
    r = client.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    jobs: list[Job] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = href if href.startswith("http") else urljoin(BASE, href)
        if "welcome-to-nl.nl" not in full and "welcometothenetherlands.com" not in full:
            continue
        path = full.lower()
        if not any(x in path for x in ("vacature", "job", "career", "stage")):
            continue
        if path.rstrip("/") in {f"{BASE}/vacatures".lower(), f"{BASE}/".lower()}:
            continue
        if full in seen:
            continue
        title = a.get_text(" ", strip=True)
        if not title or len(title) < 4:
            continue
        if title.lower() in {"lees meer", "read more", "meer info", "cookies"}:
            continue
        seen.add(full)
        jobs.append(
            Job(
                title=title,
                company="Welcome to the Netherlands listing",
                location="Netherlands",
                url=full,
                source=SOURCE_ID,
                region="eu",
                sponsorship=True,
                description=title,
            )
        )

    # Keyword site search as fallback
    search_url = f"{BASE}/?s=java"
    try:
        r2 = client.get(search_url)
        if r2.status_code == 200:
            soup2 = BeautifulSoup(r2.text, "lxml")
            for a in soup2.select("article a, h2 a, h3 a"):
                href = a.get("href") or ""
                full = href if href.startswith("http") else urljoin(BASE, href)
                if full in seen or (
                    "welcome-to-nl.nl" not in full and "welcometothenetherlands.com" not in full
                ):
                    continue
                title = a.get_text(" ", strip=True)
                if len(title) < 4:
                    continue
                seen.add(full)
                jobs.append(
                    Job(
                        title=title,
                        company="Welcome to the Netherlands listing",
                        location="Netherlands",
                        url=full,
                        source=SOURCE_ID,
                        region="eu",
                        sponsorship=True,
                        description=title,
                    )
                )
    except Exception:
        pass

    return jobs
