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
| Phase 5 — Lead Management (scoring, detail page, bulk actions, CSV export, activity timeline) | ✅ Completed |
| Phase 6+ (campaigns, SMTP, AI personalization, service matching, follow-ups, CRM, analytics) | ⛔ Not implemented |

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

---

## Phase 5 Implementation

Phase 5 introduces professional lead-management tooling on top of Phases 1–4:
a richer lead table with all required columns + bulk selection, configurable
point-based lead scoring with HOT/WARM/COLD/UNQUALIFIED tiers, per-lead detail
pages showing contact info + score breakdown + notes + activity timeline,
bulk actions (status/industry change, campaign assignment placeholder,
suppression, CSV export), and an append-only activity log on every lead.

### New / updated modules

| Module | Purpose |
| --- | --- |
| `apps/leads/scoring.py` | `POINTS` config, `ScoreComponents` dataclass, `ScoreClassification` enum (HOT/WARM/COLD/UNQUALIFIED), `compute_lead_score`, `score_leads_qs`, `rescore_leads`. Clamps scores to [0,100]; blocked e-mail statuses (INVALID/BOUNCED/UNSUBSCRIBED/SUPPRESSED) force score = 0 → UNQUALIFIED. |
| `apps/leads/activity_models.py` | `ActivityType` enum (CREATED/STATUS_CHANGE/SCORE_CHANGE/NOTE_ADDED/EMAIL_SENT/EMAIL_OPENED/REPLY/MEETING/MERGED/SUPPRESSED/BULK_EDIT/CAMPAIGN_ADDED/EXPORTED/MANUAL_EDIT/VALIDATION), `LeadActivity` (append-only event log with `metadata` JSONField) and `LeadNote` (free-text notes). |
| `apps/leads/signals.py` + `apps.py` | Post-save hook that auto-computes an initial score for newly created leads and logs a `CREATED` activity. Explicitly-set scores are not overwritten (seed data / tests keep their values). |
| `apps/leads/services.py` | `annotate_lead_list` (adds `last_contact_at`/`note_count`/`activity_count` annotations to list querysets so the table stays O(1) queries), `record_activity`, `record_bulk_action`, `apply_bulk_action` (transactional bulk status/industry/campaign/suppress/export with activity logging), `export_leads_csv` (respects the current filters). |
| `apps/leads/filters.py` | Adds `sub_industry`, `has_website`, `score_classification` (HOT/WARM/COLD/UNQUALIFIED, correctly handling blocked-e-mail leads) and preserves existing filters. |
| `apps/leads/serializers.py` | `LeadDetailSerializer` includes `notes`, `activities` and `score_breakdown`; list serializer exposes new columns (website, sub_industry, street_address, zip_code, country, last_contact, score_classification, crm_status). Bulk-action and note serializers added. |
| `apps/leads/views.py` | New routes: notes, timeline, rescore, rescore-all, bulk-action, export, filters, statuses (with score classification counts). `perform_update` logs STATUS_CHANGE / SCORE_CHANGE activities and re-scores after edits. |

### Migrations

* `leads/migrations/0003_leadactivity_leadnote.py` — adds `LeadActivity` and `LeadNote` tables.

### Scoring rules (locked in code)

| Signal | Points |
| --- | --- |
| Valid e-mail | +20 |
| Has website | +15 |
| Named contact | +10 |
| Phone present | +10 |
| Industry known | +10 |
| Location (city + state) | +10 |
| Website accessible (proxy: website field populated) | +15 |
| Invalid e-mail | −30 |
| Suppressed / Unsubscribed / Bounced | −100 (hard block → 0 & UNQUALIFIED) |

Classification thresholds: HOT ≥ 70, WARM 50–69, COLD 20–49, UNQUALIFIED < 20 (or any blocked e-mail status). **No automatic e-mail sending** is triggered by score.

