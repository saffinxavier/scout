"""Static wiring check for the web UI. Run: python check_ui.py

Fails (non-zero exit) if index.html, app.js, interview.js, and style.css
disagree about ids/classes, so a refactor that breaks a lookup is caught
without opening a browser.
"""
import re
import sys
from pathlib import Path

WEB = Path(__file__).parent / "web"
html = (WEB / "index.html").read_text(encoding="utf-8")
css = (WEB / "style.css").read_text(encoding="utf-8")
js = (WEB / "app.js").read_text(encoding="utf-8") + (WEB / "interview.js").read_text(encoding="utf-8")

errors = []

# 1. Every id JS looks up must exist exactly once in the HTML.
html_ids = re.findall(r'id="([^"]+)"', html)
dupes = {i for i in html_ids if html_ids.count(i) > 1}
if dupes:
    errors.append(f"duplicate ids in index.html: {sorted(dupes)}")
for js_id in set(re.findall(r'getElementById\("([^"]+)"\)', js)):
    if js_id not in html_ids:
        errors.append(f"app js looks up #{js_id} but index.html has no such id")

# 2. Class/attribute selectors JS relies on must exist in the HTML.
for sel, pat in {
    ".js-open-filters": r'class="[^"]*js-open-filters',
    "[data-view]": r'data-view="',
    ".stack-chip": r'class="[^"]*stack-chip',
}.items():
    if not re.search(pat, html):
        errors.append(f"js selector {sel} matches nothing in index.html")

# 3. data-view values must be the two views interview.js knows.
if set(re.findall(r'data-view="([^"]+)"', html)) != {"jobs", "interview"}:
    errors.append("data-view values in index.html are not exactly jobs/interview")

# 4. New layout classes must be styled.
for cls in ["sidebar", "side-nav-btn", "menu-sheet", "menu-foot", "tabbar", "tab-btn"]:
    if f".{cls}" not in css:
        errors.append(f".{cls} used in index.html but not styled in style.css")

# 5. Old topbar artifacts must be fully gone everywhere.
for stale in ["filterToggle", "navJobsBtn", "navInterviewBtn", "view-nav", "topbar", "top-actions"]:
    for name, text in (("index.html", html), ("js", js), ("style.css", css)):
        if stale in text:
            errors.append(f"stale reference '{stale}' still present in {name}")

if errors:
    print("check_ui FAILED:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("check_ui passed")
