from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .scan import list_sources, load_merged_jobs, run_scan, save_jobs_snapshot, scan_one, source_catalog

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

app = Flask(__name__, static_folder=str(WEB), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.get("/app.js")
def app_js():
    return send_from_directory(WEB, "app.js")


@app.get("/config.js")
def config_js():
    return send_from_directory(WEB, "config.js")


@app.get("/api/sources")
def api_sources():
    region = (request.args.get("region") or "all").strip().lower()
    if (request.args.get("catalog") or "").strip() in {"1", "true", "yes"}:
        return jsonify({"sources": source_catalog()})
    return jsonify({"sources": list_sources(region=region)})


@app.post("/api/scan/one")
def api_scan_one():
    body = request.get_json(silent=True) or {}
    source_id = (body.get("source_id") or "").strip()
    if not source_id:
        return jsonify({"source": "", "jobs": [], "errors": [{"source": "scan", "message": "source_id required"}]}), 400
    try:
        return jsonify(scan_one(source_id))
    except Exception as e:
        return jsonify(
            {"source": source_id, "count": 0, "jobs": [], "errors": [{"source": source_id, "message": str(e)}]}
        ), 500


@app.post("/api/scan")
def api_scan():
    body = request.get_json(silent=True) or {}
    region = (body.get("region") or request.args.get("region") or "all").strip().lower()
    try:
        payload = run_scan(region=region)
        return jsonify(payload)
    except Exception as e:
        return jsonify({"count": 0, "jobs": [], "errors": [{"source": "scan", "message": str(e)}]}), 500


@app.post("/api/jobs/save")
def api_jobs_save():
    body = request.get_json(silent=True) or {}
    jobs = body.get("jobs") or []
    errors = body.get("errors") or []
    region = (body.get("region") or "all").strip().lower()
    save_jobs_snapshot(jobs, errors, region=region)
    return jsonify({"ok": True, "count": len(jobs), "region": region})


@app.get("/api/jobs")
def api_jobs():
    payload = load_merged_jobs()
    if not payload["jobs"]:
        payload["message"] = "No scan yet. Click Scan now."
    return jsonify(payload)


def main():
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
