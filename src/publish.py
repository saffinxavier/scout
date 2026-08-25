"""Build a static folder for GitHub Pages (scan + copy UI + jobs.json)."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .config import ROOT
from .scan import load_merged_jobs, run_scan

WEB = ROOT / "web"
SITE_FILES = ("index.html", "app.js", "style.css", "config.js", "interview.js")


def write_static_site(dest: Path, *, scan: bool = True) -> dict:
    if scan:
        run_scan(region="all")
    dest.mkdir(parents=True, exist_ok=True)
    for name in SITE_FILES:
        shutil.copy2(WEB / name, dest / name)
    (dest / ".nojekyll").write_text("", encoding="utf-8")
    payload = load_merged_jobs()
    (dest / "jobs.json").write_text(json.dumps(payload), encoding="utf-8")
    return payload


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="_site")
    p.add_argument("--skip-scan", action="store_true")
    args = p.parse_args()
    dest = Path(args.out)
    if not dest.is_absolute():
        dest = ROOT / dest
    payload = write_static_site(dest, scan=not args.skip_scan)
    print(f"wrote {dest} ({payload['count']} jobs)")


if __name__ == "__main__":
    main()
