from django.contrib import admin

from books.models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "inventory", "daily_fee", "cover")
    list_filter = ("cover",)
    search_fields = ("title", "author")

