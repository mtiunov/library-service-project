from datetime import date

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField(null=True, blank=True)
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="borrowings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="borrowings"
    )

    class Meta:
        ordering = ["borrow_date"]

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name} borrows " \
               f"{self.book.title} till {self.expected_return_date}"

    def clean(self):
        if self.expected_return_date and self.expected_return_date < self.borrow_date:
            raise ValidationError(
                {"expected_return_date": "Expected return date cannot "
                                         "be earlier than borrow date."}
            )
        if self.actual_return_date and self.actual_return_date < self.borrow_date:
            raise ValidationError(
                {"actual_return_date": "Actual return date cannot "
                                       "be earlier than borrow date."}
            )

    def save(self, *args, **kwargs):
        if not self.borrow_date:
            self.borrow_date = date.today()
        self.full_clean()
        super().save(*args, **kwargs)
