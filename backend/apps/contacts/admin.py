from __future__ import annotations

from django.contrib import admin

from apps.contacts.models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("full_name", "job_title", "company", "email", "phone_type", "created_at")
    list_filter = ("phone_type", "company__industry", "company__state")
    search_fields = ("first_name", "last_name", "full_name", "email", "job_title", "company__name")
    autocomplete_fields = ("company",)
    readonly_fields = ("normalized_email", "normalized_phone", "created_at", "updated_at")
    list_select_related = ("company",)
    list_per_page = 50
