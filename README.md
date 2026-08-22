# Scout

Local job listing aggregator for **Java / Spring Boot** roles that fit a **~3.5y B.Tech** profile:

- **India:** Deloitte, PwC, EY, KPMG, JPMorgan Chase, Goldman Sachs, Morgan Stanley, Citi
- **Europe:** sponsorship / relocation boards (Relocate.me, Welcome to the Netherlands, Jaabz) plus EU/remote boards filtered for visa/sponsorship signals
- **Infopark:** [infopark.in/companies-job](https://infopark.in/companies-job)

- Scan now. Company / region / date filters. Apply links. No auto-apply.
- Cache is one JSON file per region; **All** merges them.
- Sign in with **email + password** (accounts created in the Supabase Dashboard).

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

Jobs are a static site on GitHub Pages. Scan runs on GitHub (Actions), not in the phone browser. Applied/Hidden is stored in Supabase after you **sign in with email + password**. There is no Sign up or Forgot-password on the site.

### Accounts (Supabase Dashboard only)

1. **Authentication → Users → Add user** — set email and password (at least 8 characters).
2. To change a forgotten password: open that user in the Dashboard and set a new password (or send recovery from there).
3. **Authentication → Providers → Email** — **disable sign-ups** so strangers cannot register. Optional: turn off magic-link / OTP so only password login works.
4. If you already signed in with an email link once: set a password on that same user in the Dashboard, then use email + password on the site. Applied marks stay on that user.

### Publish setup

1. Supabase → **SQL Editor** → paste and run [`supabase/schema.sql`](supabase/schema.sql).
2. GitHub repo → **Settings** → **Pages** → **Source** = **GitHub Actions**.
3. Push to **main** — **Scan and publish** runs automatically. You can still **Actions** → **Run workflow** anytime.

Site URL: [https://saffinxavier.github.io/scout/](https://saffinxavier.github.io/scout/)

Local Flask still works for **Scan now** at http://127.0.0.1:5000 — sign in with the same email and password.

