from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from borrowings.filters import BorrowingFilter

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    CreateBorrowingSerializer,
    BorrowingReturnSerializer,
)


class BorrowingListView(generics.ListCreateAPIView):
    serializer_class = BorrowingListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BorrowingFilter

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


class BorrowingReturnView(generics.UpdateAPIView):
    queryset = Borrowing.objects.select_related("book", "user")
    permission_classes = [IsAuthenticated]
    serializer_class = BorrowingReturnSerializer

    def update(self, request, *args, **kwargs) -> Response:
        instance = self.get_object()

        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to return this borrowing."},
                status=status.HTTP_403_FORBIDDEN
            )

        if instance.actual_return_date:
            return Response({"detail": "This borrowing has already been returned."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            serializer.save()

            instance.book.inventory += 1
            instance.book.save()

        return Response({"detail": "Borrowing returned successfully."},
                        status=status.HTTP_200_OK)
