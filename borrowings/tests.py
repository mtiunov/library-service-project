import json
from unittest.mock import patch, AsyncMock
from django.conf import settings

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from datetime import date, timedelta, datetime

from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.filters import BorrowingFilter
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer, BorrowingDetailSerializer
from users.tests import create_user

BORROWINGS_URL = reverse("borrowings:borrowing-list-create")


def sample_book(**params):
    defaults = {
        "title": "Sample book",
        "author": "Sample author",
        "cover": "HARD",
        "inventory": 10,
        "daily_fee": 1.00,
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


def sample_borrowing(user=None, book=None, **params):
    if user is None:
        user = create_user(email="borrower@test.com", password="borrowpass")
    if book is None:
        book = sample_book(title="Borrowed Book")

    defaults = {
        "borrow_date": date.today(),
        "expected_return_date": date.today() + timedelta(days=14),
        "actual_return_date": None,
        "book": book,
        "user": user,
    }
    defaults.update(params)

    return Borrowing.objects.create(**defaults)


def detail_url(borrowing_id):
    return reverse("borrowings:borrowing-detail", args=[borrowing_id])


class UnauthenticatedBorrowingApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.book = sample_book()

        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpassword"
        )

        self.borrowing = sample_borrowing()

    def test_list_borrowing_unauthorized(self) -> None:
        res = self.client.get(BORROWINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_unauthorized(self) -> None:
        payload = {
            "borrow_date": date.today(),
            "expected_return_date": date.today() + timedelta(days=14),
            "book": self.book.id,
            "user": self.user.id,
        }

        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_return_borrowing_unauthorized(self) -> None:
        url = reverse("borrowings:borrowing-return", args=[self.borrowing.id])

        res = self.client.patch(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_borrowing_unauthorized(self) -> None:
        url = reverse("borrowings:borrowing-return", args=[self.borrowing.id])

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test12345"
        )
        self.client.force_authenticate(self.user)

        self.book1 = sample_book(title="Test Title1", inventory=1)
        self.book2 = sample_book(title="Test Title2", inventory=2)

        self.user1 = get_user_model().objects.create_user(
            email="test1@test.com",
            password="tespass12345"
        )

        self.borrowing = Borrowing.objects.create(
            expected_return_date="2025-09-24",
            book=self.book1, user=self.user
        )

        self.borrowing1 = sample_borrowing(
            expected_return_date="2025-08-29",
            user=self.user1, book=self.book1
        )
        self.borrowing2 = sample_borrowing(
            expected_return_date="2025-08-30",
            user=self.user, book=self.book2
        )

    def test_str_borrowing(self) -> None:
        borrowing = Borrowing.objects.get(id=1)

        self.assertEqual(
            str(borrowing),
            f"{self.user.first_name} {self.user.last_name} "
            f"borrows {self.book1.title} till {borrowing.expected_return_date}"
        )

    def test_list_borrowings_signined_user(self) -> None:
        res = self.client.get(BORROWINGS_URL)

        borrowings = Borrowing.objects.filter(user=self.user.id)
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_borrowings_filtering_active_status(self) -> None:
        payload = {"actual_return_date": "2025-08-31"}
        url = reverse("borrowings:borrowing-return", args=[self.borrowing.id])
        patch_res = self.client.patch(url, payload)
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)

        self.borrowing.refresh_from_db()
        self.assertIsNotNone(self.borrowing.actual_return_date)

        res = self.client.get(BORROWINGS_URL, {"is_active": True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        filtered_qs = BorrowingFilter(
            {"is_active": True},
            queryset=Borrowing.objects.filter(user=self.user)
        ).qs

        serializer = BorrowingListSerializer(filtered_qs, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_list_borrowings_filtering_inactive_status(self) -> None:
        payload = {"actual_return_date": "2025-08-31"}
        url = reverse("borrowings:borrowing-return", args=[self.borrowing.id])
        patch_res = self.client.patch(url, payload)
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)

        self.borrowing.refresh_from_db()
        self.assertIsNotNone(self.borrowing.actual_return_date)

        res = self.client.get(BORROWINGS_URL, {"is_active": False})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        filtered_qs = BorrowingFilter(
            {"is_active": False},
            queryset=Borrowing.objects.filter(user=self.user)
        ).qs

        serializer = BorrowingListSerializer(filtered_qs, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_borrowing_retrieve(self) -> None:
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])
        res = self.client.get(url)

        serializer = BorrowingDetailSerializer(self.borrowing)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_borrowing_another_user_not_allowed(self) -> None:
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing1.id])
        res = self.client.get(url)

        self.assertNotEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    @patch("telegram.Bot.send_message", new_callable=AsyncMock)
    def test_create_borrowing_triggers_telegram(self, mock_send_message) -> None:
        payload = {
            "expected_return_date": "2025-09-30",
            "book": self.book1.id,
        }
        res = self.client.post(BORROWINGS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        borrowing = Borrowing.objects.get(pk=res.data["id"])
        self.assertEqual(borrowing.book.id, payload["book"])
        self.assertEqual(borrowing.user.id, self.user.id)

        expected_date = datetime.strptime(
            payload["expected_return_date"], "%Y-%m-%d"
        ).date()
        self.assertEqual(borrowing.expected_return_date, expected_date)

        self.assertEqual(mock_send_message.await_count, 1)

        kwargs = mock_send_message.call_args.kwargs

        self.assertIn(borrowing.book.title, kwargs["text"])
        self.assertIn(str(borrowing.expected_return_date), kwargs["text"])
        self.assertIn(self.user.email, kwargs["text"])

    @patch("telegram.Bot.send_message", new_callable=AsyncMock)
    def test_check_book_inventory_after_create_borrowing(
            self, mock_send_message
    ) -> None:
        payload = {
            "expected_return_date": "2025-09-30",
            "book": self.book1.id,
        }

        res = self.client.post(BORROWINGS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.book1.refresh_from_db()
        self.assertEqual(
            self.book1.inventory,
            0,
            msg="The book inventory should decrease after borrowing."
        )

        mock_send_message.assert_called_once()
        kwargs = mock_send_message.call_args.kwargs
        self.assertEqual(kwargs["chat_id"], settings.TELEGRAM_CHAT_ID)
        self.assertIn(self.book1.title, kwargs["text"])

    @patch("telegram.Bot.send_message", new_callable=AsyncMock)
    def test_check_book_out_of_stock(self, mock_send_message) -> None:
        payload = {
            "expected_return_date": "2025-09-30",
            "book": self.book1.id,
        }
        payload1 = {
            "expected_return_date": "2025-09-20",
            "book": self.book1.id,
        }
        self.client.post(BORROWINGS_URL, payload)
        self.book1.refresh_from_db()

        res = self.client.post(BORROWINGS_URL, payload1)
        self.book1.refresh_from_db()
        response_content = res.content.decode("utf-8")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = json.loads(response_content)
        expected_message = "The book is out of stock."
        self.assertEqual(response_data, [expected_message])

        mock_send_message.assert_called_once()

    def test_create_borrowing_with_expected_return_date_past(self) -> None:
        payload = {
            "expected_return_date": "2025-06-13",
            "book": self.book1.id,
        }
        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_borrowing(self) -> None:
        url = reverse("borrowings:borrowing-return", args=[self.borrowing.id])
        self.borrowing.borrow_date = date(2025, 8, 1)
        self.borrowing.save()

        payload = {
            "actual_return_date": str(self.borrowing.borrow_date + timedelta(days=1)),
        }

        res = self.client.patch(url, payload)
        self.borrowing.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_return_borrowing_with_past_date(self) -> None:
        url = reverse("borrowings:borrowing-return", args=[self.borrowing.id])

        self.borrowing.borrow_date = date(2025, 7, 30)
        self.borrowing.save()

        payload = {
            "actual_return_date": "2025-07-29",
        }
        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("actual_return_date", response.data)
        self.assertTrue(
            any("Actual return date cannot be earlier than borrow date."
                in str(error) for error in
                response.data["actual_return_date"])
        )


class AdminUserBorrowingTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "Testpass12345", is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.book1 = Book.objects.create(
            title="Test Title1",
            author="Test Author1",
            cover="Hard",
            inventory=1,
            daily_fee=1
        )

        self.book2 = Book.objects.create(
            title="Test Title2",
            author="Test Author2",
            cover="Hard",
            inventory=2,
            daily_fee=2
        )

        self.user1 = get_user_model().objects.create_user(
            email="test1@test.com",
            password="test123567@"
        )

        self.borrowing = Borrowing.objects.create(
            expected_return_date="2025-09-24",
            book=self.book1,
            user=self.user
        )

        self.borrowing1 = Borrowing.objects.create(
            expected_return_date="2025-09-25",
            book=self.book1,
            user=self.user1
        )

        self.borrowing2 = Borrowing.objects.create(
            expected_return_date="2025-09-26",
            book=self.book2,
            user=self.user
        )

    def test_list_borrowings_of_all_users(self) -> None:
        res = self.client.get(BORROWINGS_URL)
        borrowings = Borrowing.objects.all()
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_borrowings_filtering_is_active_status(self) -> None:
        payload = {"actual_return_date": "2025-09-16"}
        url = reverse("borrowings:borrowing-return", args=[self.borrowing.id])
        self.client.patch(url, payload)

        res = self.client.get(BORROWINGS_URL, {"is_active": True})
        borrowings = Borrowing.objects.filter(actual_return_date__isnull=True)
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_borrowings_filtering_by_user_id(self) -> None:
        res = self.client.get(BORROWINGS_URL, {"user_id": self.user1.id})
        borrowings = Borrowing.objects.filter(user__id=self.user1.id)
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
