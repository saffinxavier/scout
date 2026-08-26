# Scout — Objective

## Goal
Help **Saffin Xavier** (Kochi, India; Indian national; **3.5+ years**; **B.Tech only**; notice 3 months) find and apply to **Java / Spring** backend roles without manually checking every career site.

## Target roles
- Senior / mid backend software engineer (Java, Spring Boot, microservices)
- Willing to relocate; Europe and UAE need **visa/sponsorship**; India Big 4 + banks OK; Infopark Kochi local board

## Product (this repo)
Local Flask app + scrapers that aggregate jobs onto **one dark job-board page**.

### Regions / sources
Detail (tables, on/off, fetch notes): [`SOURCES.md`](SOURCES.md).
- **India:** JPMorgan, Citi (`jobs.citi.com`), PwC (Workday), Deloitte (South Asia RSS), EY (careers.ey.com RSS + India gate), KPMG (Oracle CX_3001 + CX_3). GS/MS still off (no JSON search)
- **Europe:** Relocate.me (`international-jobs?query=java`), Jaabz, Arbeitnow, Remotive (Remotive.com JSON is a teaser; adapter also reads Jobicy Java remote JSON). Welcome NL is **disabled**
- **UAE:** Relocate.me country board (`/united-arab-emirates`, UAE paths only) + Jaabz UAE visa-sponsorship search. Same Java/years/education/seniority/sponsorship gates as Europe
- **Infopark:** `infopark.in/companies-job` (all pages); skips Java/seniority gates so local board is browsable
- **Remote:** India-eligible fully remote Java/Spring — Remotive+Jobicy (`geo: india_eligible`) + Himalayas public API. Keeps India / APAC / Asia / Worldwide; drops US-only / Europe-only. Same Java/years/education/seniority gates as India (**no** visa/sponsorship gate)

### Filters (profile fit)
- Keywords: java, spring boot, spring, springboot (OR)
- Drop intern/campus/etc.
- Drop if stated min experience **> 4** years
- Drop Masters/MBA/M.Tech **requirements**
- India/EU/UAE/Remote seniority excludes: AVP, VP, principal, staff, architect, director (Lead titles allowed; **word-boundary** match so “architecture” is not dropped)
- Infopark: no Java/Spring or seniority gate
- Europe/UAE: sponsorship/visa gate; India/Infopark/Remote: **no** sponsorship gate
- **GS / Morgan Stanley** HTML sources stay **disabled** until a JSON search exists

### UX
- Dark-only job cards; Scan streams **one source at a time** for the **selected region** (not all sources if region filtered)
- Default **Posted = last 24 hours** (region/date/status/search remembered in the browser)
- Filters: region (with counts; India bucket labeled **BIG4 & Banks**), company (with counts). Counts match the current status/date/search (Open hides applied/hidden). Date range, **title/company search** (in the filter row/sheet), **New since last visit** (URLs seen this browser)
- Apply / **Flag** (look later) / Hide per job
- Layout: desktop has a left **sidebar** (brand, Jobs/Interview nav, Scan, Info at status row, email + sign out at bottom) that **collapses to an icon rail** (chevron toggle, remembered in the browser); phones get a **bottom tab bar** (Jobs / Interview / Filters / Menu) — Menu opens a sheet with Scan, email, sign out. Job grid uses auto-fill columns (min 17rem) so it fills the available width
- Login-gated **Interview** view for Deloitte Preliminary Screening prep, with Java / Spring Boot / Angular / Kafka toggles that tailor role-fit answers
- **Info** (i) lists sources that are on vs off (Welcome NL, GS, …) and last scan issues
- Job cache is **per region** (`data/jobs-india.json`, `jobs-eu.json`, `jobs-uae.json`, `jobs-infopark.json`, `jobs-remote.json`). Scan one region without wiping the others. **All** shows the merged list.
- Hosted board: GitHub Pages + Action scan (no Scan in the browser). Gated email+password login (Supabase). Applied / Flagged / Hidden per user. Passwords created/reset in the Dashboard only.

## How to run
```bash
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.app
```
Open http://127.0.0.1:5000 — hard-refresh after UI changes; restart process after Python adapter changes if needed (scan reloads registry each call).

## How to continue in a new chat
Ask the agent to read `OBJECTIVE.md` and `PROGRESS.md` (rule: `.cursor/rules/handoff-docs.mdc`).
