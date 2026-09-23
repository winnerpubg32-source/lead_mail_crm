from __future__ import annotations

from django.contrib import admin

from apps.email_engine.models import DailyEmailUsage, EmailMessage, EmailTemplate


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "created_at", "updated_at")
    search_fields = ("name", "subject", "body")


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "campaign",
        "lead",
        "to_email",
        "status",
        "scheduled_at",
        "sent_at",
        "attempt_count",
    )
    list_filter = ("status", "campaign")
    search_fields = ("to_email", "subject", "error_message")
    readonly_fields = ("created_at", "updated_at", "attempt_count", "sent_at")


@admin.register(DailyEmailUsage)
class DailyEmailUsageAdmin(admin.ModelAdmin):
    list_display = ("date", "sent_count", "limit", "updated_at")
    readonly_fields = ("created_at", "updated_at")
