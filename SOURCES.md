# Scout — Regions & sources

Scout aggregates **Java / Spring** jobs into one board. Enable flags and URLs live in [`config.yaml`](config.yaml); fetch logic lives in [`src/sources/`](src/sources/). Each region has its own cache: `data/jobs-{region}.json`. **All** in the UI merges those files.

## Filter cheat-sheet

| Gate | India | Europe | UAE | Infopark | Remote |
|------|:-----:|:------:|:---:|:--------:|:------:|
| Java / Spring keywords | yes | yes | yes | **no** | yes |
| Max experience **> 4** years | yes | yes | yes | yes | yes |
| Masters / MBA / M.Tech **requirements** | yes | yes | yes | yes | yes |
| Drop intern / campus / … | yes | yes | yes | yes | yes |
| Seniority (AVP, VP, principal, staff, architect, director) | yes | yes | yes | **no** | yes |
| Visa / sponsorship | **no** | **yes** | **yes** | **no** | **no** |

Europe / UAE keep a job if it is from a `sponsorship_board: true` source **or** the text matches sponsorship keywords (visa, sponsorship, work permit, …).

**Remote geo (adapter-level):** keep India / APAC / Asia / Worldwide / Anywhere / unrestricted; drop US-only or Europe-only listings.

---

## India (`india`) — UI: **BIG4 & Banks**

Cache: `data/jobs-india.json`

| id | On? | Fetch | Notes |
|----|-----|-------|--------|
| `jpmorgan` | yes | Oracle HCM JSON | Keyword Java |
| `citi` | yes | Phenom (`jobs.citi.com`) | Workday CXS was 303 → maintenance; no posted dates on list pages |
| `pwc` | yes | Workday CXS | India location substrings (+ remote); fails clearly when Workday is in maintenance |
| `deloitte` | yes | Jobs2Web RSS | South Asia board only; rejects US `apply.deloitte.com` URLs |
| `ey` | yes | Jobs2Web RSS | India location gate |
| `kpmg` | yes | Oracle CX_3001 + CX_3 | Titles often generic; adapter fetches each JD for filters |
| `goldman_sachs` | **no** | HTML | No public JSON search |
| `morgan_stanley` | **no** | HTML | No public JSON search |

---

## Europe (`eu`) — UI: **Europe**

Cache: `data/jobs-eu.json` · sponsorship / relocation focus

| id | On? | Fetch | Notes |
|----|-----|-------|--------|
| `relocate_me` | yes | HTML board | `international-jobs?query=java`; sponsorship board |
| `jaabz` | yes | HTML | `q=java+spring&visa=1`; Cloudflare 403 common on GitHub Actions IPs |
| `arbeitnow` | yes | Public API | Not a sponsorship board — visa **keywords** still required |
| `remotive` | yes | Remotive JSON + Jobicy JSON | `geo: eu`; Remotive teaser ~20 jobs; Java in title; EU/worldwide geo |
| `welcome_nl` | **no** | HTML | Board empty / redirected; left disabled |

---

## UAE (`uae`) — UI: **UAE**

Cache: `data/jobs-uae.json` · same filters as Europe (incl. sponsorship)

| id | On? | Fetch | Notes |
|----|-----|-------|--------|
| `relocate_me_uae` | yes | HTML (same module as EU) | `/united-arab-emirates` only; does not crawl the global intl board |
| `jaabz_uae` | yes | HTML (same module as EU) | UAE visa-sponsorship search; same Actions Cloudflare risk as EU Jaabz |

Many Dubai ads ask for 5–8+ years and are dropped by `max_years: 4`.

---

## Infopark (`infopark`) — UI: **Infopark**

Cache: `data/jobs-infopark.json` · local Kochi board

| id | On? | Fetch | Notes |
|----|-----|-------|--------|
| `infopark` | yes | HTML pagination | `infopark.in/companies-job`; **no** Java/Spring or seniority gate so the board stays browsable |

---

## Remote (`remote`) — UI: **Remote**

Cache: `data/jobs-remote.json` · fully remote, **India-eligible** geos, no visa gate

| id | On? | Fetch | Notes |
|----|-----|-------|--------|
| `remotive_remote` | yes | Same Remotive + Jobicy as `remotive` | `geo: india_eligible` (not EU) |
| `himalayas` | yes | Himalayas public JSON API | Search `java` / `spring boot` + India country pass; keeps India/APAC/worldwide `locationRestrictions` |

`remotive` (Europe) and `remotive_remote` (Remote) share [`src/sources/remotive.py`](src/sources/remotive.py); only `region` + `geo` differ.

---

## How to change sources

1. Edit enable flags, URLs, and options in [`config.yaml`](config.yaml).
2. Adapter code: [`src/sources/<name>.py`](src/sources/).
3. New source id → register in [`src/sources/__init__.py`](src/sources/__init__.py) `REGISTRY`.
4. New region → add to `REGIONS` in [`src/scan.py`](src/scan.py) and the UI labels in [`web/app.js`](web/app.js).
5. Scan (local **Scan now** or `run_scan`) writes `data/jobs-{region}.json`.

Product goals and UX: [`OBJECTIVE.md`](OBJECTIVE.md). Quick start: [`README.md`](README.md).
