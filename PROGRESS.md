# Scout — Progress

Last updated: 2026-08-22

## Done
- [x] Local Flask app + `config.yaml` sources + dark job-board UI
- [x] Filters: keywords, max_years=4, education, seniority (config-driven), EU sponsorship rules
- [x] Infopark adapter with **full pagination** (fixed missing Empay Java on page 3+)
- [x] Pagination audit/fixes: JPM offset loop, Workday max_results 500, Jaabz pages, Arbeitnow pages, Relocate intl pages
- [x] Deloitte: South Asia only (`southasiacareers.deloitte.com` + India location gate); rejects `apply.deloitte.com` US URLs; adapter modules fully reloaded each scan
- [x] Progressive scan: `/api/sources` + `/api/scan/one` — loads sources **one-by-one** for selected region only
- [x] Default Posted filter = last 24 hours
- [x] Region/company dropdown counts; scan button spinner
- [x] `OBJECTIVE.md` + `PROGRESS.md` for chat handoff
- [x] Citi: Phenom `jobs.citi.com` (Workday CXS was 303 → maintenance HTML / empty JSON)
- [x] Per-region job files; All = merged list (India scan no longer wipes EU/Infopark)
- [x] EU boards (Jaabz / Relocate / Welcome NL): no fake java/visa text in description; Java/Spring must be in the real title
- [x] GitHub Pages + Action publish; Applied/Hidden in Supabase (email magic link)

## Known limitations
- PwC still uses Workday CXS; when Workday is in maintenance the source fails with a clear error (no public Phenom board)
- Citi list pages have no posted date — jobs show as date-unknown (toggle “include unknown”)
- GS / Morgan Stanley / EY / KPMG HTML scrapers remain fragile (JS career sites)
- Arbeitnow may rate-limit (429) after several pages — adapter keeps partial results
- Relocate.me search `?page=` is a no-op; intl board pages are used instead
- Year/degree filters are best-effort when adapters only have titles (no full JD)
- Infopark detail pretty-URLs (`/jobs/...`) map to list URLs (`/company-jobs/details/...`)

## Next ideas (not started)
- [ ] Fetch Infopark/Workday job detail for better year/degree detection
- [ ] EY/KPMG/GS dedicated APIs if public endpoints found
- [ ] Warn when HTML adapters return 0 jobs with no error

## Key paths
- Config: `config.yaml`
- Scan/filter: `src/scan.py`, `src/filters.py`
- Sources: `src/sources/`
- UI: `web/index.html`, `web/app.js`, `web/style.css`
- Profile reference: `Saffin profile.txt`
