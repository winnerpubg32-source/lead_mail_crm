"""
Seed the database with a realistic B2B dataset for dashboard development.

This is **development tooling**, not an importer: the CSV/XLSX ingestion pipeline
(column mapping, chunked Celery processing, row-level error reporting) is a later
phase and must not be pre-empted here. The fixtures below exist so the Leads,
Companies and Contacts tables show believable rows while the import module is
still being built.

Usage::

    python manage.py seed_lead_data                 # 40 companies, ~90 leads
    python manage.py seed_lead_data --companies 120
    python manage.py seed_lead_data --flush         # wipe first, then reseed
    python manage.py seed_lead_data --flush --empty # wipe only (test empty states)
"""

from __future__ import annotations

import random
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from apps.companies.models import Company
from apps.contacts.models import Contact, PhoneType
from apps.leads.models import EmailStatus, Lead, LeadStatus
from core.normalization import split_full_name

# --- fixture vocabulary -----------------------------------------------------
#: Generic descriptors used when an industry has no dedicated list.
NAME_DESCRIPTORS = ["Industries", "Group", "Solutions", "Holdings", "Enterprises"]

INDUSTRIES: dict[str, list[str]] = {
    "Transportation & Logistics": ["Freight Brokerage", "Fleet Services", "Last Mile Delivery"],
    "Manufacturing": ["Precision Machining", "Industrial Components", "Packaging"],
    "Healthcare": ["Dental Groups", "Outpatient Clinics", "Diagnostics"],
    "Wholesale Distribution": ["Industrial Supply", "Food Service", "Electrical"],
    "Real Estate": ["Property Management", "Commercial Brokerage", "Multifamily"],
    "Hospitality": ["Hotel Groups", "Restaurant Groups", "Conference Centres"],
    "Professional Services": ["Accounting", "Engineering Consulting", "IT Managed Services"],
    "Construction": ["Commercial Builders", "Mechanical Contractors", "Roofing"],
    "Retail": ["Specialty Retail", "Consumer Electronics", "Home Improvement"],
    "Financial Services": ["Wealth Management", "Commercial Lending", "Insurance Brokerage"],
}

# name roots + legal suffix are combined to produce messy, realistic inputs.
NAME_ROOTS = [
    "Northwind",
    "Brightline",
    "Vertex",
    "Halcyon",
    "Copperfield",
    "Lakeshore",
    "Summit Ridge",
    "Ironwood",
    "Blue Harbor",
    "Cedar Park",
    "Redstone",
    "Meridian",
    "Granite Peak",
    "Silverbrook",
    "Harborview",
    "Stonebridge",
    "Pinecrest",
    "Riverton",
    "Beacon Hill",
    "Foxglove",
    "Clearwater",
    "Highland",
    "Oakfield",
    "Sable Creek",
    "Westgate",
    "Willow Bend",
    "Amber Point",
    "Bramble",
    "Kestrel",
    "Marsh Landing",
]

#: Descriptors are per industry so a generated name reads believably
#: ("Northwind Freight Systems" is transportation, not dentistry).
INDUSTRY_DESCRIPTORS: dict[str, list[str]] = {
    "Transportation & Logistics": [
        "Logistics",
        "Freight Systems",
        "Transport Group",
        "Cargo Lines",
    ],
    "Manufacturing": ["Precision Manufacturing", "Industries", "Fabrication", "Components"],
    "Healthcare": ["Dental Group", "Health Partners", "Medical Group", "Care Network"],
    "Wholesale Distribution": ["Supply Co.", "Distribution", "Wholesale Group", "Trading Co."],
    "Real Estate": ["Property Partners", "Realty Group", "Property Management", "Estates"],
    "Hospitality": ["Hospitality", "Hotel Group", "Resorts", "Restaurant Group"],
    "Professional Services": ["Consulting", "Advisory Group", "Services Group", "Associates"],
    "Construction": ["Builders", "Construction Group", "Contractors", "Mechanical"],
    "Retail": ["Retail Group", "Stores", "Outfitters", "Home & Garden"],
    "Financial Services": ["Financial Group", "Capital Partners", "Wealth Advisors", "Insurers"],
}

LEGAL_SUFFIXES = ["Inc.", "LLC", "Corp.", "Ltd.", "Group", "Co.", ""]

