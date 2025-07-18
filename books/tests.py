from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient
from books.models import Book
from books.serializers import BookSerializer
from decimal import Decimal

BOOK_URL = reverse("books:book-list")


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


def detail_url(book_id):
    return reverse("books:book-detail", args=[book_id])


class UnauthenticatedBookApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BOOK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_book_str_representation(self):
        book = sample_book()

        expected_str = "Sample book by Sample author"

        self.assertEqual(str(book), expected_str)

    def test_list_books(self):
        sample_book()
        sample_book()

        res = self.client.get(BOOK_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retriewe_book_detail(self):
        book = sample_book()

        url = detail_url(book.id)
        res = self.client.get(url)

        serializer = BookSerializer(book)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_book_unauthorized(self):
        payload = {
            "title": "Book A",
            "author": "Alice",
            "cover": "HARD",
            "inventory": 5,
            "daily_fee": 2.00,
        }
        res = self.client.post(BOOK_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBookApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_create_book_forbidden(self) -> None:
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "HARD",
            "inventory": 2,
            "daily_fee": 2.5,
        }
        res = self.client.post(BOOK_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_book_delete_forbidden(self) -> None:
        book = sample_book()

        url = detail_url(book.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_book(self):
        payload = {
            "title": "New Book 2",
            "author": "New Author 2",
            "cover": "HARD",
            "inventory": 20,
            "daily_fee": 2,
        }
        res = self.client.post(BOOK_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        book = Book.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(book, key))

    def test_patch_update_book(self):
        payload = {
            "title": "New Book 3",
            "author": "New Author 3",
            "cover": "HARD",
            "inventory": 20,
            "daily_fee": 2.0,
        }
        book = sample_book()
        url = detail_url(book.id)
        res = self.client.patch(url, payload)

        book = Book.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(book, key))

    def test_put_update_book(self):
        book = sample_book()

        payload = {
            "title": "Updated Title",
            "author": "Updated Author",
            "cover": "HARD",
            "inventory": 10,
            "daily_fee": 2.00,
        }

        url = detail_url(book.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        book.refresh_from_db()
        self.assertEqual(book.title, payload["title"])
        self.assertEqual(book.author, payload["author"])
        self.assertEqual(book.cover, payload["cover"])
        self.assertEqual(book.inventory, payload["inventory"])
        self.assertEqual(book.daily_fee, Decimal(str(payload["daily_fee"])))

    def test_book_delete(self):
        book = sample_book()
        url = detail_url(book.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
