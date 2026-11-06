import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from telegram import Bot

# Load biến môi trường từ .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


async def main():
    print("=" * 50)
    print("CHECKING TELEGRAM BOT CONFIGURATION")
    print("=" * 50)

    if not TELEGRAM_BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN is not configured in .env!")
        print("Please create a bot with @BotFather and paste the token into the .env file")
        sys.exit(1)

    if not TELEGRAM_CHAT_ID:
        print("[ERROR] TELEGRAM_CHAT_ID is not configured in .env!")
        print("Please get the chat_id (via @userinfobot or /start) and paste it into the .env file")
        sys.exit(1)

    try:
        chat_id_int = int(TELEGRAM_CHAT_ID)
    except ValueError:
        print(f"[ERROR] TELEGRAM_CHAT_ID must be an integer (received: {TELEGRAM_CHAT_ID})")
        sys.exit(1)

    print(f"-> Bot Token: {TELEGRAM_BOT_TOKEN[:6]}...{TELEGRAM_BOT_TOKEN[-4:]}")
    print(f"-> Chat ID:   {chat_id_int}")
    print("\nChecking connection to Telegram API and sending test message...")

    message = (
        "🚀 *[Freelance Job Fit Radar]* Test Alert\n\n"
        "✅ *Bot connected successfully!*\n"
        "📍 System is ready to receive and analyze jobs from Upwork.\n\n"
        "📊 *Sample Job:* `FastAPI Backend Developer`\n"
        "🎯 *Fit Score:* `85/100`\n"
        "💡 *Reason:* Matched `[Python, FastAPI, Telegram]`\n"
        "💰 *Budget:* `$300 - $500`\n"
    )

    try:
        async with Bot(token=TELEGRAM_BOT_TOKEN) as bot:
            me = await bot.get_me()
            print(f"-> Authentication success: Bot @{me.username} ({me.first_name})")
            sent_msg = await bot.send_message(
                chat_id=chat_id_int,
                text=message,
                parse_mode="Markdown"
            )
            print(f"-> [SUCCESS] Message sent (Message ID: {sent_msg.message_id})")
            print("Check the Telegram app on your phone/computer!")
    except Exception as e:
        print(f"\n[ERROR WHEN SENDING MESSAGE]: {e}")
        print("\nSome common reasons:")
        print("1. Token sai hoặc hết hạn.")
        print("2. Bạn chưa bấm '/start' vào bot nên bot chưa có quyền gửi tin cho bạn.")
        print("3. Chat ID bị sai.")


if __name__ == "__main__":
    asyncio.run(main())
