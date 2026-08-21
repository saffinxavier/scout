from __future__ import annotations

from .html_careers import make_html_fetcher

SOURCE_ID = "morgan_stanley"
fetch = make_html_fetcher(SOURCE_ID)