### Backend APIs

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/leads/` | Paginated list with new columns (sub_industry, website, score_classification, last_contact, source) + additional filters (sub_industry, has_website, score_classification). |
| `GET` | `/api/v1/leads/{id}/` | Detail payload: full company/contact info, notes, activities, score breakdown. |
| `PATCH` | `/api/v1/leads/{id}/` | Update lead_status / email_status / lead_score / source. Logs activity and re-scores. |
| `POST` | `/api/v1/leads/{id}/notes/` | Add a note; appends a `NOTE_ADDED` activity. |
| `GET` | `/api/v1/leads/{id}/timeline/` | Activity timeline (latest 200). |
| `POST` | `/api/v1/leads/{id}/rescore/` | Recompute score and log a `SCORE_CHANGE` activity. |
| `POST` | `/api/v1/leads/bulk-action/` | Bulk `change_status`, `change_industry`, `assign_campaign` (placeholder), `suppress`, `export`. All actions log `BULK_EDIT`/`STATUS_CHANGE`/`SUPPRESSED`/etc. activities per lead. |
| `GET` | `/api/v1/leads/export/` | CSV download respecting the active filters. |
| `GET` | `/api/v1/leads/filters/` | Distinct industry/sub_industry/city/state/source values for dynamic filter dropdowns. |
| `GET` | `/api/v1/leads/statuses/` | Enum vocabulary extended with score classification counts and point config. |

### Frontend pages / components

| Route | Page | Description |
| --- | --- | --- |
| `/leads` | `LeadsPage` (expanded) | All 13 columns from the brief (Business, Contact, Email, Phone, Industry, Sub-industry, City, State, Lead Score, Email Status, CRM Status, Source, Last Contact). Checkbox column for bulk row selection; bulk action bar with status/industry/campaign/suppress/export; CSV export button; expanded filters (sub_industry, has_email, has_website, score_classification, source). |
| `/leads/:id` | `LeadDetailPage` (new) | Header/contact card with company/contact/email/phone/website/address, side rail with score breakdown (colored by classification), record details card, activity timeline, notes editor, and a "Campaign history" placeholder card. "Recompute score" action triggers a rescore + refresh. |

Supporting pieces:

* `features/leads/components/LeadTable.tsx` — rewritten with new columns, checkbox selection, colored score chips (HOT/WARM/COLD/UNQUALIFIED), Last Contact relative timestamps, links to detail page.
* `features/leads/components/BulkActionBar.tsx` — sticky toolbar shown when rows are selected.
* `features/leads/components/ContactCard.tsx`, `ScoreBreakdown.tsx`, `ActivityTimeline.tsx`, `NotesPanel.tsx` — detail page cards.
* `components/ui/Textarea.tsx` — small shared textarea used by notes.
* `hooks/useLeads.ts` — extended with `useLead`, `useLeadFilterOptions`, `useUpdateLead`, `useAddLeadNote`, `useRescoreLead`, `useBulkAction`, `useExportLeads`.
* `services/leads.service.ts` — typed helpers for all new endpoints plus a CSV export helper that downloads the blob with the server-provided filename.
* `config/status.ts` — `scoreClassification`, `scoreClassificationConfig`, `ACTIVITY_ICONS`; score colors/tone aligned to HOT/WARM/COLD/UNQUALIFIED; MERGED added to lead status config.
* `config/list-options.ts` — score filters use classification labels (HOT/WARM/COLD/UNQUALIFIED) instead of raw numeric cutoffs.
* `lib/api/client.ts` — query parameter serializer supports repeated keys (array values → multiple `?key=v1&key=v2`) for future multi-select filters.
* `lib/utils/toast.ts` — `toast.success/error/info` convenience shortcuts.

### Performance considerations

* List querysets are annotated once via `annotate_lead_list` using a single `Subquery`, avoiding N+1 activity queries per row.
* Score counts on the statuses endpoint iterate leads in chunks (`iterator(chunk_size=500)`).
* Bulk actions run inside a single `transaction.atomic()` and re-score only the affected IDs.
* CSV export streams rows via Django's `iterator(chunk_size=500)` so the whole table isn't pulled into memory at once.
* Lead row links use react-router `<Link>` for instant transitions; selections live in page state, clearing on navigation.

### Tests performed

* `python manage.py check` — passes with 0 issues.
* New migration `0003_leadactivity_leadnote` applies cleanly.
* **297 backend tests passing** (up from 286). New tests cover:
  * scoring rules, classification thresholds, blocked-email zeroing;
  * locked point-value config contract;
  * detail payload includes notes, activities, score breakdown, new fields;
  * add-note endpoint logs NOTE_ADDED activity;
  * rescore endpoint recomputes score and persists it;
  * bulk status change and bulk suppress set status/email/score correctly and log activities;
  * CSV export returns valid CSV with the lead row;
  * HOT/WARM/COLD/UNQUALIFIED filters return correct counts (blocked e-mails always fall into UNQUALIFIED).
* `tsc --noEmit` — clean.
* `npm run build` — production build succeeds (LeadDetailPage chunk: 13 kB gzipped 4 kB).
* `npm test` (Vitest) — **49 tests** all passing, including the updated LeadsPage test covering all new columns.

---

## Phase 6 Implementation

Phase 6 ships **Campaign Management** and **Email Templates**. It validates
and prepares outreach campaigns against the lead database but does **not**
send real e-mails — SMTP delivery is deferred to Phase 7, per the brief.

### New models

| Model | App | Purpose |
| --- | --- | --- |
| `Campaign` | `campaigns` | name, description, industry, sub_industry, location, minimum_lead_score, daily_limit, status (DRAFT/READY/RUNNING/PAUSED/COMPLETED/CANCELLED), template FK, scheduled start/end, recommended_service, sent/reply/meeting counters, eligible_count (cached audience snapshot). |
| `CampaignLead` | `campaigns` | Audience membership join table with send_status (PENDING/QUEUED/SENT/REPLIED/BOUNCED/SKIPPED) and timestamps. `(campaign, lead)` is unique. |
| `EmailTemplate` | `email_engine` | name, description, subject, body, default_recommended_service, plus derived helpers `used_variables` / `unknown_variables` / `missing_variables` / `render_preview`. |

### Migrations

* `campaigns/migrations/0001_initial.py` — `Campaign` + `CampaignLead` + indexes.
* `email_engine/migrations/0001_initial.py` — `EmailTemplate`.

### Template engine

Supported variables (validated, documented in `/api/v1/email/templates/variables/`):

    {{first_name}}, {{contact_name}}, {{company_name}}, {{industry}},
    {{city}}, {{state}}, {{website}}, {{recommended_service}}

Unknown variables are flagged in the API response and in the UI. Subject and
body are rendered server-side via `render_template`, with a sample lead used
for previews. Inline preview is available for editor-as-you-type.

### Campaign services

* `eligible_leads_qs(campaign)` — applies audience filters (industry,
  sub_industry icontains, location OR-matched against city/state/country,
  minimum_lead_score, deliverable e-mail, not MERGED).
* `count_eligible_leads(campaign)` — cheap `COUNT`.
* `validate_campaign_for_launch(campaign)` — returns a list of human-readable
  errors (name length, daily limit, template required, scheduled end > start,
  non-empty audience).
* `prepare_campaign(campaign)` — transactional; validates, snapshots eligible
  leads into `CampaignLead` (PENDING), sets `eligible_count`, transitions to
  READY.
* `transition_campaign(campaign, new_status)` — enforces allowed transitions;
  DRAFT→RUNNING auto-prepares. Phase 6 never creates `EmailMessage` rows or
  calls SMTP.

### Backend APIs

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/campaigns/` | Paginated list (search + status filter + sort). |
| `POST` | `/api/v1/campaigns/` | Create draft. |
| `GET` | `/api/v1/campaigns/{id}/` | Detail (with template, membership count). |
| `PATCH` | `/api/v1/campaigns/{id}/` | Update (wizard saves). |
| `DELETE` | `/api/v1/campaigns/{id}/` | Cancel (blocked while RUNNING/PAUSED) and delete. |
| `POST` | `/api/v1/campaigns/{id}/status/` | Transition status (DRAFT→READY→RUNNING→PAUSED→…). |
| `POST` | `/api/v1/campaigns/{id}/prepare/` | Validate + snapshot audience; response confirms no e-mails are sent. |
| `GET` | `/api/v1/campaigns/{id}/preview-audience/` | Paginated leads currently matching the audience rules. |
| `GET` | `/api/v1/campaigns/{id}/members/` | Paginated `CampaignLead` rows. |
| `GET` | `/api/v1/campaigns/{id}/validate/` | Live `valid`, `errors`, `eligible_count` for the wizard. |
| `GET` | `/api/v1/campaigns/statuses/` | Enum vocabulary with per-status counts. |
| `GET` | `/api/v1/email/templates/` | List templates. |
| `POST` | `/api/v1/email/templates/` | Create template. |
| `GET`/`PATCH`/`DELETE` | `/api/v1/email/templates/{id}/` | Retrieve/update/delete. |
| `POST` | `/api/v1/email/templates/{id}/preview/` | Render template against optional context. |
| `POST` | `/api/v1/email/templates/preview-inline/` | Render an unsaved subject/body blob (editor live preview). |
| `GET` | `/api/v1/email/templates/variables/` | Supported variable list + sample lead. |

