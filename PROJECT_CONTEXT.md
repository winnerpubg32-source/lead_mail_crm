# OutreachOS — Project Context

OutreachOS is a B2B lead outreach & CRM SaaS built with Django + DRF on the backend
and React + TypeScript + Vite + Tailwind on the frontend. PostgreSQL is the
primary database, Redis/Celery handle background imports.

## Phase Status

| Phase | Status |
| --- | --- |
| Phase 1 — Project foundation + dashboard | ✅ Completed |
| Phase 2 — Lead / Company / Contact database + APIs | ✅ Completed |
| Phase 3 — CSV/XLSX import (column detection, preview, chunked processing, history) | ✅ Completed |
| Phase 4 — Data normalization · deduplication · merge · missing-email · data-quality dashboard | ✅ Completed |
| Phase 5+ (lead scoring, campaigns, SMTP, AI personalization, service matching, follow-ups, CRM, analytics) | ⛔ Not implemented |

---

## Phase 4 Implementation

Phase 4 adds robust normalization, database-side duplicate detection with
confidence-weighted matching rules, a pairwise review workflow, transactional
merge with full provenance preservation, a Missing-E-mail leads view, and a
data-quality statistics dashboard. All work builds directly on the Phase 3
import pipeline and Phase 2 models; Phase 1–3 code is unchanged except for
small compatibility additions (a new `MERGED` lead status, a `normalized_address`
column on Company, a `normalized_name` key on Contact, and new indexes).

### New / updated models

| Model | App | Change |
| --- | --- | --- |
| `Company` | `companies` | Added `normalized_address` (max 500, indexed); added composite indexes `company_name_city_state_idx` and `company_norm_phone_idx`. `save()` now normalizes state abbreviations (`Ohio` → `OH`) and computes `normalized_address`. |
| `Contact` | `contacts` | Added `normalized_name` (matching key, accent-folded, punctuation-stripped, titles dropped; indexed with `company_id`). `save()` applies light title-casing and computes `normalized_name` via `normalize_contact_name`. |
| `Lead` | `leads` | Added `LeadStatus.MERGED`, a `merged_into` FK (self-referential, soft, nullable) and `merged_at` timestamp so losing leads keep their provenance rows. Default querysets exclude merged leads (via `?include_merged=true` to override). |
| `DuplicateGroup` | `data_quality` | New — one potential duplicate pair with `reason_code`, `confidence`, `status` (OPEN/MERGED/KEPT_BOTH/IGNORED), cluster key, resolution metadata. |
| `DuplicateGroupMember` | `data_quality` | New — through-table linking a group to its two leads (role A/B). |
| `MergeAudit` | `data_quality` | New — immutable audit row written on every merge: winner, loser, reason, confidence, fields taken from the loser, preserved source list, performer. |

### Migrations

* `companies/migrations/0002_company_normalized_address_and_more.py`
* `contacts/migrations/0002_contact_normalized_name_and_more.py`
* `leads/migrations/0002_lead_merged_at_lead_merged_into_and_more.py`
* `data_quality/migrations/0001_initial.py`

### Normalization logic (extended `core/normalization.py`)

The existing helpers (`normalize_whitespace`, `normalize_company_name`,
`company_name_key`, `normalize_domain`, `normalize_email`, `normalize_phone`,
`build_full_name`, `split_full_name`) are unchanged. New functions added:

| Function | Behaviour |
| --- | --- |
| `normalize_address(street, city, state, zip, country)` | Lowercases, accent-folds, strips punctuation, shortens common street-type abbreviations (street→st, avenue→ave, suite→ste, etc.) and US directionals; normalises US state names to two-letter codes; returns a stable canonical string. |
| `address_key(...)` | Tight alphanumeric key (no spaces) built from `normalize_address` for equality checks. |
| `normalize_contact_name(first, last)` | Lowercases, strips accents/punctuation, drops honorifics (Dr/Mr/Mrs/Ms/Miss/Prof/Sir) and collapses whitespace. |
| `normalize_name_case(value)` | Light title-casing ("jane smith" → "Jane Smith") for cosmetic use only; never the dedup key. |
| `normalize_state(value)` | Maps full US state names to their two-letter abbreviations; passes through unknown values unchanged. |

