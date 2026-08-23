from __future__ import annotations

import ssl
from typing import Any

import httpx

# Shared client helpers. verify_ssl=False is intentional for flaky career CDNs on Windows.


def make_client(cfg: dict[str, Any]) -> httpx.Client:
    http = cfg.get("http") or {}
    timeout = float(http.get("timeout_seconds", 30))
    verify = bool(http.get("verify_ssl", True))
    headers = {
        "User-Agent": http.get(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ),
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    return httpx.Client(timeout=timeout, verify=verify, headers=headers, follow_redirects=True)


def get_text(client: httpx.Client, url: str) -> str:
    r = client.get(url)
    r.raise_for_status()
    return r.text


def get_json(client: httpx.Client, url: str) -> Any:
    r = client.get(url)
    r.raise_for_status()
    return r.json()


def post_json(client: httpx.Client, url: str, body: dict[str, Any]) -> Any:
    r = client.post(url, json=body, headers={"Content-Type": "application/json"})
    r.raise_for_status()
    return r.json()


# Silence unused ssl import warning if tooling complains — kept for future pin options.
_ = ssl
