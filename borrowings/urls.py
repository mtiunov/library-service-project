from django.urls import path
from borrowings.views import BorrowingListView


app_name = "borrowings"

urlpatterns = [
    path("borrowings/", BorrowingListView.as_view(), name="borrowing-list"),
]