All normalisation functions are **pure**, never invent data, and are unit tested
in `core/tests/test_normalization.py`.

### Duplicate detection logic

`apps/data_quality/services.py::detect_duplicates()` scans active (non-merged)
leads using five weighted rules plus one bonus rule. Detection is set-based —
no full table is loaded into Python memory — and already-existing groups are
not recreated on subsequent runs.

| Code | Rule | Confidence |
| --- | --- | --- |
| `EMAIL` | Same normalized e-mail across contacts (any company) | **100%** |
| `COMPANY_WEBSITE` | Multiple leads under the same company (domain-unique) | **95%** |
| `COMPANY_PHONE` | Same normalized phone across companies | **90%** |
| `COMPANY_ADDRESS` | Same normalized address across companies | **80%** |
| `CONTACT_NAME_COMPANY` | Same normalized contact name within the same company | **70%** |
| `COMPANY_CITY_STATE` | Same normalized company name + city + state (weaker) | **60%** |

Rules are ordered from highest confidence to lowest; each detected pair becomes
a `DuplicateGroup` with two members (A/B).

### Merge behaviour

`merge_leads(winner_id, loser_id, group=..., performed_by=...)` is
**transactional** (wrapped in `transaction.atomic()`):

1. Selects both leads with `select_for_update()`.
2. Validates the winner is not itself merged and the loser is not already merged.
3. Fills empty company fields from the loser company (industry, sub_industry,
   website, phone, street address, city, state, zip, country, employee count)
   without overwriting non-empty values on the winner.
4. Fills empty contact fields from the loser contact (first name, last name,
   job title, phone, email) without overwriting non-empty values.
5. Promotes the higher lead score and the more advanced pipeline status to the winner.
6. Saves the winner.
7. Marks the loser `lead_status=MERGED`, sets `merged_into=winner`, stamps
   `merged_at` — the loser is **never deleted**, so `source`, `source_file`,
   and `source_row_number` are preserved forever.
8. If a `DuplicateGroup` is passed, marks it MERGED with the surviving lead and resolution metadata.
9. Writes a `MergeAudit` row recording every field taken from the loser and
   the full source provenance list from both records.

No e-mails are invented; existing values are never blanked out.

### Source preservation

Both the surviving lead and the losing lead retain their original `source`,
`source_file`, and `source_row_number`. In addition, the `MergeAudit.merged_sources`
column stores a list of `{source, source_file, source_row_number, lead}` objects
so full provenance survives even if a loser's columns are later modified.

### Backend APIs

