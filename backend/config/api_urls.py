"""
API routing table for OutreachOS (``/api/``).

Three groups:

1. Infrastructure endpoints that are live in Phase 1 (health, auth basics).
2. Versioned (``/api/v1/``) mount points for every domain module. The routers
   for modules that are not implemented yet resolve to an empty URL pattern
   list, so the shape of the API is already fixed and later phases only have to
   fill in ``apps/<module>/urls.py``.
"""

from __future__ import annotations

from django.urls import include, path

urlpatterns = [
    # --- Infrastructure (live) ---------------------------------------------
    path("", include("core.urls")),
    # --- Domain modules (versioned) ----------------------------------------
    path("v1/accounts/", include("apps.accounts.urls")),
    path("v1/companies/", include("apps.companies.urls")),
    path("v1/contacts/", include("apps.contacts.urls")),
    path("v1/leads/", include("apps.leads.urls")),
    path("v1/imports/", include("apps.imports.urls")),
    path("v1/campaigns/", include("apps.campaigns.urls")),
    path("v1/email/", include("apps.email_engine.urls")),
    path("v1/ai/", include("apps.ai_engine.urls")),
    path("v1/crm/", include("apps.crm.urls")),
    path("v1/analytics/", include("apps.analytics.urls")),
    path("v1/suppression/", include("apps.suppression.urls")),
]
