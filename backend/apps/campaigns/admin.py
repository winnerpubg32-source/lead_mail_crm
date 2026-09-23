from __future__ import annotations

from django.contrib import admin

from apps.campaigns.models import Campaign, CampaignLead


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "eligible_count", "sent_count", "daily_limit", "updated_at")
    list_filter = ("status",)
    search_fields = ("name", "description", "recommended_service")


@admin.register(CampaignLead)
class CampaignLeadAdmin(admin.ModelAdmin):
    list_display = ("campaign", "lead", "send_status", "sent_at", "replied_at")
    list_filter = ("send_status", "campaign")
    search_fields = ("campaign__name", "lead__contact__email", "lead__company__name")
