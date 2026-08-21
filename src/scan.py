from __future__ import annotations

import importlib
import json
from typing import Any

from .config import ROOT, load_config
from .filters import dedupe_by_url, passes_filters
from .http_util import make_client
from .models import Job, SourceError


def _registry():
    """Reload adapters each scan so new sources apply without restart."""
    from . import sources as sources_pkg

    importlib.reload(sources_pkg)
    return sources_pkg.REGISTRY


def _filter_kwargs(cfg: dict[str, Any], source_cfgs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "keywords": list(cfg.get("keywords") or ["java", "spring boot"]),
        "exclude_levels": list(cfg.get("exclude_levels") or []),
        "sponsorship_keywords": list(cfg.get("sponsorship_keywords") or []),
        "sponsorship_board_ids": {
            s["id"] for s in source_cfgs if s.get("sponsorship_board") and s.get("region") == "eu"
        },
        "max_years": int(cfg.get("max_years") or 4),
        "exclude_education": list(cfg.get("exclude_education") or []),
        "exclude_seniority": list(cfg.get("exclude_seniority") or []),
    }


def list_sources(region: str | None = None, cfg: dict[str, Any] | None = None) -> list[dict[str, str]]:
    cfg = cfg or load_config()
    out = []
    for s in cfg.get("sources") or []:
        if not s.get("enabled", True) or not s.get("id"):
            continue
        if region and region != "all" and s.get("region") != region:
            continue
        out.append(
            {
                "id": s["id"],
                "region": s.get("region") or "",
                "company": s.get("company") or s["id"],
            }
        )
    return out


def scan_one(source_id: str, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fetch + filter a single source (for progressive UI scans)."""
    cfg = cfg or load_config()
    source_cfgs = [s for s in (cfg.get("sources") or []) if s.get("enabled", True)]
    sc = next((s for s in source_cfgs if s.get("id") == source_id), None)
    if not sc:
        return {
            "source": source_id,
            "jobs": [],
            "errors": [{"source": source_id, "message": "Unknown or disabled source"}],
        }

    fk = _filter_kwargs(cfg, source_cfgs)
    registry = _registry()
    fetch = registry.get(source_id)
    jobs: list[Job] = []
    errors: list[SourceError] = []

    if not fetch:
        errors.append(
            SourceError(source_id, f"No adapter registered (known: {', '.join(sorted(registry))})")
        )
    else:
        with make_client(cfg) as client:
            try:
                for j in fetch(client, sc, cfg):
                    kept = passes_filters(j, **fk)
                    if kept:
                        jobs.append(kept)
            except Exception as e:
                errors.append(SourceError(source_id, str(e)))

    jobs = dedupe_by_url(jobs)
    jobs.sort(key=lambda j: (j.posted_at or "", j.title), reverse=True)
    return {
        "source": source_id,
        "count": len(jobs),
        "jobs": [j.to_dict() for j in jobs],
        "errors": [e.to_dict() for e in errors],
    }


def run_scan(
    cfg: dict[str, Any] | None = None,
    *,
    region: str | None = None,
) -> dict[str, Any]:
    cfg = cfg or load_config()
    source_cfgs = [s for s in (cfg.get("sources") or []) if s.get("enabled", True)]
    if region and region != "all":
        source_cfgs = [s for s in source_cfgs if s.get("region") == region]

    fk = _filter_kwargs(cfg, [s for s in (cfg.get("sources") or []) if s.get("enabled", True)])
    registry = _registry()
    jobs: list[Job] = []
    errors: list[SourceError] = []

    with make_client(cfg) as client:
        for sc in source_cfgs:
            sid = sc.get("id")
            if not sid:
                continue
            fetch = registry.get(sid)
            if not fetch:
                errors.append(
                    SourceError(
                        sid,
                        f"No adapter registered (known: {', '.join(sorted(registry))})",
                    )
                )
                continue
            try:
                raw_jobs = fetch(client, sc, cfg)
                for j in raw_jobs:
                    kept = passes_filters(j, **fk)
                    if kept:
                        jobs.append(kept)
            except Exception as e:
                errors.append(SourceError(sid, str(e)))

    jobs = dedupe_by_url(jobs)
    jobs.sort(key=lambda j: (j.posted_at or "", j.title), reverse=True)

    payload = {
        "count": len(jobs),
        "jobs": [j.to_dict() for j in jobs],
        "errors": [e.to_dict() for e in errors],
    }

    out = ROOT / "data" / "jobs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def save_jobs_snapshot(jobs: list[dict[str, Any]], errors: list[dict[str, str]]) -> None:
    jobs = sorted(jobs, key=lambda j: (j.get("posted_at") or "", j.get("title") or ""), reverse=True)
    payload = {"count": len(jobs), "jobs": jobs, "errors": errors}
    out = ROOT / "data" / "jobs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
