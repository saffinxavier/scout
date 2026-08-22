# Scout

Local job listing aggregator for **Java / Spring Boot** roles that fit a **~3.5y B.Tech** profile:

- **India:** Deloitte, PwC, EY, KPMG, JPMorgan Chase, Goldman Sachs, Morgan Stanley, Citi
- **Europe:** sponsorship / relocation boards (Relocate.me, Welcome to the Netherlands, Jaabz) plus EU/remote boards filtered for visa/sponsorship signals
- **Infopark:** [infopark.in/companies-job](https://infopark.in/companies-job)

- Scan now. Company / region / date filters. Apply links. No accounts, no auto-apply.
- Cache is one JSON file per region; **All** merges them.

## Quick start

```bash
cd scout
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.app
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) → set region if you want → **Scan now** (loads that region’s sources one-by-one).

New chat handoff: read [`OBJECTIVE.md`](OBJECTIVE.md) and [`PROGRESS.md`](PROGRESS.md).

Optional CLI scan (writes `data/jobs-{region}.json`; `run_scan()` writes all three):

```bash
.\.venv\Scripts\python.exe -c "from src.scan import run_scan; print(run_scan()['count'])"
```

Filter self-check:

```bash
.\.venv\Scripts\python.exe -m src.check_filters
```

## Filters

| Rule | Behavior |
|------|----------|
| Keywords | Title/description matches **Java** or **Spring Boot** |
| Level | Drops Intern / Graduate / Campus / Trainee / Apprentice |
| Experience | Drops postings whose stated minimum is **> 4 years** (`5+`, `8+`); keeps `3-5` and unknown |
| Education | Drops Masters / MBA / M.Tech **requirements** |
| Europe sponsorship | Kept if source is a sponsorship board **or** text matches visa/sponsorship keywords |
| India / Infopark | No sponsorship gate |
| UI filters | Region (incl. Infopark), **company**, date range on the current scan |

Edit sources and keywords in [`config.yaml`](config.yaml).

## Notes

- Some India career sites (Big 4, GS, MS) are JS-heavy; their HTML adapters may return few or zero rows until search URLs in `config.yaml` are updated. JPM (Oracle HCM), Citi, and PwC (Workday) use public JSON APIs and are usually more reliable.
- Infopark is a local Kochi board: it skips the Java/Spring and Lead/Architect gates so you can browse what is posted. India & Europe stay Java/Spring-only with seniority filters.
- Scrapers are for **personal** use; sites change often. Failed sources show in the warning banner without blocking others.
- Pagination: Infopark, Jaabz, Relocate (intl board), Arbeitnow, JPM, and Workday (Citi/PwC) walk multiple pages. Remotive returns its full search set. HTML career scrapers (GS/MS/Big 4 landing pages) stay single-page / best-effort.
- SSL verify is off by default in config for flaky career CDNs on Windows — local-only tool.

## Hosted URL (phone + other laptops)

Jobs are a static site on GitHub Pages. Scan runs on GitHub (Actions), not in the phone browser. Applied/Hidden is stored in your Supabase project after you sign in with email.

One-time setup:

1. Supabase → **SQL Editor** → paste and run [`supabase/schema.sql`](supabase/schema.sql).
2. Supabase → **Authentication** → **URL configuration** → add Redirect URLs:
   - `http://127.0.0.1:5000/`
   - `https://saffinxavier.github.io/scout/`
3. GitHub repo → **Settings** → **Pages** → **Source** = **GitHub Actions**.
4. Push this repo, then **Actions** → **Scan and publish** → **Run workflow**.

Site URL after the first successful deploy: [https://saffinxavier.github.io/scout/](https://saffinxavier.github.io/scout/)

Local Flask still works for **Scan now**. Sign in there too so marks match the hosted site.

