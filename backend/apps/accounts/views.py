"""
Authentication endpoints — deliberately minimal.

Phase 1 provides: register, login (token + session), logout, current user.
Password reset, refresh tokens, SSO and 2FA belong to the authentication phase.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import (
    AuthTokenSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class AccountsRootView(APIView):
    """Tiny discovery endpoint proving the module is routed."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Accounts module root")
    def get(self, request):
        return Response(
            {
                "module": "accounts",
                "phase": 1,
                "status": "foundation",
                "endpoints": [
                    request.build_absolute_uri("register/"),
                    request.build_absolute_uri("login/"),
                    request.build_absolute_uri("logout/"),
                    request.build_absolute_uri("me/"),
                ],
            }
        )


class RegisterView(APIView):
    authentication_classes: tuple = ()
    permission_classes = (permissions.AllowAny,)

    @extend_schema(request=RegisterSerializer, responses={201: AuthTokenSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    authentication_classes: tuple = ()
    permission_classes = (permissions.AllowAny,)

    @extend_schema(request=LoginSerializer, responses={200: AuthTokenSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        user.last_seen_at = timezone.now()
        user.save(update_fields=["last_seen_at", "updated_at"])
        return Response({"token": token.key, "user": UserSerializer(user).data})


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user).data)
