from __future__ import annotations

from typing import Any

import httpx

from ..models import Job
from .workday import fetch_workday

SOURCE_ID = "citi"


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    return fetch_workday(
        client,
        source_cfg,
        source_id=SOURCE_ID,
        default_tenant="citi",
        default_shard="wd5",
        default_site="2",
    )