LOCATIONS: list[tuple[str, str, str, str]] = [
    ("Columbus", "OH", "43215", "1200 Meridian Plaza"),
    ("Tampa", "FL", "33602", "455 Harbour Island Blvd"),
    ("Grand Rapids", "MI", "49503", "88 Ottawa Ave NW"),
    ("Denver", "CO", "80202", "1700 Lincoln St"),
    ("Charlotte", "NC", "28202", "620 S Tryon St"),
    ("Milwaukee", "WI", "53202", "411 E Wisconsin Ave"),
    ("Salt Lake City", "UT", "84101", "222 S Main St"),
    ("Phoenix", "AZ", "85004", "1 E Washington St"),
    ("Nashville", "TN", "37201", "315 Union St"),
    ("Kansas City", "MO", "64106", "1100 Main St"),
    ("Portland", "OR", "97204", "805 SW Broadway"),
    ("Raleigh", "NC", "27601", "150 Fayetteville St"),
    ("Indianapolis", "IN", "46204", "1 Indiana Sq"),
    ("Omaha", "NE", "68102", "1299 Farnam St"),
    ("Boise", "ID", "83702", "250 S 5th St"),
    ("Louisville", "KY", "40202", "500 W Jefferson St"),
    ("Albuquerque", "NM", "87102", "500 Marquette Ave NW"),
    ("Des Moines", "IA", "50309", "666 Grand Ave"),
    ("Richmond", "VA", "23219", "919 E Main St"),
    ("Buffalo", "NY", "14202", "50 Fountain Plaza"),
]

#: Titles are matched to the industry so a dental group does not list a
#: "Plant Director" — the demo data should survive a design review.
INDUSTRY_JOB_TITLES: dict[str, list[str]] = {
    "Transportation & Logistics": [
        "VP Operations",
        "Head of Fleet",
        "Director of Dispatch",
        "Logistics Manager",
    ],
    "Manufacturing": [
        "Plant Director",
        "VP Manufacturing",
        "Production Manager",
        "Head of Quality",
    ],
    "Healthcare": [
        "Managing Partner",
        "Practice Manager",
        "Director of Clinical Ops",
        "Chief Medical Officer",
    ],
    "Wholesale Distribution": [
        "Purchasing Manager",
        "VP Supply Chain",
        "Warehouse Director",
        "Category Manager",
    ],
    "Real Estate": [
        "Managing Director",
        "Head of Property Management",
        "VP Acquisitions",
        "Portfolio Manager",
    ],
    "Hospitality": [
        "Regional Director",
        "General Manager",
        "Director of Revenue",
        "Head of Operations",
    ],
    "Professional Services": [
        "Managing Partner",
        "Director of Consulting",
        "Head of Delivery",
        "Principal Consultant",
    ],
    "Construction": [
        "VP Construction",
        "Project Director",
        "Chief Estimator",
        "Site Operations Manager",
    ],
    "Retail": [
        "Regional Manager",
        "Head of Merchandising",
        "Store Operations Director",
        "Category Buyer",
    ],
    "Financial Services": [
        "Chief Financial Officer",
        "Managing Director",
        "Head of Commercial Lending",
        "VP Wealth Management",
    ],
}

#: Fallback titles for industries without a dedicated list.
JOB_TITLES = [
    "VP Operations",
    "Chief Operating Officer",
    "Operations Manager",
    "Director of IT",
    "Procurement Lead",
    "Sales Director",
]

FIRST_NAMES = [
    "Marcus",
    "Elena",
    "Dale",
    "Priya",
    "Andre",
    "Nadia",
    "Gregory",
    "Sofia",
    "Trevor",
    "Amara",
    "Julian",
    "Hannah",
    "Owen",
    "Rosa",
    "Devon",
    "Maya",
    "Curtis",
    "Leah",
    "Victor",
    "Ingrid",
    "Rafael",
    "Colleen",
    "Simon",
    "Tessa",
    "Bruno",
    "Aisha",
    "Nathan",
    "Carmen",
]

LAST_NAMES = [
    "Whitfield",
    "Ruiz",
    "Kowalski",
    "Raghavan",
    "Boateng",
    "Fischer",
    "Alderman",
    "Marchetti",
    "Lindqvist",
    "Okafor",
    "Castellano",
    "Nguyen",
    "Brennan",
    "Delgado",
    "Sorensen",
    "Ali",
    "Whitaker",
    "Novak",
    "Petrov",
    "Gunnarsson",
    "Mendez",
    "Doyle",
    "Kim",
    "Ashford",
    "Rossi",
    "Hassan",
    "Fletcher",
    "Vargas",
]

SOURCES = [
    "dataset_import",
    "website_form",
    "referral",
    "outbound_prospecting",
    "trade_show_list",
    "partner_network",
]
SOURCE_WEIGHTS = [46, 18, 12, 12, 8, 4]

