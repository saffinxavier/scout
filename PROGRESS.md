# Scout — Progress

Last updated: 2026-08-22

## Done
- [x] Local Flask app + `config.yaml` sources + dark job-board UI
- [x] Filters: keywords, max_years=4, education, seniority (config-driven), EU sponsorship rules
- [x] Infopark adapter with **full pagination** (fixed missing Empay Java on page 3+)
- [x] Pagination audit/fixes: JPM offset loop, Workday max_results 500, Jaabz pages, Arbeitnow pages, Relocate intl pages
- [x] Deloitte switched to **southasiacareers.deloitte.com** RSS (India/South Asia), not US apply.deloitte.com
- [x] Progressive scan: `/api/sources` + `/api/scan/one` — loads sources **one-by-one** for selected region only
- [x] Default Posted filter = last 24 hours
- [x] Region/company dropdown counts; scan button spinner
- [x] `OBJECTIVE.md` + `PROGRESS.md` for chat handoff

## Known limitations
- GS / Morgan Stanley / EY / KPMG HTML scrapers remain fragile (JS career sites)
- Arbeitnow may rate-limit (429) after several pages — adapter keeps partial results
- Relocate.me search `?page=` is a no-op; intl board pages are used instead
- Year/degree filters are best-effort when adapters only have titles (no full JD)
- Infopark detail pretty-URLs (`/jobs/...`) map to list URLs (`/company-jobs/details/...`)

## Next ideas (not started)
- [ ] Fetch Infopark/Workday job detail for better year/degree detection
- [ ] EY/KPMG/GS dedicated APIs if public endpoints found
- [ ] GitHub Pages + Actions mirror
- [ ] Optional “Applied” status tracking

## Key paths
- Config: `config.yaml`
- Scan/filter: `src/scan.py`, `src/filters.py`
- Sources: `src/sources/`
- UI: `web/index.html`, `web/app.js`, `web/style.css`
- Profile reference: `Saffin profile.txt`
