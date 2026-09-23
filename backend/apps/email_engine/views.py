"""Email template, delivery queue, and daily quota API views."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.email_engine.models import EmailMessage, EmailTemplate
from apps.email_engine.serializers import (
    EmailMessageSerializer,
    EmailTemplateSerializer,
    TemplatePreviewSerializer,
    email_status_vocabulary,
    template_variables,
)
from apps.email_engine.services import daily_usage_payload


class EmailEnginePingView(APIView):
    authentication_classes: tuple = ()
    permission_classes: tuple = (AllowAny,)

    def get(self, request):
        return Response({"module": "email_engine", "status": "live", "phase": 7})


class EmailUsageView(APIView):
    """Workspace-safe daily quota payload; SMTP secrets are never serialized."""

    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(daily_usage_payload())


@extend_schema_view(
    list=extend_schema(summary="List email templates", tags=["email", "templates"]),
    retrieve=extend_schema(summary="Retrieve a template", tags=["email", "templates"]),
    create=extend_schema(summary="Create an email template", tags=["email", "templates"]),
    update=extend_schema(summary="Replace a template", tags=["email", "templates"]),
    partial_update=extend_schema(summary="Patch a template", tags=["email", "templates"]),
    destroy=extend_schema(summary="Delete a template", tags=["email", "templates"]),
)
class EmailTemplateViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD for reusable email templates."""

    permission_classes = (AllowAny,)
    serializer_class = EmailTemplateSerializer
    queryset = EmailTemplate.objects.all()
    ordering_fields = ("name", "created_at", "updated_at")
    ordering = ("-updated_at",)

    @action(detail=True, methods=["post"], url_path="preview")
    def preview(self, request, pk=None):
        """Render the template against sample data (or posted context override)."""
        template = self.get_object()
        serializer = TemplatePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.preview(template=template))

    @action(detail=False, methods=["post"], url_path="preview-inline")
    def preview_inline(self, request):
        """Preview an unsaved subject/body blob (for the editor as-you-type)."""
        serializer = TemplatePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.preview(template=None))

    @action(detail=False, methods=["get"], url_path="variables")
    def variables(self, request):
        return Response(template_variables())


class EmailMessageViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Read-only delivery history for campaign detail and operations views."""

    permission_classes = (AllowAny,)
    serializer_class = EmailMessageSerializer
    queryset = EmailMessage.objects.select_related("campaign", "lead", "lead__company")
    filterset_fields = ("campaign", "lead", "status")
    ordering_fields = ("scheduled_at", "sent_at", "created_at", "attempt_count")
    ordering = ("-created_at",)

    @action(detail=False, methods=["get"], url_path="statuses")
    def statuses(self, request):
        return Response(email_status_vocabulary())
