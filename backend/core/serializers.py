"""Serializers for the infrastructure endpoints."""

from __future__ import annotations

from rest_framework import serializers


class HealthSerializer(serializers.Serializer):
    """``GET /api/health/`` contract: ``{"status": "ok"}``."""

    status = serializers.CharField()
    service = serializers.CharField(required=False)
    version = serializers.CharField(required=False)
    environment = serializers.CharField(required=False)
    time = serializers.DateTimeField(required=False)


class DependencySerializer(serializers.Serializer):
    database = serializers.CharField()
    cache = serializers.CharField()
    broker = serializers.CharField()


class ReadinessSerializer(serializers.Serializer):
    status = serializers.CharField()
    latency_ms = serializers.FloatField(required=False, allow_null=True)
    dependencies = DependencySerializer()
