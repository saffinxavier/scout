from __future__ import annotations

from typing import Any

import httpx

from ..models import Job
from .workday import fetch_workday

SOURCE_ID = "pwc"


def fetch(client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
    return fetch_workday(
        client,
        source_cfg,
        source_id=SOURCE_ID,
        default_tenant="pwc",
        default_shard="wd3",
        default_site="Global_Experienced_Careers",
    )
