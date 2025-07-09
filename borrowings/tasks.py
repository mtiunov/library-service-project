from celery import shared_task
from django.utils.timezone import now
from borrowings.models import Borrowing
from borrowings.telegram import send_telegram_message
from asgiref.sync import async_to_sync


@shared_task
def notify_overdue_borrowings():
    today = now().date()
    borrowings = Borrowing.objects.filter(
        expected_return_date__lt=today,
        actual_return_date__isnull=True
    ).select_related("book", "user")

    if not borrowings.exists():
        message = "No overdue borrowing today!"
        async_to_sync(send_telegram_message)(message)
        return

    for borrowing in borrowings:
        message = (
            f"⚠️ <b>Delay!</b>\n"
            f"👤 <b>User:</b> {borrowing.user.email}\n"
            f"📖 <b>Book:</b> {borrowing.book.title}\n"
            f"📅 <b>Borrow date:</b> {borrowing.borrow_date}\n"
            f"📆 <b>Expected return:</b> {borrowing.expected_return_date}"
        )
        async_to_sync(send_telegram_message)(message)
