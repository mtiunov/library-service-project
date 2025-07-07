from telegram import Bot
from django.conf import settings

bot = Bot(token=settings.TELEGRAM_API_KEY)


async def send_telegram_message(text: str) -> None:
    await bot.send_message(
        chat_id=settings.TELEGRAM_CHAT_ID,
        text=text,
        parse_mode="HTML"
    )
