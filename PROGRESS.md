# Scout — Progress

Last updated: 2026-08-26

## Done
- [x] Local Flask app + `config.yaml` sources + dark job-board UI
- [x] Filters: keywords, max_years=4, education, seniority (config-driven), EU sponsorship rules
- [x] Infopark adapter with **full pagination** (fixed missing Empay Java on page 3+)
- [x] Pagination audit/fixes: JPM offset loop, Workday max_results 500, Jaabz pages, Arbeitnow pages, Relocate intl pages
- [x] Deloitte: South Asia only (`southasiacareers.deloitte.com` + India location gate); rejects `apply.deloitte.com` US URLs; adapter modules fully reloaded each scan
- [x] Progressive scan: `/api/sources` + `/api/scan/one` — loads sources **one-by-one** for selected region only
- [x] Default Posted filter = last 24 hours
- [x] Region/company dropdown counts follow current filters (status/search/date); 0-count company kept if selected; empty state says 0 shown of N loaded
- [x] `OBJECTIVE.md` + `PROGRESS.md` for chat handoff
- [x] Citi: Phenom `jobs.citi.com` (Workday CXS was 303 → maintenance HTML / empty JSON)
- [x] Per-region job files; All = merged list (India scan no longer wipes EU/Infopark)
- [x] EU boards (Jaabz / Relocate / Welcome NL): no fake java/visa text in description; Java/Spring must be in the real title
- [x] GitHub Pages + Action publish; Applied / Flagged / Hidden in Supabase
- [x] Gated email+password login (no magic link / no in-app reset); Dashboard-only users
- [x] Auth screen + mobile filter sheet + board UI polish
- [x] Trust the list: Reload vs Scan, published time, empty-filter hints, 0-job source warnings, mark confirmation, re-login on expired session
- [x] Title/company search; New-since-last-visit (localStorage URLs); persist region/date/status/search
- [x] Seniority match uses word boundaries (`architect` ≠ architecture)
- [x] GS / Morgan Stanley / EY / KPMG set `enabled: false` (dead HTML boards)
- [x] Search lives in the filters panel; Flag mark; phone icon buttons (sign out / scan / filters)
- [x] Sources info dialog (on vs off); scan progress is not dumped in the status line
- [x] Hosted Pages does not probe `/api/jobs` (that path is Flask-only; Pages uses `jobs.json`)
- [x] Region dropdown: India bucket labeled **BIG4 & Banks** (value still `india`)
- [x] UAE region (Jaabz + Relocate UAE-only; same sponsorship/Java/years gates as Europe)
- [x] Local `/api/jobs/save` carries over last-good jobs for failed sources (same as `run_scan`); unknown region is 400; region error lists are not mixed; Apply links allow http(s) only
- [x] Deloitte Interview Prep screen inside the gated app: Jobs/Interview nav, Java/Spring Boot/Angular/Kafka toggles, authored role-fit Q13-Q15 answers, and copy buttons
- [x] Sidebar redesign: desktop left side menu (nav / Scan / account), mobile bottom tab bar (Jobs / Interview / Filters / Menu) with Menu bottom sheet; old crowded topbar removed. `check_ui.py` statically checks HTML/JS/CSS wiring
- [x] Imported UI/UX skills into `.cursor/skills/`: `frontend-design` (Anthropic) + `ui-ux-pro-max` (SKILL.md + references)
- [x] MyGoTo catalog setup: installed Taste (`design-taste-frontend`), Web Interface Guidelines, Matt Pocock pack, `i-have-adhd`, Design Motion Principles into `.agents/skills` + mirrored into `.cursor/skills` (DeploySafe stays browser-only)
- [x] Collapsible sidebar (icon rail, `scout.sideCollapsed` in localStorage), auto-fill job grid columns (no more dead space between breakpoints, shell max 96rem), sheet Close buttons are X icons
- [x] **Remote** region (India-eligible): `remotive_remote` (Remotive+Jobicy geo gate) + Himalayas public API; no visa gate; cache `data/jobs-remote.json`
- [x] [`SOURCES.md`](SOURCES.md) — regions, filter matrix, and per-source on/off + fetch notes

## Known limitations
- PwC still uses Workday CXS; when Workday is in maintenance the source fails with a clear error (no public Phenom board)
- Citi list pages have no posted date — jobs show as date-unknown (toggle “include unknown”)
- GS / Morgan Stanley stay **disabled** (no public JSON search)
- KPMG Oracle titles are often generic (`Consultant`); adapter fetches each JD so Java/years filters can run
- Welcome NL (`welcome_nl`) is **disabled**: `welcometothenetherlands.com/vacatures/` redirects to Everaert internships; `welcome-to-nl.nl/jobs` currently shows 0 jobs
- Arbeitnow may rate-limit (429) after several pages — adapter keeps partial results
- Relocate.me `/search?query=` redirects to the unfiltered board; EU adapter searches `international-jobs?query=java`. UAE adapter uses `/united-arab-emirates` and keeps only that country slug (does not crawl the global intl board)
- Remotive.com JSON ignores search (always ~20 mixed jobs; HTML/RSS Cloudflare 403). Adapter also reads Jobicy’s Java remote JSON; `empty_ok` so a real empty set is not treated as a fetch error. EU uses `geo: eu`; Remote uses `geo: india_eligible`
- Remote India-eligible list can be thin after Java + years filters; US-only / Europe-only postings are dropped by design
- Jaabz works locally; GitHub Actions IPs get Cloudflare 403 — both `run_scan` and local progressive `/api/jobs/save` keep the last saved jobs of failed sources (`carry_over_failed_sources`) and append “kept N previously saved job(s)” to the error. Scan Europe/UAE locally + commit `data/jobs-eu.json` / `jobs-uae.json` to refresh hosted Jaabz
- UAE Java/Spring list will often be thin: many Dubai ads want 5–8+ years and are dropped by `max_years=4`
- Year/degree filters are best-effort when adapters only have titles (no full JD)
- Infopark detail pretty-URLs (`/jobs/...`) map to list URLs (`/company-jobs/details/...`)

## Next ideas (not started)
- [ ] Fetch Infopark/Workday/KPMG job detail for better year/degree/Java detection
- [ ] Source health line (jobs per source)
- [ ] GS JSON search if a public endpoint appears
- [ ] Filter sheet focus trap

## Key paths
- Config: `config.yaml`
- Scan/filter: `src/scan.py`, `src/filters.py`
- Sources: `src/sources/`
- UI: `web/index.html`, `web/app.js`, `web/style.css` (wiring check: `check_ui.py`)
- Profile reference: `Saffin profile.txt`
