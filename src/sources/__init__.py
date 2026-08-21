from __future__ import annotations

from typing import Any, Callable

import httpx

from ..models import Job
from . import (
    arbeitnow,
    citi,
    deloitte,
    ey,
    goldman_sachs,
    infopark,
    jaabz,
    jpmorgan,
    kpmg,
    morgan_stanley,
    pwc,
    relocate_me,
    remotive,
    welcome_nl,
)

FetchFn = Callable[[httpx.Client, dict[str, Any], dict[str, Any]], list[Job]]

REGISTRY: dict[str, FetchFn] = {
    "relocate_me": relocate_me.fetch,
    "welcome_nl": welcome_nl.fetch,
    "jaabz": jaabz.fetch,
    "arbeitnow": arbeitnow.fetch,
    "remotive": remotive.fetch,
    "infopark": infopark.fetch,
    "jpmorgan": jpmorgan.fetch,
    "citi": citi.fetch,
    "goldman_sachs": goldman_sachs.fetch,
    "morgan_stanley": morgan_stanley.fetch,
    "deloitte": deloitte.fetch,
    "pwc": pwc.fetch,
    "ey": ey.fetch,
    "kpmg": kpmg.fetch,
}
