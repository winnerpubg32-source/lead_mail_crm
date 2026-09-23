# OutreachOS

**B2B Lead Outreach & CRM SaaS — Phase 1 foundation.**

OutreachOS will eventually import large business datasets (names, contacts, e-mails,
phone numbers, websites, industries, cities, states), qualify leads, generate
personalised B2B outreach e-mails, deliver them over SMTP with a hard limit of
**90 marketing e-mails per day**, and manage the resulting conversations in a CRM.

This repository currently contains **Phase 1: the project foundation and a
professional dashboard frontend**. No outreach, import, AI or CRM business logic
is implemented yet — on purpose.

---

## Table of contents

- [What is included in Phase 1](#what-is-included-in-phase-1)
- [Tech stack](#tech-stack)
- [Quick start (Docker Compose)](#quick-start-docker-compose)
- [Local development without Docker](#local-development-without-docker)
- [Project structure](#project-structure)
- [Environment variables](#environment-variables)
- [API reference (Phase 1)](#api-reference-phase-1)
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

Automated verification at the end of this phase:

```
backend   16 Django tests passing
frontend  18 Vitest tests passing · tsc --noEmit clean · eslint clean · vite build clean
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
│   │   ├── pagination.py  permissions.py  exceptions.py  utils.py
│   │   ├── serializers.py
│   │   ├── views.py                  # API root, health, ready, version
│   │   ├── urls.py
│   │   └── tests/                    # health + auth tests
│   ├── apps/                         # one bounded context per module
│   │   ├── accounts/                 # ✅ user model + token auth (register/login/me/logout)
│   │   ├── companies/                # ⛔ registered, routed, empty
│   │   ├── contacts/                 # ⛔ registered, routed, empty
│   │   ├── leads/                    # ⛔ registered, routed, empty
│   │   ├── imports/                  # ⛔ registered, routed, empty
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
│   │   ├── pages/                    # DashboardPage, SettingsPage, ModulePlaceholderPage, 404
│   │   ├── routes/                   # AppRoutes (lazy-loaded), paths.ts
│   │   ├── services/                 # data access — the mock ↔ API switch point
│   │   ├── hooks/                    # useDashboardOverview, useTheme, useMediaQuery, …
│   │   ├── data/mock/                # Phase 1 placeholder dataset (UI only)
│   │   ├── config/                   # navigation, module registry, status maps, colours
│   │   ├── lib/                      # api client, env access, formatting, query client
│   │   └── types/                    # API + dashboard contracts
│   ├── nginx/default.conf            # production SPA + /api proxy
│   ├── Dockerfile                    # development + build + production targets
│   └── vite.config.ts · vitest.config.ts · eslint.config.js
│
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

## API reference (Phase 1)

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
| `GET` | `/api/v1/{companies,contacts,leads,imports,campaigns,email,ai,crm,analytics,suppression}/` | Module status stubs — return `{"status": "not_implemented", …}` so every planned route already resolves |
| `GET` | `/api/schema/`, `/api/docs/` | OpenAPI schema + Swagger UI (DEBUG only) |

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

`/dashboard` · `/leads` · `/companies` · `/contacts` · `/imports` · `/campaigns` ·
`/email` · `/follow-ups` · `/crm` · `/analytics` · `/templates` · `/ai` ·
`/suppression` · `/settings`

Only `/dashboard` is functional; `/settings` is a small but real surface (theme,
UI preferences, API connectivity diagnostics). Every other module renders a
professional placeholder describing its planned scope, data columns and API path —
the navigation, routing and layout are final, only the business logic is pending.

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

Current state: **16 Django tests**, **18 frontend tests**, typecheck, lint and
build all pass.

Frontend tests cover the dashboard (KPI cards, `0 / 90` capacity, all five
required sections, empty states, error + retry) and every route in the sidebar.

---

## Roadmap

Later phases, in the order the codebase is prepared for them:

1. **Data ingestion** — `companies`, `contacts`, `leads`, `imports`: CSV/XLSX
   upload, column mapping, chunked Celery processing, deduplication.
2. **Qualification** — lead scoring and AI-assisted qualification (`ai_engine`).
3. **Campaigns & sending** — sequences, SMTP mailboxes, the enforced
   **90 e-mails/day** budget, bounce handling (`campaigns`, `email_engine`,
   `suppression`).
4. **CRM** — deals, notes, tasks, activity timeline (`crm`).
5. **Analytics** — aggregation tables feeding the dashboard cards (`analytics`),
   with the dashboard switching to the live API via `VITE_USE_MOCK_DATA=false`.

Deliberately **not** implemented in Phase 1: CSV/XLSX import, SMTP sending, AI
generation, campaign execution, lead scoring and CRM automation.

---

## Troubleshooting

**`docker compose up` fails on the backend with a database error**
The backend waits for PostgreSQL's healthcheck before migrating. If it still
fails, check credentials match between `.env` and the `postgres` service, then
`docker compose down -v && docker compose up --build` to reset volumes.

**Port already in use (5432 / 6379 / 8000 / 5173)**
Change the host-side mappings in `.env` (`POSTGRES_HOST_PORT`,
`REDIS_HOST_PORT`, `BACKEND_HOST_PORT`, `FRONTEND_HOST_PORT`).

**Frontend shows "API offline"**
Expected when only the frontend is running: the dashboard still renders the
placeholder dataset. Start the backend (`docker compose up backend`) or point
`VITE_PROXY_TARGET` at a running Django instance.

**Blank page after deploying the production frontend image**
The SPA needs history fallback — `nginx/default.conf` already contains
`try_files $uri /index.html`. Also set `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS` to your real domain, and switch
`VITE_USE_MOCK_DATA=false` only once the analytics endpoint exists.

**`npm run build` complains about TypeScript version / peer dependencies**
Use Node 20.19+ (or 22+) as pinned in `frontend/package.json` and install with
`npm install` — the lockfile pins the versions this phase was verified against.
