"""Serializers for the contacts module."""

from __future__ import annotations

from rest_framework import serializers

from apps.contacts.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    """Full contact representation."""

    company_name = serializers.CharField(read_only=True)

    class Meta:
        model = Contact
        fields = (
            "id",
            "company",
            "company_name",
            "first_name",
            "last_name",
            "full_name",
            "job_title",
            "email",
            "normalized_email",
            "phone",
            "normalized_phone",
            "phone_type",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "normalized_email",
            "normalized_phone",
            "created_at",
            "updated_at",
        )


class ContactListSerializer(ContactSerializer):
    """List payload including the company context used by the contacts table."""

    company_industry = serializers.CharField(source="company.industry", read_only=True, default="")
    company_city = serializers.CharField(source="company.city", read_only=True, default="")
    company_state = serializers.CharField(source="company.state", read_only=True, default="")

    class Meta(ContactSerializer.Meta):
        fields = (
            *ContactSerializer.Meta.fields,
            "company_industry",
            "company_city",
            "company_state",
        )
