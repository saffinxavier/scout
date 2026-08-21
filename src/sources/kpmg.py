from __future__ import annotations

from .html_careers import make_html_fetcher

SOURCE_ID = "kpmg"
fetch = make_html_fetcher(SOURCE_ID)
