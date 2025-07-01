from rest_framework import serializers
from borrowings.models import Borrowing
from books.serializers import BookSerializer


class BorrowingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer(many=False, read_only=True)
    user = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class CreateBorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "borrow_date",
            "expected_return_date",
            "book",
        )

    def create(self, validated_data):
        book = validated_data["book"]
        if book.inventory == 0:
            raise serializers.ValidationError("The book is out of stock.")

        book.inventory -= 1
        book.save()

        user = self.context["request"].user
        borrowing = Borrowing.objects.create(user=user, **validated_data)

        return borrowing


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("actual_return_date",)