All endpoints live under `/api/v1/data-quality/` and are also reachable via the
unversioned API root. The module exports a `ping` route so smoke tests see it
as live.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/data-quality/` | Module status stub (`ping` — route existence) |
| `GET` | `/api/v1/data-quality/stats/` | Data-quality dashboard counters (all via DB aggregation) |
| `POST` | `/api/v1/data-quality/backfill/` | Re-run normalization across companies/contacts (admin utility) |
| `GET` | `/api/v1/data-quality/duplicates/` | Paginated list of duplicate groups; `status` filter defaults to `OPEN` |
| `GET` | `/api/v1/data-quality/duplicates/{id}/` | Pair detail: records A/B, reason, confidence |
| `POST` | `/api/v1/data-quality/duplicates/detect/` | Run duplicate detection (`{clear_existing: true}` resets) |
| `POST` | `/api/v1/data-quality/duplicates/{id}/merge/` | Merge two leads (`{winner, loser}`); returns `MergeAudit` |
| `POST` | `/api/v1/data-quality/duplicates/{id}/keep-both/` | Mark pair as not duplicates |
| `POST` | `/api/v1/data-quality/duplicates/{id}/ignore/` | Dismiss pair from the review queue |
| `GET` | `/api/v1/data-quality/missing-email/` | Paginated list of leads without a valid normalized e-mail (searchable, filterable by industry/city/state/source) |
| `GET` | `/api/v1/data-quality/merges/` | Merge audit log, paginated |

### Management commands

* `python manage.py backfill_data_quality` — re-applies normalization to all
  Companies and Contacts.
* `python manage.py detect_duplicates [--clear]` — runs all six duplicate rules;
  optionally clears existing groups before scanning.

### Frontend pages / components

Three new pages are registered in the sidebar under **Lead database**:

| Route | Page | Description |
| --- | --- | --- |
| `/data-quality` | `DataQualityPage` | KPI grid (total, valid/invalid/missing e-mails, missing phones, missing websites, missing contact names, open duplicates), quick actions to run a scan and open the review views. |
| `/duplicates` | `DuplicatesPage` | Paginated list of `DuplicateReviewCard`s showing Record A vs Record B with confidence badge, reason label, company/contact/email/phone/source; click-to-choose winner, **Merge**, **Keep both** and **Ignore** actions. |
| `/missing-email` | `MissingEmailPage` | Filterable/searchable list of leads without a valid e-mail — shows company, website, phone, contact, city, state, industry, source, source filename + row. No e-mails are guessed or generated. |

Supporting pieces:

* `types/dataQuality.ts` — TypeScript contracts mirroring the serializers.
* `services/dataQuality.service.ts` — typed fetch helpers and query keys.
* `hooks/useDataQuality.ts` — TanStack Query hooks including mutations for
  detect/merge/keep-both/ignore with automatic cache invalidation.
* `features/data-quality/components/StatsOverviewCard.tsx` — KPI tile grid.
* `features/data-quality/components/DuplicateReviewCard.tsx` — pairwise comparison with winner selection and action buttons.
* `lib/utils/toast.ts` — minimal in-page toast used for merge/ignore feedback.

Navigation is extended in `config/navigation.ts` and routes added in
`routes/AppRoutes.tsx` (all lazy-loaded, consistent with the rest of the shell).

### Performance considerations

* All dedup queries are set-based with `values_list` + dictionary grouping — no
  full-table ORM loads.
* Dedicated indexes on `normalized_email`, `normalized_phone`, `normalized_website`,
  `normalized_address`, `normalized_name`, and composite indexes
  `(state, city)`, `(normalized_name, city, state)`,
  `(company, normalized_name)` make detection rules index-friendly.
* Statistics use `COUNT` aggregations at the database layer; no records are
  pulled into Python memory.
* Merge logic operates on single pairs with `select_for_update()`; bulk operations
  (like initial migration population) are performed with `bulk_create`.

### Tests performed

* `python manage.py check` — passes with 0 issues.
* All Django migrations apply cleanly.
* **286 backend tests passing**, including:
  * Existing Phase 1–3 tests (health, accounts, companies, contacts, leads, imports).
  * `core/tests/test_normalization.py` — 61 tests covering whitespace, company name, domain, email, phone, name splitting **plus address normalization, contact name normalization, US state abbreviation, name-case formatting, address keys**.
  * `apps/data_quality/tests/test_services.py` — tests for:
    * email match @ 100% confidence,
    * company+website @ 95%,
    * company+phone @ 90%,
    * company+address @ 80%,
    * company+city+state @ 60%,
    * idempotency of re-running detection,
    * merge provenance preservation,
    * merge filling empty company/contact fields,
    * self-merge rejection,
    * audit record creation,
    * ignore / keep-both workflow actions,
    * missing-email queryset (including merged exclusion),
    * data-quality stats counts.
  * `apps/data_quality/tests/test_api.py` — HTTP round-trips for `/stats/`,
    `/duplicates/`, `/duplicates/detect/`, `/duplicates/{id}/merge/`,
    `/duplicates/{id}/keep-both/`, `/duplicates/{id}/ignore/`,
    `/missing-email/`.
* `npm run typecheck` (`tsc --noEmit`) — clean.
* `npm run build` (`tsc -b && vite build`) — production build succeeds.
* `npm test` (Vitest + Testing Library) — **51 tests** all passing, including
  existing route coverage for the three new pages.

### Known issues / non-goals

* Duplicate detection currently produces **pairs** rather than larger clusters;
  `cluster_key` is populated so the UI can group related pairs later, but the
  review UI treats them one-by-one, consistent with the brief.
* The scan is triggered manually (via the button or management command). A
  scheduled nightly scan can be added in a later phase.
* Frontend toast notifications are intentionally minimal (plain DOM nodes, no
  animation library). A shared design-system toast is a future refinement.
* Phase 5+ features (lead scoring, campaigns, SMTP sending, AI personalization,
  service matching, follow-ups, CRM workflows, advanced analytics) are
  deliberately **not** implemented, as per the scope boundary.
