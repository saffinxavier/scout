# Scout — Objective

## Goal
Help **Saffin Xavier** (Kochi, India; Indian national; **3.5+ years**; **B.Tech only**; notice 3 months) find and apply to **Java / Spring** backend roles without manually checking every career site.

## Target roles
- Senior / mid backend software engineer (Java, Spring Boot, microservices)
- Willing to relocate; Europe needs **visa/sponsorship**; India Big 4 + banks OK; Infopark Kochi local board

## Product (this repo)
Local Flask app + scrapers that aggregate jobs onto **one dark job-board page**.

### Regions / sources
- **India:** JPMorgan, Citi, PwC (Workday), Deloitte (**South Asia** careers / RSS — not US `apply.deloitte.com`), GS/MS/EY/KPMG best-effort HTML
- **Europe:** Relocate.me, Jaabz, Welcome NL, Arbeitnow, Remotive (sponsorship board or keyword)
- **Infopark:** `infopark.in/companies-job` (all pages); skips Java/seniority gates so local board is browsable

### Filters (profile fit)
- Keywords: java, spring boot, spring, springboot (OR)
- Drop intern/campus/etc.
- Drop if stated min experience **> 4** years
- Drop Masters/MBA/M.Tech **requirements**
- India/EU seniority excludes: AVP, VP, principal, staff, architect, director (Lead titles allowed)
- Infopark: no Java/Spring or seniority gate

### UX
- Dark-only job cards; Scan streams **one source at a time** for the **selected region** (not all sources if region filtered)
- Default **Posted = last 24 hours**
- Filters: region (with counts), company (with counts), date range
- Apply link per job

## How to run
```bash
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.app
```
Open http://127.0.0.1:5000 — hard-refresh after UI changes; restart process after Python adapter changes if needed (scan reloads registry each call).

## How to continue in a new chat
Ask the agent to read `OBJECTIVE.md` and `PROGRESS.md` (rule: `.cursor/rules/handoff-docs.mdc`).
