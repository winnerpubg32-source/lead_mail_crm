"""Admin registration for data quality models."""

from __future__ import annotations

from django.contrib import admin

from apps.data_quality.models import DuplicateGroup, DuplicateGroupMember, MergeAudit


class DuplicateGroupMemberInline(admin.TabularInline):
    model = DuplicateGroupMember
    extra = 0
    raw_id_fields = ("lead",)


@admin.register(DuplicateGroup)
class DuplicateGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "reason_code", "confidence", "status", "created_at")
    list_filter = ("status", "reason_code")
    search_fields = ("cluster_key",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [DuplicateGroupMemberInline]


@admin.register(MergeAudit)
class MergeAuditAdmin(admin.ModelAdmin):
    list_display = ("id", "surviving_lead", "merged_lead", "reason_code", "created_at")
    list_filter = ("reason_code",)
    raw_id_fields = ("surviving_lead", "merged_lead", "duplicate_group")
    readonly_fields = ("created_at", "updated_at")
