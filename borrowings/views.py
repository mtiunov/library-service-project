from rest_framework import generics
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer


class BorrowingListView(generics.ListAPIView):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingListSerializer
