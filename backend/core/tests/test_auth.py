"""Basic authentication structure works end to end."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

User = get_user_model()

PASSWORD = "foundation-test-pass-123"


class AuthFoundationTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            email="founder@outreachos.test",
            password=PASSWORD,
            full_name="Ava Founder",
        )

    def test_user_is_created_with_email_login(self) -> None:
        self.assertEqual(self.user.email, "founder@outreachos.test")
        self.assertTrue(self.user.check_password(PASSWORD))
        self.assertTrue(self.user.is_active)

    def test_current_user_endpoint_requires_authentication(self) -> None:
        response = self.client.get("/api/v1/accounts/me/")
        self.assertEqual(response.status_code, 401)

    def test_token_authentication_returns_current_user(self) -> None:
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get("/api/v1/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "founder@outreachos.test")

    def test_login_returns_token_pair_shape(self) -> None:
        response = self.client.post(
            "/api/v1/accounts/login/",
            {"email": "founder@outreachos.test", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("token", body)
        self.assertEqual(body["user"]["email"], "founder@outreachos.test")

    def test_login_rejects_bad_credentials(self) -> None:
        response = self.client.post(
            "/api/v1/accounts/login/",
            {"email": "founder@outreachos.test", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_registration_creates_user(self) -> None:
        response = self.client.post(
            "/api/v1/accounts/register/",
            {
                "email": "new@outreachos.test",
                "full_name": "New User",
                "password": "another-strong-pass-9",
                "password_confirm": "another-strong-pass-9",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(User.objects.filter(email="new@outreachos.test").exists())

    def test_logout_deletes_token(self) -> None:
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.post("/api/v1/accounts/logout/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Token.objects.filter(user=self.user).exists())
