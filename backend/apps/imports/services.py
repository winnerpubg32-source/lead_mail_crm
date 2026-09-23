"""
The import engine: turning an ``ImportJob`` into Companies, Contacts and Leads.

Design notes
------------
* **Chunked, streaming.** Rows are pulled from the file in blocks of
  :data:`CHUNK_SIZE`; each block is resolved with a handful of bulk queries
  (``__in`` lookups, ``bulk_create``) and then thrown away, so memory use is
  independent of the file size — a 500 000-row CSV costs the same as a 500-row
  one.
* **Idempotent.** A company is matched on its website domain, falling back to
  the normalized name; a contact on its e-mail inside the company; a lead on the
  company/contact pair. Re-importing the same file therefore creates nothing new:
  the rows land in ``duplicate_rows``.
* **Merge, never overwrite.** When a row matches an existing record, only
  *empty* fields are filled in. Existing values are never cleared and no e-mail
  is ever invented.
* **Row-level resilience.** A row that raises is counted in ``error_rows`` and
  recorded in ``job.issues``; the run continues. If a whole chunk hits a
  database constraint, it is retried row by row.

Every row ends in exactly one bucket: ``valid`` + ``duplicate`` + ``invalid`` +
``error`` equals ``processed_rows``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import UTC, datetime

from django.db import DatabaseError, transaction

from apps.companies.models import Company
from apps.contacts.models import Contact, PhoneType
from apps.imports.models import ImportJob, ImportStatus
from apps.imports.parsers import read_table
from apps.imports.records import MappingError, Record, build_plan, build_record
from apps.leads.models import Lead
from core.normalization import normalize_company_name, normalize_phone

logger = logging.getLogger(__name__)

__all__ = ["CHUNK_SIZE", "ImportRunner", "enqueue_import_job", "process_import_job"]

#: Rows handled per database round-trip.
CHUNK_SIZE = 500
#: Company fields that may be filled in on an existing record.
COMPANY_FILL_FIELDS = (
    "industry",
    "sub_industry",
    "website",
    "normalized_website",
    "phone",
    "normalized_phone",
    "street_address",
    "city",
    "state",
    "zip_code",
    "country",
    "employee_count",
)
CONTACT_FILL_FIELDS = (
    "first_name",
    "last_name",
    "job_title",
    "phone",
    "normalized_phone",
    "phone_type",
)


@dataclass
class ChunkResult:
    """Row outcomes for one chunk of the file."""

    processed: int = 0
    valid: int = 0
    duplicate: int = 0
    invalid: int = 0
    error: int = 0
    missing_email: int = 0
    new_companies: int = 0
    new_contacts: int = 0
    issues: list[dict] = dc_field(default_factory=list)


class ImportRunner:
    """
    Executes one ``ImportJob``.

    Instantiate with the job, call :meth:`run`. All state lives on the job row,
    which is updated after every chunk so the UI can poll progress.
    """

    def __init__(self, job: ImportJob) -> None:
        self.job = job
        self.file_path = job.upload.path if job.upload else ""
        self.headers: list[str] = list(job.headers or [])
        self.plan = None  # built in run()

    # ------------------------------------------------------------------ helpers
    def _default_source(self) -> str:
        """``import:contacts_2026.csv`` — provenance kept on every row."""
        return f"import:{self.job.filename}"[:120]

    def _load_plan(self):
        headers, _ = read_table(
            self.file_path, self.job.file_type, sheet=self.job.selected_sheet or None
        )
        if not headers:
            raise MappingError("The file has no header row.")
        self.headers = headers
        mapping = self.job.column_mapping or None
        self.plan = build_plan(headers, mapping or {})
        # Persist the resolved mapping the run actually used (including
        # auto-detected values if the job had none).
        self.job.headers = headers
        self.job.column_mapping = self.plan.column_mapping()
        return self.plan

    # ------------------------------------------------------------------- chunks
    def _chunk_rows(self):
        """Yield ``CHUNK_SIZE`` data rows at a time — the file is never fully read."""
        chunk: list = []
        _, data_rows = read_table(
            self.file_path,
            self.job.file_type,
            sheet=self.job.selected_sheet or None,
            encoding=self.job.encoding or None,
            delimiter=self.job.delimiter or None,
        )
        for row in data_rows:
            chunk.append(row)
            if len(chunk) >= CHUNK_SIZE:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

    def _resolve_companies(self, records: list[Record]) -> tuple[dict[str, Company], int]:
        """
        Find or create the company of every record in the chunk.

        Returns ``({company key: Company}, created count)``. Existing companies
        are enriched with anything the file knows and the database does not.
        """
        domains = {record.domain for record in records if record.domain}
        names = {record.normalized_name for record in records if record.normalized_name}

        by_domain: dict[str, Company] = {}
        by_name: dict[str, Company] = {}
        existing = (
            Company.objects.filter(normalized_website__in=domains)
            if domains
            else Company.objects.none()
        )
        for company in existing:
            by_domain.setdefault(company.normalized_website, company)
        existing = (
            Company.objects.filter(normalized_name__in=names) if names else Company.objects.none()
        )
        for company in existing:
            by_name.setdefault(company.normalized_name, company)

        resolved: dict[str, Company] = {}
        to_create: list[Company] = []
        source = self._default_source()

        for record in records:
            key = record.company_key
            company = by_domain.get(record.domain) if record.domain else None
            if company is None and record.normalized_name:
                company = by_name.get(record.normalized_name)
            if company is None and key in resolved:
                company = resolved[key]

            if company is not None:
                self._fill_company(company, record)
                resolved[key] = company
                continue

            company = Company(
                name=record.company_name,
                normalized_name=record.normalized_name,
                website=record.website,
                normalized_website=record.domain,
                industry=record.industry,
                sub_industry=record.sub_industry,
                phone=record.company_phone,
                normalized_phone=normalize_phone(record.company_phone),
                street_address=record.street_address,
                city=record.city,
                state=record.state,
                zip_code=record.zip_code,
                country=record.country or "United States",
                employee_count=record.employee_count,
                source=record.source or source,
            )
            to_create.append(company)
            resolved[key] = company
            if record.domain:
                by_domain[record.domain] = company
            if record.normalized_name:
                by_name[record.normalized_name] = company

        if to_create:
            # bulk_create skips save(), so the normalized twins are set above.
            created = Company.objects.bulk_create(
                to_create, batch_size=CHUNK_SIZE, ignore_conflicts=False
            )
            for company in created:
                if company.normalized_website:
                    by_domain[company.normalized_website] = company
                if company.normalized_name:
                    by_name[company.normalized_name] = company

        return resolved, len(to_create)

    @staticmethod
    def _fill_company(company: Company, record: Record) -> None:
        """Fill only empty fields from the file — never overwrite user edits."""
        changed = False
        values = {
            "industry": record.industry,
            "sub_industry": record.sub_industry,
            "website": record.website,
            "phone": record.company_phone,
            "street_address": record.street_address,
            "city": record.city,
            "state": record.state,
            "zip_code": record.zip_code,
            "employee_count": record.employee_count,
        }
        for name, value in values.items():
            if value and not getattr(company, name):
                setattr(company, name, value)
                changed = True
        if record.domain and not company.normalized_website:
            company.normalized_website = record.domain
            changed = True
        if record.company_phone and not company.normalized_phone:
            company.normalized_phone = normalize_phone(record.company_phone)
            changed = True
        if changed:
            company.save()

    def _resolve_contacts(
        self, records: list[Record], companies: dict[str, Company]
    ) -> tuple[dict[str, Contact], int]:
        """Find or create the contact of every record that carries one."""
        pairs = [
            (companies[record.company_key], record)
            for record in records
            if record.needs_contact and record.company_key in companies
        ]
        company_ids = {company.pk for company, _ in pairs}

        by_email: dict[tuple[int, str], Contact] = {}
        by_name: dict[tuple[int, str], Contact] = {}
        if company_ids:
            contacts = Contact.objects.filter(company_id__in=company_ids).only(
                "id", "company_id", "full_name", "normalized_email", "email"
            )
            for contact in contacts:
                if contact.normalized_email:
                    by_email.setdefault((contact.company_id, contact.normalized_email), contact)
                key = normalize_company_name(contact.full_name or contact.email)
                if key:
                    by_name.setdefault((contact.company_id, key), contact)

        resolved: dict[str, Contact] = {}
        to_create: list[Contact] = []

        for company, record in pairs:
            email = record.normalized_email
            name_key = normalize_company_name(record.contact_name)
            contact = by_email.get((company.pk, email)) if email else None
            if contact is None and name_key:
                contact = by_name.get((company.pk, name_key))
            if contact is None and record.contact_key:
                contact = resolved.get(f"{company.pk}:{record.contact_key}")

            if contact is not None:
                self._fill_contact(contact, record)
            else:
                contact = Contact(
                    company=company,
                    first_name=record.first_name,
                    last_name=record.last_name,
                    full_name=record.contact_name,
                    job_title=record.job_title,
                    email=record.email,
                    normalized_email=email,
                    phone=record.contact_phone,
                    normalized_phone=normalize_phone(record.contact_phone),
                    phone_type=record.phone_type
                    if record.phone_type in PhoneType.values
                    else PhoneType.UNKNOWN,
                )
                to_create.append(contact)
                if email:
                    by_email[(company.pk, email)] = contact
                if name_key:
                    by_name[(company.pk, name_key)] = contact

            if record.company_key:
                resolved[f"{company.pk}:{record.contact_key}"] = contact

        if to_create:
            created = Contact.objects.bulk_create(to_create, batch_size=CHUNK_SIZE)
            for contact in created:
                if contact.normalized_email and contact.company_id:
                    by_email[(contact.company_id, contact.normalized_email)] = contact
        return resolved, len(to_create)

    @staticmethod
    def _fill_contact(contact: Contact, record: Record) -> None:
        changed = False
        for name, value in (
            ("first_name", record.first_name),
            ("last_name", record.last_name),
            ("job_title", record.job_title),
            ("phone", record.contact_phone),
        ):
            if value and not getattr(contact, name):
                setattr(contact, name, value)
                changed = True
        if record.contact_name and not contact.full_name:
            contact.full_name = record.contact_name
            changed = True
        if record.contact_phone and not contact.normalized_phone:
            contact.normalized_phone = normalize_phone(record.contact_phone)
            changed = True
        if record.phone_type and contact.phone_type == PhoneType.UNKNOWN:
            contact.phone_type = record.phone_type
            changed = True
        if changed:
            contact.save()

    def _existing_lead_keys(
        self, pairs: list[tuple[int, int | None]]
    ) -> set[tuple[int, int | None]]:
        """Which (company, contact) pairs already have a lead, in one query."""
        company_ids = {company_id for company_id, _ in pairs}
        if not company_ids:
            return set()
        rows = Lead.objects.filter(company_id__in=company_ids).values_list(
            "company_id", "contact_id"
        )
        return set(rows)

    # ---------------------------------------------------------------------- run
    def run(self) -> ChunkResult:
        """Process the whole file; updates the job as it goes."""
        job = self.job
        job.status = ImportStatus.PROCESSING
        job.started_at = datetime.now(tz=UTC)
        job.error_message = ""
        job.issues = []
        job.save(
            update_fields=[
                "status",
                "started_at",
                "error_message",
                "issues",
                "updated_at",
            ]
        )

        total = ChunkResult()
        try:
            plan = self._load_plan()
            job.total_rows = 0
            job.save(update_fields=["headers", "column_mapping", "total_rows", "updated_at"])

            for chunk in self._chunk_rows():
                result = self._process_chunk(chunk, plan)
                self._accumulate(total, result)
                job.processed_rows += result.processed
                job.total_rows = max(job.total_rows, job.processed_rows)
                job.valid_rows += result.valid
                job.invalid_rows += result.invalid
                job.duplicate_rows += result.duplicate
                job.error_rows += result.error
                job.missing_email_rows += result.missing_email
                job.new_companies += result.new_companies
                job.new_contacts += result.new_contacts
                job.issues = (job.issues + result.issues)[: ImportJob.MAX_ISSUES]
                job.save(
                    update_fields=[
                        "total_rows",
                        "processed_rows",
                        "valid_rows",
                        "invalid_rows",
                        "duplicate_rows",
                        "error_rows",
                        "missing_email_rows",
                        "new_companies",
                        "new_contacts",
                        "issues",
                        "updated_at",
                    ]
                )

            job.status = ImportStatus.COMPLETED
            job.completed_at = datetime.now(tz=UTC)
            job.save(update_fields=["status", "completed_at", "updated_at"])
        except Exception as exc:
            logger.exception("Import job %s failed", job.pk)
            job.status = ImportStatus.FAILED
            job.completed_at = datetime.now(tz=UTC)
            job.error_message = f"{type(exc).__name__}: {exc}"[:2000]
            job.save(update_fields=["status", "completed_at", "error_message", "updated_at"])
            raise

        return total

    @staticmethod
    def _accumulate(total: ChunkResult, result: ChunkResult) -> None:
        for name in (
            "processed",
            "valid",
            "duplicate",
            "invalid",
            "error",
            "missing_email",
            "new_companies",
            "new_contacts",
        ):
            setattr(total, name, getattr(total, name) + getattr(result, name))
        total.issues.extend(result.issues)

    def _process_chunk(self, chunk: list, plan) -> ChunkResult:
        """
        Write one chunk, falling back to row-by-row when a bulk insert breaks.

        The fast path handles the common case; the fallback keeps one bad row
        from failing thousands of good ones.
        """
        try:
            with transaction.atomic():
                return self._write_chunk(chunk, plan)
        except DatabaseError as exc:
            # Constraint violation, bad value, …: retry one row at a time so a
            # single bad row cannot fail thousands of good ones.
            logger.warning("Chunk insert failed (%s) — retrying row by row", exc)
            return self._write_rows_individually(chunk, plan)

    def _write_chunk(self, chunk: list, plan) -> ChunkResult:
        result = ChunkResult()
        records = [build_record(row.number, row.values, plan) for row in chunk]

        usable = [record for record in records if record.is_usable]
        for record in records:
            result.processed += 1
            if not record.is_usable:
                result.invalid += 1
                self._note(result, record, "invalid", "Skipped: no business name")

        if not usable:
            return result

        companies, new_companies = self._resolve_companies(usable)
        contacts, new_contacts = self._resolve_contacts(usable, companies)
        result.new_companies += new_companies
        result.new_contacts += new_contacts

        pairs: list[tuple[int, int | None]] = []
        for record in usable:
            company = companies.get(record.company_key)
            contact = (
                contacts.get(f"{company.pk}:{record.contact_key}")
                if company and record.needs_contact
                else None
            )
            pairs.append((company.pk, contact.pk if contact else None))

        existing = self._existing_lead_keys(pairs)
        source = self._default_source()
        new_leads: list[Lead] = []

        for record, (company_id, contact_id) in zip(usable, pairs, strict=True):
            key = (company_id, contact_id)
            if key in existing:
                result.duplicate += 1
                outcome = "duplicate"
            else:
                existing.add(key)
                contact = contacts.get(f"{company_id}:{record.contact_key}") if contact_id else None
                new_leads.append(
                    Lead(
                        company_id=company_id,
                        contact_id=contact_id,
                        lead_score=0,
                        source=record.source or source,
                        source_file=self.job.filename[:255],
                        source_row_number=record.row,
                    )
                )
                result.valid += 1
                outcome = "valid"

            has_email = bool(record.normalized_email) or bool(contact and contact.normalized_email)
            if not has_email:
                result.missing_email += 1
            for issue in record.issues:
                self._note(result, record, "warning", issue.message, outcome=outcome)

        if new_leads:
            Lead.objects.bulk_create(new_leads, batch_size=CHUNK_SIZE)

        return result

    def _write_rows_individually(self, chunk: list, plan) -> ChunkResult:
        """Slow but safe: one transaction per row so a single bad row is isolated."""
        merged = ChunkResult()
        for row in chunk:
            try:
                with transaction.atomic():
                    partial = self._write_chunk([row], plan)
            except Exception as exc:
                logger.warning("Row %s failed: %s", row.number, exc)
                partial = ChunkResult(processed=1, error=1)
                partial.issues.append(
                    {
                        "row": row.number,
                        "level": "error",
                        "message": f"{type(exc).__name__}: {exc}"[:200],
                    }
                )
            self._accumulate(merged, partial)
        return merged

    @staticmethod
    def _note(
        result: ChunkResult,
        record: Record,
        level: str,
        message: str,
        *,
        outcome: str = "",
    ) -> None:
        """Collect a bounded sample of row problems for the result panel."""
        if len(result.issues) >= ImportJob.MAX_ISSUES:
            return
        entry = {"row": record.row, "level": level, "message": message}
        if outcome:
            entry["outcome"] = outcome
        result.issues.append(entry)


def process_import_job(job_id: int) -> dict:
    """
    Run one import job (entry point shared by Celery, the fallback thread and
    tests). Returns a small summary dict instead of a model instance so it can
    travel through the broker.
    """
    job = ImportJob.objects.get(pk=job_id)
    if job.status in {ImportStatus.PROCESSING, ImportStatus.COMPLETED}:
        # Guard against a double submit (double click / retry after a worker loss).
        return {"job": job.pk, "status": job.status, "skipped": True}

    result = ImportRunner(job).run()
    return {
        "job": job.pk,
        "status": job.status,
        "processed": result.processed,
        "imported": result.valid,
        "duplicates": result.duplicate,
        "invalid": result.invalid,
        "errors": result.error,
        "missing_email": result.missing_email,
    }


def enqueue_import_job(job: ImportJob) -> str:
    """
    Hand the job to Celery.

    If the broker is unreachable the import still runs — in a background thread —
    so a missing worker degrades to "slow" instead of "broken". Returns the
    dispatch mode for logging/tests: ``"celery"`` or ``"thread"``.
    """
    from apps.imports.tasks import run_import_job

    try:
        run_import_job.delay(job.pk)
        return "celery"
    except Exception as exc:
        logger.warning(
            "Celery broker unavailable (%s) — running import %s in a thread", exc, job.pk
        )
        import threading

        thread = threading.Thread(
            target=process_import_job,
            args=(job.pk,),
            name=f"import-job-{job.pk}",
            daemon=True,
        )
        thread.start()
        return "thread"
