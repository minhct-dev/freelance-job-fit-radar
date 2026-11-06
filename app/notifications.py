from telegram import Bot

from app.settings import settings


async def send_job_alert(text: str) -> None:
    """Send one alert when Telegram credentials are configured."""
    if not settings.telegram_bot_token or settings.telegram_chat_id is None:
        raise RuntimeError("Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first")

    async with Bot(settings.telegram_bot_token) as bot:
        await bot.send_message(chat_id=settings.telegram_chat_id, text=text)
