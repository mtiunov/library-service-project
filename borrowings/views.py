from rest_framework import generics
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    CreateBorrowingSerializer,
)


class BorrowingListView(generics.ListCreateAPIView):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingListSerializer

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateBorrowingSerializer
        if self.request.method == "LIST":
            return BorrowingListSerializer


class BorrowingRetrieveView(generics.RetrieveAPIView):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingDetailSerializer
