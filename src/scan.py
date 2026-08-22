from __future__ import annotations

import importlib
import json
import pkgutil
from typing import Any

from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT, load_config
from .filters import dedupe_by_url, passes_filters
from .http_util import make_client
from .models import Job, SourceError

REGIONS = ("india", "eu", "infopark")
EMPTY_FETCH_MSG = "0 jobs returned (empty, blocked, or HTML adapter missed the board)"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _data_dir() -> Path:
    d = ROOT / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def region_jobs_path(region: str) -> Path:
    return _data_dir() / f"jobs-{region}.json"


def _url_key(job: dict[str, Any]) -> str:
    return (job.get("url") or "").strip().lower().split("?")[0]


def split_jobs_by_region(jobs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {r: [] for r in REGIONS}
    for j in jobs:
        r = j.get("region")
        if r in buckets:
            buckets[r].append(j)
    return buckets


def _read_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"count": 0, "jobs": [], "errors": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"count": 0, "jobs": [], "errors": []}
    jobs = data.get("jobs") or []
    errors = data.get("errors") or []
    generated_at = data.get("generated_at")
    if not generated_at:
        try:
            generated_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()
        except OSError:
            generated_at = None
    return {"count": len(jobs), "jobs": jobs, "errors": errors, "generated_at": generated_at}


def _write_region(region: str, jobs: list[dict[str, Any]], errors: list[dict[str, str]]) -> None:
    jobs = sorted(
        jobs,
        key=lambda j: (j.get("posted_at") or "", j.get("title") or ""),
        reverse=True,
    )
    payload = {
        "count": len(jobs),
        "jobs": jobs,
        "errors": errors,
        "region": region,
        "generated_at": _now_iso(),
    }
    region_jobs_path(region).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _source_region_map(cfg: dict[str, Any] | None = None) -> dict[str, str]:
    cfg = cfg or load_config()
    return {
        s["id"]: s.get("region") or ""
        for s in (cfg.get("sources") or [])
        if s.get("id")
    }


def _split_errors(
    errors: list[dict[str, str]], region_map: dict[str, str]
) -> dict[str, list[dict[str, str]]]:
    buckets: dict[str, list[dict[str, str]]] = {r: [] for r in REGIONS}
    for e in errors:
        r = region_map.get(e.get("source") or "")
        if r in buckets:
            buckets[r].append(e)
    return buckets


def migrate_legacy_jobs_json() -> None:
    """One-shot: split old data/jobs.json into per-region files if none exist yet."""
    legacy = _data_dir() / "jobs.json"
    if not legacy.exists():
        return
    if any(region_jobs_path(r).exists() for r in REGIONS):
        return
    data = _read_payload(legacy)
    buckets = split_jobs_by_region(data["jobs"])
    err_buckets = _split_errors(data["errors"], _source_region_map())
    for r in REGIONS:
        _write_region(r, buckets[r], err_buckets[r])


def load_merged_jobs() -> dict[str, Any]:
    migrate_legacy_jobs_json()
    jobs: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    seen: set[str] = set()
    stamps: list[str] = []
    for r in REGIONS:
        payload = _read_payload(region_jobs_path(r))
        if payload.get("generated_at"):
            stamps.append(payload["generated_at"])
        for j in payload["jobs"]:
            key = _url_key(j)
            if not key or key in seen:
                continue
            seen.add(key)
            jobs.append(j)
        errors.extend(payload["errors"])
    jobs.sort(key=lambda j: (j.get("posted_at") or "", j.get("title") or ""), reverse=True)
    return {
        "count": len(jobs),
        "jobs": jobs,
        "errors": errors,
        "generated_at": max(stamps) if stamps else None,
        "sources": source_catalog(),
    }


def save_jobs_snapshot(
    jobs: list[dict[str, Any]],
    errors: list[dict[str, str]],
    region: str = "all",
) -> None:
    region = (region or "all").strip().lower()
    err_buckets = _split_errors(errors, _source_region_map())
    if region in REGIONS:
        jobs = [j for j in jobs if j.get("region") == region]
        errs = err_buckets[region] if err_buckets[region] else errors
        _write_region(region, jobs, errs)
        return
    buckets = split_jobs_by_region(jobs)
    for r in REGIONS:
        _write_region(r, buckets[r], err_buckets[r])


def _registry():
    """Reload all source modules so adapter edits apply without restarting Flask."""
    from . import sources as sources_pkg

    for info in pkgutil.iter_modules(sources_pkg.__path__, sources_pkg.__name__ + "."):
        try:
            importlib.reload(importlib.import_module(info.name))
        except Exception:
            pass
    return importlib.reload(sources_pkg).REGISTRY


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


def source_catalog(cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    cfg = cfg or load_config()
    out: list[dict[str, Any]] = []
    for s in cfg.get("sources") or []:
        sid = s.get("id")
        if not sid:
            continue
        out.append(
            {
                "id": sid,
                "region": s.get("region") or "",
                "label": s.get("company") or sid,
                "enabled": bool(s.get("enabled", True)),
                "note": s.get("note") or "",
            }
        )
    return out


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
                raw_jobs = list(fetch(client, sc, cfg))
                if not raw_jobs:
                    errors.append(SourceError(source_id, EMPTY_FETCH_MSG))
                for j in raw_jobs:
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
                raw_jobs = list(fetch(client, sc, cfg))
                if not raw_jobs:
                    errors.append(SourceError(sid, EMPTY_FETCH_MSG))
                for j in raw_jobs:
                    kept = passes_filters(j, **fk)
                    if kept:
                        jobs.append(kept)
            except Exception as e:
                errors.append(SourceError(sid, str(e)))

    jobs = dedupe_by_url(jobs)
    jobs.sort(key=lambda j: (j.posted_at or "", j.title), reverse=True)

    job_dicts = [j.to_dict() for j in jobs]
    err_dicts = [e.to_dict() for e in errors]
    scanned = (region or "all").strip().lower()
    if scanned in REGIONS:
        save_jobs_snapshot(job_dicts, err_dicts, region=scanned)
    else:
        save_jobs_snapshot(job_dicts, err_dicts, region="all")

    return {
        "count": len(job_dicts),
        "jobs": job_dicts,
        "errors": err_dicts,
    }