#: Every status is guaranteed to appear at least once so the dashboard's status
#: filters and chips always have data behind them. The weighted distribution
#: below fills the remainder.
#: Distribution across the pipeline (weight → status).
STATUS_WEIGHTS: list[tuple[LeadStatus, int]] = [
    (LeadStatus.NEW, 38),
    (LeadStatus.QUALIFIED, 16),
    (LeadStatus.CONTACTED, 18),
    (LeadStatus.REPLIED, 10),
    (LeadStatus.MEETING, 6),
    (LeadStatus.PROPOSAL, 4),
    (LeadStatus.WON, 3),
    (LeadStatus.LOST, 3),
    (LeadStatus.DO_NOT_CONTACT, 2),
]

#: E-mail deliverability mix, correlated with the status below.
EMAIL_STATUS_BY_STATUS: dict[str, list[EmailStatus]] = {
    LeadStatus.NEW: [EmailStatus.UNKNOWN, EmailStatus.VALID, EmailStatus.INVALID],
    LeadStatus.QUALIFIED: [EmailStatus.VALID, EmailStatus.VALID, EmailStatus.UNKNOWN],
    LeadStatus.CONTACTED: [EmailStatus.VALID, EmailStatus.VALID, EmailStatus.BOUNCED],
    LeadStatus.REPLIED: [EmailStatus.VALID],
    LeadStatus.MEETING: [EmailStatus.VALID],
    LeadStatus.PROPOSAL: [EmailStatus.VALID],
    LeadStatus.WON: [EmailStatus.VALID],
    LeadStatus.LOST: [EmailStatus.VALID, EmailStatus.INVALID],
    LeadStatus.DO_NOT_CONTACT: [EmailStatus.UNSUBSCRIBED, EmailStatus.SUPPRESSED],
}

#: Score band per status so the numbers look like a real pipeline.
SCORE_BY_STATUS: dict[str, tuple[int, int]] = {
    LeadStatus.NEW: (25, 68),
    LeadStatus.QUALIFIED: (70, 95),
    LeadStatus.CONTACTED: (55, 88),
    LeadStatus.REPLIED: (72, 97),
    LeadStatus.MEETING: (80, 99),
    LeadStatus.PROPOSAL: (84, 99),
    LeadStatus.WON: (88, 100),
    LeadStatus.LOST: (30, 70),
    LeadStatus.DO_NOT_CONTACT: (10, 60),
}


