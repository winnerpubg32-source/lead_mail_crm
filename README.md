# OutreachOS

**B2B Lead Outreach & CRM SaaS — Phase 1 foundation, Phase 2 lead database, Phase 3 CSV/XLSX import, Phase 4 data quality.**

OutreachOS imports large business datasets (names, contacts, e-mails, phone
numbers, websites, industries, cities, states), normalises and deduplicates
them, and will eventually qualify leads, generate personalised B2B outreach
e-mails, deliver them over SMTP with a hard limit of **90 marketing e-mails per
day**, and manage the resulting conversations in a CRM.

This repository contains **Phases 1–4**: the dashboard, the Leads / Companies /
Contacts database, CSV/XLSX upload with column mapping + chunked background
processing + import history, and data-quality tooling — normalization,
duplicate detection with confidence-weighted rules, a pairwise merge workflow,
merge-audit provenance, a missing-e-mail view, and a data-health dashboard.
Outreach, AI and CRM business logic are still deliberately absent.

---

## Table of contents

- [What is included in Phase 1](#what-is-included-in-phase-1)
- [What is included in Phase 2](#what-is-included-in-phase-2)
- [What is included in Phase 3](#what-is-included-in-phase-3)
- [Tech stack](#tech-stack)
- [Quick start (Docker Compose)](#quick-start-docker-compose)
- [Local development without Docker](#local-development-without-docker)
- [Project structure](#project-structure)
- [Environment variables](#environment-variables)
- [API reference](#api-reference)
- [Phase 2 — the lead database](#phase-2--lead-database-leads--companies--contacts)
- [Phase 3 — data import](#phase-3--data-import-imports)
- [Frontend architecture](#frontend-architecture)
- [Testing & quality gates](#testing--quality-gates)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)

---

## What is included in Phase 1

| Area | Status |
| --- | --- |
| Django project, settings split (base/development/production), PostgreSQL wiring | ✅ Done |
| Django REST Framework, CORS, environment-driven configuration | ✅ Done |
| Health endpoint `GET /api/health/` → `{"status": "ok"}` | ✅ Done |
| Basic authentication structure (custom e-mail user, token login/logout/me) | ✅ Done |
| Redis + Celery wiring (broker, result backend, worker entrypoints) | ✅ Done |
| 11 domain apps registered and routed (empty by design) | ✅ Done |
| React + Vite + TypeScript + Tailwind dashboard with 14 routes | ✅ Done |
| Polished dashboard: 8 KPI cards, capacity gauge, outreach feed, leads table, sources, campaigns, pipeline | ✅ Done |
| Dark/light mode, responsive layout, loading / empty / error states | ✅ Done |
| Docker Compose stack (frontend, backend, postgres, redis) | ✅ Done |
| CSV/XLSX import, SMTP sending, AI generation, CRM automation, lead scoring | ⛔ Phase 2+ |

Automated verification at the end of Phase 1:

```
backend   16 Django tests passing
frontend  18 Vitest tests passing · tsc --noEmit clean · eslint clean · vite build clean
```

---

## What is included in Phase 2

| Area | Status |
| --- | --- |
| `Company`, `Contact`, `Lead` models with the exact brief fields, incl. `normalized_name` / `normalized_website` / `normalized_email` / `source_file` / `source_row_number` | ✅ Done |
| Migrations written **and applied** (`companies`, `contacts`, `leads`) | ✅ Done |
| Lead status vocabulary (9 values) and e-mail status vocabulary (6 values) as DB enums | ✅ Done |
| `GET /api/{leads,companies,contacts}/` and `/{id}/` — pagination, search, filtering, ordering | ✅ Done |
| Leads vocabulary endpoint `GET /api/leads/statuses/` (per-status counts) | ✅ Done |
| Real Leads table — Business, Contact, Email, Phone, Industry, City, State, Lead Score, Status + search, filters, pagination | ✅ Done |
| Companies and Contacts pages reading real database rows | ✅ Done |
| Empty states when no records exist | ✅ Done |
| CSV/XLSX import, e-mail sending, AI, lead scoring | ⛔ Later phases |

Automated verification at the end of Phase 2:

```
backend   121 Django tests passing · ruff check + format clean · manage.py check clean
frontend  34 Vitest tests passing · tsc -b clean · eslint clean · vite build clean
```

---

## What is included in Phase 3

| Area | Status |
| --- | --- |
| **CSV + XLSX uploads** — content-based type detection (a renamed file is still rejected), 100 MB cap, per-sheet analysis of workbooks | ✅ Done |
| **Intelligent column mapping** — normalised exact match → alias/synonym table → fuzzy matching (no AI), with per-column confidence and manual overrides | ✅ Done |
| **Preview before import** — total rows, rows with/without e-mail, potential duplicates, invalid e-mails, first 50 rows, and the full SOURCE COLUMN → SYSTEM FIELD table | ✅ Done |
| **Background processing** — `ImportJob` + Celery (`imports.run_import_job`), CSV streamed in chunks of 500 rows, XLSX in batches; nothing is loaded fully into memory | ✅ Done |
| **Data quality** — e-mail + phone + website + company/name + address normalisation, e-mail syntax validation, invalid addresses dropped with a row warning, rows **without** an e-mail still stored, missing e-mails never invented | ✅ Done |
| **Idempotent merging** — companies matched on domain (`normalized_website`) then name, contacts on company + e-mail then name, leads on company + contact; re-importing the same file adds nothing and reports the rows as duplicates | ✅ Done |
| **Result screen** — “Import completed” with Total / Imported / Duplicates / Invalid / Missing Email (+ new companies, new contacts, errors) | ✅ Done |
| **Import history** — every run with its row counts, status filter and delete | ✅ Done |
| **`ImportJob` fields** — `id`, `filename`, `status`, `total_rows`, `processed_rows`, `valid_rows`, `invalid_rows`, `duplicate_rows`, `error_rows`, `started_at`, `completed_at` (+ provenance, analysis and issues) | ✅ Done |
| E-mail sending, AI, campaigns, scoring | ⛔ Later phases |

Automated verification at the end of Phase 3:

```
backend   205 Django tests passing · ruff check + format clean · manage.py check clean
frontend  51 Vitest tests passing · tsc -b clean · eslint clean · vite build clean
```

End-to-end proof against the running stack (`samples/sample_businesses.csv`,
14 messy real-world rows):

```
upload  → 14 rows detected, 5 columns mapped (exact/alias/fuzzy), 1 invalid e-mail flagged
start   → dispatched to Celery, job QUEUED → PROCESSING → COMPLETED in 0.09 s
result  → Total 14 · Imported 12 · Duplicates 1 · Invalid 1 · Missing email 1
re-run  → Total 14 · Imported 0 · Duplicates 13 · Invalid 1   (idempotent)
```

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, Vite 8, TypeScript 5.9, Tailwind CSS 4, React Router 7, TanStack Query 5, lucide-react |
| Backend | Python 3.12 (3.11+ works), Django 5.2, Django REST Framework 3.18, drf-spectacular |
| Database | PostgreSQL 16 |
| Background | Redis 7, Celery 5.6 |
| Infrastructure | Docker, Docker Compose |

---

## Quick start (Docker Compose)

**Requirements:** Docker Desktop / Docker Engine with the Compose plugin.

```bash
# 1. Clone and enter the repository
git clone <repository-url> lead_mail_crm && cd lead_mail_crm

# 2. Create your environment file
cp .env.example .env

# 3. Build and start everything (frontend, backend, postgres, redis)
docker compose up --build
```

| Service | URL |
| --- | --- |
| **Dashboard** | http://localhost:5173 |
| API health | http://localhost:8000/api/health/ |
| API root | http://localhost:8000/api/ |
| API docs (Swagger, debug only) | http://localhost:8000/api/docs/ |
| Django admin | http://localhost:8000/admin/ |

The backend container waits for PostgreSQL, applies migrations automatically and
then starts the development server, so the first `up` needs no extra steps.

**Optional extras**

```bash
# Celery worker + beat (no tasks exist yet — this only proves the broker wiring)
docker compose --profile workers up --build

# A Django admin login
docker compose exec backend python manage.py createsuperuser

# Start the stack without receiving data
docker compose down          # keep database volume
docker compose down -v       # wipe database volume
```

A `Makefile` wraps the same commands: `make up`, `make up-workers`, `make logs`,
`make migrate`, `make test`, `make health`, `make help`.

---

## Local development without Docker

Useful for day-to-day work with hot reload and native tooling.

### 1. Database and Redis

```bash
docker compose up -d postgres redis
```

### 2. Backend (Django)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements/dev.txt

# Point Django at the services started above
export DJANGO_SETTINGS_MODULE=config.settings.development
export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export POSTGRES_DB=outreachos POSTGRES_USER=outreachos POSTGRES_PASSWORD=outreachos
export REDIS_URL=redis://localhost:6379/0
export CELERY_BROKER_URL=redis://localhost:6379/1
export CELERY_RESULT_BACKEND=redis://localhost:6379/2

python manage.py migrate
python manage.py createsuperuser       # optional
python manage.py runserver 0.0.0.0:8000
```

### 3. Frontend (React)

```bash
cd frontend
npm install
cp .env.example .env.local   # optional — defaults already work
npm run dev                  # http://localhost:5173
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`
(`VITE_PROXY_TARGET`), so the browser only ever talks to one origin — no CORS
configuration needed in development.

### 4. Celery (optional in Phase 1)

```bash
cd backend
celery -A config worker -l info -Q outreachos
celery -A config beat -l info
```

---

## Project structure

```
lead_mail_crm/
├── backend/                          # Django + DRF + Celery
│   ├── config/                       # project configuration
│   │   ├── settings/
│   │   │   ├── base.py               # shared settings (env-driven)
│   │   │   ├── development.py        # DEBUG, permissive hosts/CORS
│   │   │   └── production.py         # hardening, WhiteNoise, gunicorn
│   │   ├── api_urls.py               # /api/ routing table
│   │   ├── urls.py                   # admin + /api/ + schema/docs
│   │   ├── handlers.py               # JSON error envelope for /api/*
│   │   ├── celery.py                 # Celery app + task autodiscovery
│   │   ├── asgi.py / wsgi.py
│   ├── core/                         # shared foundation (no domain logic)
│   │   ├── models.py                 # TimeStamped / Base / Owned abstract models
│   │   ├── normalization.py          # name / domain / e-mail / phone normalization
│   │   ├── pagination.py  permissions.py  exceptions.py  utils.py
│   │   ├── serializers.py
│   │   ├── views.py                  # API root, health, ready, version
│   │   ├── urls.py
│   │   └── tests/                    # health + auth tests
│   ├── apps/                         # one bounded context per module
│   │   ├── accounts/                 # ✅ user model + token auth (register/login/me/logout)
│   │   ├── companies/                # ✅ Company model + read-only API + filters
│   │   ├── contacts/                 # ✅ Contact model + read-only API + filters
│   │   ├── leads/                    # ✅ Lead model + API, vocabulary, seed command
│   │   ├── imports/                  # ✅ ImportJob + mapping/parsers/analysis/services + API
│   │   ├── campaigns/                # ⛔ registered, routed, empty
│   │   ├── email_engine/             # ⛔ registered, routed, empty
│   │   ├── ai_engine/                # ⛔ registered, routed, empty
│   │   ├── crm/                      # ⛔ registered, routed, empty
│   │   ├── analytics/                # ⛔ registered, routed, empty
│   │   └── suppression/              # ⛔ registered, routed, empty
│   ├── scripts/                      # container entrypoints (wait → migrate → exec)
│   ├── requirements/                 # base.txt · dev.txt · prod.txt
│   ├── Dockerfile                    # development + production targets
│   └── manage.py
│
├── frontend/                         # React + Vite + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                   # design system: Button, Card, Badge, Table, …
│   │   │   ├── layout/               # AppShell, Sidebar, Topbar, PageHeader, …
│   │   │   ├── charts/               # SVG Sparkline, CapacityGauge, SourceDonut, MiniBarChart
│   │   │   └── feedback/             # EmptyState, ErrorState, LoadingState, ErrorBoundary
│   │   ├── features/dashboard/       # dashboard-specific components
│   │   ├── features/leads/           # LeadTable (9 columns), table page skeleton
│   │   ├── features/imports/         # dropzone, file summary, mapping table, preview, progress, result
│   │   ├── pages/                    # Dashboard, Leads, Companies, Contacts, Imports, Import history, Settings, placeholders, 404
│   │   ├── routes/                   # AppRoutes (lazy-loaded), paths.ts
│   │   ├── services/                 # data access — dashboard mock ↔ API switch, real lead APIs
│   │   ├── hooks/                    # useLeads/useCompanies/useContacts/useImports, list query state, theme, …
│   │   ├── data/mock/                # dashboard placeholder dataset (UI only)
│   │   ├── config/                   # navigation, module registry, status maps, colours
│   │   ├── lib/                      # api client, env access, formatting, query client
│   │   └── types/                    # API + dashboard + lead/company/contact/import contracts
│   ├── nginx/default.conf            # production SPA + /api proxy
│   ├── Dockerfile                    # development + build + production targets
│   └── vite.config.ts · vitest.config.ts · eslint.config.js
│
├── samples/                          # sample_businesses.csv · .xlsx — messy fixtures used by the import tests
├── docker-compose.yml                # frontend · backend · postgres · redis (+ workers profile)
├── .env.example                      # every supported variable, documented
├── Makefile                          # developer shortcuts
└── README.md
```

---

## Environment variables

Copy `.env.example` to `.env`; every value has a working default for local use.

### Backend (Django)

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` | Settings module |
| `DJANGO_SECRET_KEY` | insecure dev key | **Change in production** |
| `DJANGO_DEBUG` | `true` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Host allow-list |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `localhost:5173` | CSRF origins |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | `outreachos` | Database credentials |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `localhost` / `5432` | Database location (`postgres` inside Compose) |
| `DATABASE_URL` | *(unset)* | Optional single-string alternative to the `POSTGRES_*` values |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache / general Redis |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery results |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Allowed browser origins |
| `CORS_ALLOW_ALL_ORIGINS` | `false` (`true` in development) | Development convenience |
| `OUTREACH_DAILY_EMAIL_LIMIT` | `90` | Daily marketing e-mail cap |
| `API_PAGE_SIZE` | `25` | DRF default page size |
| `EMAIL_BACKEND` | console backend | SMTP is a later phase |

### Frontend (Vite)

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api` | Relative API path (proxied by Vite/nginx) |
| `VITE_API_URL` | `http://localhost:8000/api` | API origin used when the mock switch is off |
| `VITE_USE_MOCK_DATA` | `true` | `true` → placeholder dataset, `false` → Django API |
| `VITE_PROXY_TARGET` | `http://127.0.0.1:8000` | Dev-server proxy target |
| `VITE_PORT` | `5173` | Dev-server port |

Only `VITE_*` variables are exposed to the browser.

---

## API reference

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/` | API root — discovery payload |
| `GET` | `/api/health/` | **Liveness probe → `{"status": "ok"}`** (also returns service/version/time) |
| `GET` | `/api/ready/` | Readiness probe — checks PostgreSQL, cache and Redis broker |
| `GET` | `/api/version/` | Build metadata, including the 90/day limit |
| `POST` | `/api/v1/accounts/register/` | Create a user, returns a token |
| `POST` | `/api/v1/accounts/login/` | Token login |
| `POST` | `/api/v1/accounts/logout/` | Invalidate the token (authenticated) |
| `GET` | `/api/v1/accounts/me/` | Current user (authenticated) |
| `GET` | `/api/v1/{imports,campaigns,email,ai,crm,analytics,suppression}/` | Module status stubs — return `{"status": "not_implemented", …}` so every planned route already resolves |
| `GET` | `/api/schema/`, `/api/docs/` | OpenAPI schema + Swagger UI (DEBUG only) |

### Phase 2 — lead database (leads / companies / contacts)

Read-only collections backed by PostgreSQL. Every route is exposed both under
the canonical versioned prefix and under the unversioned alias from the brief
(`/api/leads/` ≡ `/api/v1/leads/`, same viewsets, same payloads).

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/leads/` · `/api/v1/leads/` | Paginated lead list — `{count, next, previous, results}` |
| `GET` | `/api/leads/{id}/` | Single lead (company + contact context included) |
| `GET` | `/api/leads/statuses/` | Lead-status vocabulary with per-status counts |
| `GET` | `/api/companies/` | Company list, with `lead_count` / `contact_count` |
| `GET` | `/api/companies/{id}/` | Single company |
| `GET` | `/api/companies/status/` | Module status + totals |
| `GET` | `/api/contacts/` | Contact list, with company context |
| `GET` | `/api/contacts/{id}/` | Single contact |
| `GET` | `/api/contacts/status/` | Module status + totals |

Query parameters shared by all three lists: `page`, `page_size`, `search`,
`ordering`. Filters — leads: `lead_status` (repeatable or CSV), `email_status`,
`source`, `company`, `contact`, `industry`, `city`, `state`, `country`,
`min_score`, `max_score`, `has_email`, `is_contactable`, `created_after`,
`created_before`; companies: `industry`, `state`, `city`, `country`, `source`,
`domain`, `employee_count_min`, `employee_count_max`, `has_website`; contacts:
`company`, `job_title`, `phone_type`, `city`, `state`, `industry`, `source`,
`has_email`.

Lead statuses: `NEW`, `QUALIFIED`, `CONTACTED`, `REPLIED`, `MEETING`,
`PROPOSAL`, `WON`, `LOST`, `DO_NOT_CONTACT`. E-mail statuses: `UNKNOWN`,
`VALID`, `INVALID`, `BOUNCED`, `UNSUBSCRIBED`, `SUPPRESSED`.

Development data: `python manage.py seed_lead_data` (add `--flush` to reset,
`--flush --empty` to leave the tables empty and exercise the empty states).

### Phase 3 — data import (`/api/v1/imports/`, alias `/api/imports/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/imports/` | Import history — paginated; `status`, `file_type`, `with_errors`, `search`, `ordering` |
| `GET` | `/api/v1/imports/{id}/` | One job with its preview (counts, mapping, first 50 rows, issues) |
| `POST` | `/api/v1/imports/upload/` | Multipart upload (`file`, optional `sheet`) — analyses immediately, returns the detected mapping + preview |
| `GET` | `/api/v1/imports/fields/` | The 20 system fields with their aliases and hints (for the mapping UI) |
| `POST` | `/api/v1/imports/{id}/mapping/` | Apply manual mapping changes, returns the recomputed preview |
| `POST` | `/api/v1/imports/{id}/start/` | Confirm the mapping and queue the run (Celery); accepts a `column_mapping` override |
| `GET` | `/api/v1/imports/{id}/status/` | Small polling payload — status + progress + summary |
| `POST` | `/api/v1/imports/{id}/cancel/` | Discard a queued upload and its stored file (`204`, job deleted) |
| `DELETE` | `/api/v1/imports/{id}/` | Same as cancel, used by the history page |

Rows are written through the imports service layer (the leads/companies/contacts
viewsets stay read-only), always with provenance: `source="import:<file>"`,
`source_file` and `source_row_number`. Sample datasets used for the tests live in
`samples/`.

Errors always use one envelope:

```json
{ "error": { "code": "not_found", "message": "The requested resource was not found.", "details": {} } }
```

Authentication uses DRF token auth — send `Authorization: Token <key>`. The
custom user model (`accounts.User`) logs in with **e-mail**, not a username.

---

## Frontend architecture

### Placeholder data → Django API (single switch point)

The dashboard never imports mock data directly. The flow is:

```
page → hook (useDashboardOverview) → services/dashboard.service.ts  ─┐
                                                                    ├─ VITE_USE_MOCK_DATA=true  → data/mock/dashboard.mock.ts
                                                                    └─ VITE_USE_MOCK_DATA=false → GET /api/v1/analytics/dashboard/
```

To move to the live API, build the Django endpoint returning the
`DashboardOverview` shape from `src/types/dashboard.ts` and set
`VITE_USE_MOCK_DATA=false`. No component, hook or page changes are required.

The dashboard header shows a *"Placeholder data"* flag while the mock source is
active, and the settings page reports which data source is in use.

### Design system

- **Tokens** — semantic CSS variables (`--app-surface`, `--app-border`, …) mapped
  through Tailwind's `@theme inline`, so light and dark mode are one definition.
- **Dark/light mode** — system, light and dark; applied before first paint via an
  inline script, stored in `localStorage`, shared through a small external store.
- **Components** — `Button`, `Card`, `Badge`, `Table`, `Input`, `Select`, `Switch`,
  `Progress`, `SegmentedControl`, `Skeleton`, `Avatar`, plus charts built with
  plain SVG (no charting dependency in the initial bundle).
- **States** — every data surface implements loading (skeletons), empty
  (`EmptyState`), error with retry (`ErrorState`) and a per-panel `ErrorBoundary`.
- **Responsive** — collapsible desktop rail, off-canvas mobile drawer, fluid KPI
  grid (1 → 2 → 4 columns), horizontally scrollable tables.

### Routes

`/dashboard` · `/leads` · `/companies` · `/contacts` · `/imports` ·
`/imports/history` · `/campaigns` · `/email` · `/follow-ups` · `/crm` ·
`/analytics` · `/templates` · `/ai` · `/suppression` · `/settings`

`/dashboard` is functional, `/settings` is a small but real surface (theme, UI
preferences, API connectivity diagnostics), and `/leads`, `/companies` and
`/contacts` are **backed by the live PostgreSQL database** (Phase 2): search,
filters, sortable headers, pagination, loading / empty / error states. Every
remaining module renders a professional placeholder describing its planned scope,
data columns and API path — the navigation, routing and layout are final, only the
business logic is pending.

---

## Testing & quality gates

```bash
# Backend — Django test suite (needs PostgreSQL; uses a test database)
cd backend && python manage.py test

# Frontend — unit/integration tests (Vitest + Testing Library + jsdom)
cd frontend && npm test

# Frontend — static analysis
cd frontend && npm run typecheck     # TypeScript, strict mode
cd frontend && npm run lint          # ESLint (React 19 rules)

# Frontend — production build
cd frontend && npm run build
```

Current state: **205 Django tests**, **51 frontend tests**, typecheck, lint and
build all pass.

Backend tests cover health/readiness, auth, the normalization helpers, model
constraints, the seed command, every list/detail/filter/ordering behaviour of the
leads, companies and contacts APIs, and the whole import pipeline: header
normalisation and file-type detection, the mapping engine (exact/alias/fuzzy,
row-identifier guard), row building and normalisation, preview analysis with
batched duplicate lookups, the chunked runner (progress, merging, idempotency,
per-row fallback), the Celery wiring and the full HTTP round-trip including the
guard rails.

Frontend tests cover the dashboard (KPI cards, `0 / 90` capacity, all five
required sections, empty states, error + retry), every route in the sidebar, the
three database-backed pages (columns, rows, search, filters, pagination,
empty/error states) and the import screens (drag & drop, file metadata, sheets,
preview numbers, mapping edits, progress polling, the completed screen, cancel
and the history page).

---

## Roadmap

Later phases, in the order the codebase is prepared for them:

1. **Qualification** — lead scoring and AI-assisted qualification (`ai_engine`).
3. **Campaigns & sending** — sequences, SMTP mailboxes, the enforced
   **90 e-mails/day** budget, bounce handling (`campaigns`, `email_engine`,
   `suppression`).
4. **CRM** — deals, notes, tasks, activity timeline (`crm`).
5. **Analytics** — aggregation tables feeding the dashboard cards (`analytics`),
   with the dashboard switching to the live API via `VITE_USE_MOCK_DATA=false`.

Deliberately **not** implemented yet: SMTP sending, AI generation, campaign
execution, lead scoring and CRM automation. `lead_score` exists as a stored
integer on `Lead` (0–100, settable via API/seed) — there is no scoring algorithm
behind it.

---

## Troubleshooting

**`docker compose up` fails on the backend with a database error**
The backend waits for PostgreSQL's healthcheck before migrating. If it still
fails, check credentials match between `.env` and the `postgres` service, then
`docker compose down -v && docker compose up --build` to reset volumes.

**Port already in use (5432 / 6379 / 8000 / 5173)**
Change the host-side mappings in `.env` (`POSTGRES_HOST_PORT`,
`REDIS_HOST_PORT`, `BACKEND_HOST_PORT`, `FRONTEND_HOST_PORT`).

**Frontend shows "API offline" / the Leads, Companies or Contacts pages error**
Expected when only the frontend is running: the dashboard still renders the
mock dataset, but `/leads`, `/companies` and `/contacts` always read the real
API. Start the backend (`docker compose up backend` or `python manage.py
runserver`) or point `VITE_PROXY_TARGET` at a running Django instance. If the
database is empty, seed it with `python manage.py seed_lead_data`.

**Blank page after deploying the production frontend image**
The SPA needs history fallback — `nginx/default.conf` already contains
`try_files $uri /index.html`. Also set `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS` to your real domain, and switch
`VITE_USE_MOCK_DATA=false` only once the analytics endpoint exists.

**`npm run build` complains about TypeScript version / peer dependencies**
Use Node 20.19+ (or 22+) as pinned in `frontend/package.json` and install with
`npm install` — the lockfile pins the versions this phase was verified against.
