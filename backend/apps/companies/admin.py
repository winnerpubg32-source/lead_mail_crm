from __future__ import annotations

from django.contrib import admin

from apps.companies.models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "city", "state", "employee_count", "source", "created_at")
    list_filter = ("industry", "state", "country", "source")
    search_fields = ("name", "normalized_name", "normalized_website", "city", "state")
    readonly_fields = (
        "normalized_name",
        "normalized_website",
        "normalized_phone",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
    list_per_page = 50
