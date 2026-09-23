"""Email template API views (Phase 6)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.email_engine.models import EmailTemplate
from apps.email_engine.serializers import (
    EmailTemplateSerializer,
    TemplatePreviewSerializer,
    template_variables,
)


class EmailEnginePingView(APIView):
    authentication_classes: tuple = ()
    permission_classes: tuple = (AllowAny,)

    def get(self, request):
        return Response({"module": "email_engine", "status": "live", "phase": 6})


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
