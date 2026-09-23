"""Serializers for the companies module."""

from __future__ import annotations

from rest_framework import serializers

from apps.companies.models import Company


class CompanySerializer(serializers.ModelSerializer):
    """Full company representation (list + detail)."""

    lead_count = serializers.IntegerField(read_only=True)
    contact_count = serializers.IntegerField(read_only=True)
    location = serializers.CharField(read_only=True)
    domain = serializers.CharField(read_only=True)

    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "normalized_name",
            "industry",
            "sub_industry",
            "website",
            "normalized_website",
            "domain",
            "phone",
            "normalized_phone",
            "street_address",
            "city",
            "state",
            "zip_code",
            "country",
            "employee_count",
            "source",
            "location",
            "lead_count",
            "contact_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "normalized_name",
            "normalized_website",
            "normalized_phone",
            "created_at",
            "updated_at",
        )


class CompanyListSerializer(CompanySerializer):
    """Slimmer payload for list views — drops the fields the table never shows."""

    class Meta(CompanySerializer.Meta):
        fields = (
            "id",
            "name",
            "industry",
            "sub_industry",
            "website",
            "normalized_website",
            "phone",
            "city",
            "state",
            "country",
            "employee_count",
            "source",
            "location",
            "lead_count",
            "contact_count",
            "created_at",
            "updated_at",
        )


class CompanyOptionSerializer(serializers.ModelSerializer):
    """Minimal shape used to populate company pickers."""

    class Meta:
        model = Company
        fields = ("id", "name")
