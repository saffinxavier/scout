from __future__ import annotations

from typing import Any, Protocol

import httpx

from ..models import Job


class SourceAdapter(Protocol):
    id: str

    def fetch(self, client: httpx.Client, source_cfg: dict[str, Any], app_cfg: dict[str, Any]) -> list[Job]:
        ...