A backward-compat `ping` endpoint is kept at `/api/v1/{campaigns,email}/ping`
so the existing core health-check test passes.

### Frontend

| Route | Page | Description |
| --- | --- | --- |
| `/campaigns` | `CampaignsPage` | Table: Campaign, Audience chips, Eligible Leads, Daily Limit, Sent, Replies, Status. Toolbar search + status filter. Empty states + New campaign button. |
| `/campaigns/:id` | `CampaignDetailPage` | Header with lifecycle actions (Prepare / Launch dry-run / Pause / Resume / Cancel / Complete), stat tiles, progress bar, audience + delivery details, template preview. |
| `/templates` | `TemplatesPage` | Template cards grid with New/Edit/Delete. |
| Modal | `CampaignWizard` | 5-step wizard: Audience → Service → Template → Schedule → Review. Save on step 4; final step "Launch" calls the prepare endpoint (no e-mails sent). |
| Component | `TemplateEditor` | Two-pane editor with variable-tag chips, unknown-variable warnings, and live preview rendered against sample lead data (client-side for instant feedback). |
| Component | `Progress` | Minimal shared progress bar (added to the UI kit for tables + cards). |

Supporting files:
* `types/campaign.ts` — `Campaign`, `EmailTemplate`, `CampaignMember`, status types, wizard draft.
* `services/campaigns.service.ts` — typed CRUD + status/prepare/validate/audience/members + templates + preview.
* `hooks/useCampaigns.ts` — TanStack Query hooks + mutations with automatic cache invalidation.
* `config/status.ts` — `campaignStatusConfig` with both Phase 6 UPPERCASE and dashboard-mock lowercase keys.
* `config/navigation.ts` — `/campaigns` and `/templates` marked `live`.

### Tests performed

* `python manage.py check` — 0 issues.
* New migrations apply cleanly.
* **312 backend tests passing** (up from 297). New tests cover:
  * template variable rendering, unknown-variable detection,
  * campaign creation, validation errors (missing template),
  * eligible-lead audience filtering by industry/minimum_lead_score,
  * prepare-endpoint audience snapshot + READY transition,
  * RUNNING transition without sending (counters stay 0),
  * list, statuses, validate, preview-audience endpoints.
* `tsc --noEmit` clean.
* `npm run build` succeeds; new chunks: CampaignsPage, CampaignDetailPage, CampaignWizard, TemplatesPage.
* `npm test` (Vitest) — **47 tests passing**; campaigns/templates routes removed from placeholder tests and mocked to stay offline.

### Non-goals (Phase 7+)

* Real SMTP delivery, per-mailbox configuration, daily send-budget enforcement.
* Campaign steps / sequences beyond a single template.
* Open/click tracking, bounce/complaint webhooks, automatic STOP-ON-REPLY.
* Variable personalization via the AI engine.
