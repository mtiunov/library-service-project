from django.urls import path
from borrowings.views import (
    BorrowingListView,
    BorrowingRetrieveView,
    BorrowingReturnView,
)


app_name = "borrowings"

urlpatterns = [
    path("borrowings/", BorrowingListView.as_view(), name="borrowing-list-create"),
    path("borrowings/<int:pk>", BorrowingRetrieveView.as_view(), name="borrowing-detail"),
    path("borrowings/<int:pk>/return/", BorrowingReturnView.as_view(), name="borrowing-return"),
]
