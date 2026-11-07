from telegram import Bot

from app.models.models import RankedJob
from app.utils.settings import settings


def format_job_alert(job: RankedJob) -> str:
    """Format a ranked job into a clear, scannable Telegram Markdown alert."""
    price_line = "Negotiable"
    if job.fixed_price:
        price_line = f"Fixed: ${job.fixed_price:,.0f}"
    elif job.hourly_price:
        price_line = f"Hourly: ${job.hourly_price:,.0f}/hr"

    skills = ", ".join(job.skill_and_expertise) if job.skill_and_expertise else "N/A"
    matched = ", ".join(job.matched_skills) if job.matched_skills else "None"
    missing = ", ".join(job.missing_skills) if job.missing_skills else "None"
    url_line = f"\n🔗 [View job on Upwork]({job.url})" if job.url else ""

    return (
        f"🎯 *[Freelance Job Fit Radar]* New Job Found!\n\n"
        f"📌 *Title:* `{job.title}`\n"
        f"⭐ *Client Rating:* {job.client_evaluate} stars ({job.client_review} reviews)\n"
        f"⭐ *Fit Score:* `{job.fit_score}%`\n"
        f"💰 *Budget:* {price_line}\n"
        f"🛠 *Skills:* `{skills}`\n"
        f"✅ *Matched Skills:* `{matched}`\n"
        f"⚠️ *Missing Skills:* `{missing}`"
        f"{url_line}"
    )


async def send_job_alert(text: str) -> None:
    """Send one alert when Telegram credentials are configured."""
    if not settings.telegram_bot_token or settings.telegram_chat_id is None:
        raise RuntimeError("Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first")

    async with Bot(settings.telegram_bot_token) as bot:
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=text,
            parse_mode="Markdown",
        )
