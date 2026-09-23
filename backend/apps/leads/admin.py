from __future__ import annotations

from django.contrib import admin

from apps.leads.models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("__str__", "lead_status", "email_status", "lead_score", "source", "created_at")
    list_display_links = ("__str__",)
    list_filter = ("lead_status", "email_status", "source")
    search_fields = (
        "company__name",
        "contact__full_name",
        "contact__email",
        "source_file",
    )
    autocomplete_fields = ("company", "contact")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_select_related = ("company", "contact")
    list_per_page = 50