class Command(BaseCommand):
    help = "Seed realistic companies, contacts and leads for dashboard development."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--companies", type=int, default=40, help="Number of companies to create."
        )
        parser.add_argument(
            "--leads-per-company",
            type=int,
            default=2,
            help="Upper bound of leads generated per company.",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing companies (cascades to contacts) and leads first.",
        )
        parser.add_argument(
            "--empty",
            action="store_true",
            help="Only run the flush step — useful for testing empty states.",
        )
        parser.add_argument("--seed", type=int, default=20260923, help="Random seed.")

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        rng = random.Random(options["seed"])
        company_count: int = options["companies"]
        leads_per_company: int = options["leads_per_company"]

        if options["flush"]:
            deleted_leads = Lead.objects.all().delete()[0]
            deleted_companies = Company.objects.all().delete()[0]
            # Contacts cascade from Company; orphan contacts (no company) are removed too.
            deleted_contacts = Contact.objects.filter(company__isnull=True).delete()[0]
            self.stdout.write(
                self.style.WARNING(
                    f"Flushed: {deleted_leads} leads, {deleted_companies} companies/contacts, "
                    f"{deleted_contacts} orphan contacts."
                )
            )

        if options["empty"]:
            self.stdout.write(self.style.SUCCESS("Database is empty — nothing was seeded."))
            return

        # A file name per "import batch" so the source columns look realistic.
        source_files = [
            "us_businesses_q3_2026.csv",
            "midwest_manufacturing_set.xlsx",
            "healthcare_multi_site.csv",
            "trade_show_leads_2026.csv",
        ]

        status_deck = self._status_plan(rng, company_count * max(1, leads_per_company))
        status_index = 0

        created_companies = 0
        created_contacts = 0
        created_leads = 0
        used_domains: set[str] = set()
        used_names: set[str] = set()

        for index in range(company_count):
            industry = rng.choice(list(INDUSTRIES))
            sub_industry = rng.choice(INDUSTRIES[industry])
            name, slug = self._unique_company(rng, used_names, industry)
            city, state, zip_code, street = rng.choice(LOCATIONS)
            source = rng.choices(SOURCES, weights=SOURCE_WEIGHTS, k=1)[0]
            domain = f"{slug}.com"
            if domain in used_domains:
                domain = f"{slug}{index}.com"
            used_domains.add(domain)

            company = Company.objects.create(
                name=name,
                industry=industry,
                sub_industry=sub_industry,
                website=f"https://www.{domain}",
                phone=f"({rng.randint(200, 989)}) {rng.randint(200, 999)}-{rng.randint(1000, 9999)}",
                street_address=street,
                city=city,
                state=state,
                zip_code=zip_code,
                country="United States",
                employee_count=rng.choice([12, 28, 45, 60, 85, 120, 240, 380, 520, 850, 1400]),
                source=source,
            )
            created_companies += 1

            lead_target = rng.randint(1, max(1, leads_per_company))
            for _ in range(lead_target):
                first = rng.choice(FIRST_NAMES)
                last = rng.choice(LAST_NAMES)
                title = rng.choice(INDUSTRY_JOB_TITLES.get(industry, JOB_TITLES))
                local_part = f"{first[0].lower()}.{last.lower()}"
                email = f"{local_part}@{domain}"

                if Contact.objects.filter(company=company, email=email).exists():
                    continue

                contact = Contact.objects.create(
                    company=company,
                    first_name=first,
                    last_name=last,
                    job_title=title,
                    email=email,
                    phone=f"({rng.randint(200, 989)}) {rng.randint(200, 999)}-{rng.randint(1000, 9999)}",
                    phone_type=rng.choice([PhoneType.MOBILE, PhoneType.OFFICE, PhoneType.LANDLINE]),
                )
                created_contacts += 1

                if status_index < len(status_deck):
                    status = status_deck[status_index]
                else:
                    status = rng.choices(
                        [candidate for candidate, _ in STATUS_WEIGHTS],
                        weights=[weight for _, weight in STATUS_WEIGHTS],
                        k=1,
                    )[0]
                status_index += 1
                email_status = rng.choice(EMAIL_STATUS_BY_STATUS[status])
                low, high = SCORE_BY_STATUS[status]
                from_file = source in {"dataset_import", "trade_show_list"}

                Lead.objects.create(
                    company=company,
                    contact=contact,
                    lead_score=rng.randint(low, high),
                    lead_status=status,
                    email_status=email_status,
                    source=source,
                    source_file=rng.choice(source_files) if from_file else "",
                    source_row_number=rng.randint(2, 180_000) if from_file else None,
                )
                created_leads += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_companies} companies, {created_contacts} contacts, "
                f"{created_leads} leads."
            )
        )
        self.stdout.write(
            f"Totals now — companies: {Company.objects.count()}, "
            f"contacts: {Contact.objects.count()}, leads: {Lead.objects.count()}"
        )

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _status_plan(rng: random.Random, lead_budget: int) -> list[LeadStatus]:
        """
        Status sequence for the generated leads.

        Starts with one lead per status (shuffled so the order is not obvious),
        then appends a weighted sample for the rest of the budget.
        """
        guaranteed = [status for status, _ in STATUS_WEIGHTS]
        rng.shuffle(guaranteed)

        remaining = max(0, lead_budget - len(guaranteed))
        weighted = rng.choices(
            [status for status, _ in STATUS_WEIGHTS],
            weights=[weight for _, weight in STATUS_WEIGHTS],
            k=remaining,
        )
        plan = guaranteed + weighted
        rng.shuffle(plan)
        return plan

    @staticmethod
    def _unique_company(rng: random.Random, used: set[str], industry: str) -> tuple[str, str]:
        """Build a company name (industry-appropriate) plus its domain slug."""
        descriptors = INDUSTRY_DESCRIPTORS.get(industry, NAME_DESCRIPTORS)
        for _ in range(200):
            root = rng.choice(NAME_ROOTS)
            descriptor = rng.choice(descriptors)
            suffix = rng.choice(LEGAL_SUFFIXES)
            name = " ".join(part for part in (root, descriptor, suffix) if part)
            if name in used:
                continue
            used.add(name)
            slug = f"{root}{descriptor}".lower().replace(" ", "").replace(".", "").replace("&", "")
            return name, slug

        # Deterministic fallback keeps the command from looping forever.
        fallback_root, fallback_slug = split_full_name(rng.choice(FIRST_NAMES))
        name = f"{fallback_root} {rng.randint(1000, 9999)} Group"
        return name, f"{fallback_slug or 'company'}{rng.randint(1000, 9999)}".lower()
