from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User

CREATE_USER_URL = reverse("users:create")
TOKEN_URL = reverse("users:token_obtain_pair")
ME_URL = reverse("users:manage")


def sample_user(**params):
    defaults = {
        "email": "sample@user.com",
        "password": "Samplepassword"
    }
    defaults.update(params)

    return defaults


def create_user(**params) -> User:
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_user_success(self) -> None:
        data = sample_user()

        res = self.client.post(CREATE_USER_URL, data)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertEqual(user.check_password(data["password"]), True)
        self.assertNotIn("password", res.data)

    def test_user_exists(self) -> None:
        data = sample_user()
        create_user(**data)

        res = self.client.post(CREATE_USER_URL, data)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_short(self) -> None:
        payload = {
            "email": "sample@user.com",
            "password": "Samp"
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test_create_token_user(self) -> None:
        data = sample_user()

        create_user(**data)

        res = self.client.post(TOKEN_URL, data)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self) -> None:
        create_user(email="sample@user.com", password="Sampleuser")

        data = sample_user()

        res = self.client.post(TOKEN_URL, data)
        self.assertNotIn("access", res.data)
        self.assertNotIn("refresh", res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_nouser(self) -> None:
        data = sample_user()

        res = self.client.post(TOKEN_URL, data)
        self.assertNotIn("access", res.data)
        self.assertNotIn("refresh", res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_missing_field(self) -> None:
        res = self.client.post(TOKEN_URL, {"email": "test@test.com", "password": ""})

        self.assertNotIn("access", res.data)
        self.assertNotIn("refresh", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self) -> None:
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticateUserApiTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user(
            email="test@test.com",
            password="Testpassword",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile(self) -> None:
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "id": self.user.id,
                "email": self.user.email,
                "is_staff": self.user.is_staff,
            },
        )

    def test_post_me_not_allowed(self) -> None:
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_self(self) -> None:
        payload = {"email": "12345@test.com", "password": "newpassword"}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, payload["email"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
