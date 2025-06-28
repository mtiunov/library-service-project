from rest_framework import generics
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer, BorrowingDetailSerializer


class BorrowingListView(generics.ListAPIView):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingListSerializer


class BorrowingRetrieveView(generics.RetrieveAPIView):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingDetailSerializer
