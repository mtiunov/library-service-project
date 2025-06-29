from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    CreateBorrowingSerializer,
)


class BorrowingListView(generics.ListCreateAPIView):
    serializer_class = BorrowingListSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateBorrowingSerializer
        if self.request.method == "GET":
            return BorrowingListSerializer

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book", "user")

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset


class BorrowingRetrieveView(generics.RetrieveAPIView):
    serializer_class = BorrowingDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book", "user")
        if self.request.user.is_staff:
            return queryset
        else:
            return Borrowing.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj
