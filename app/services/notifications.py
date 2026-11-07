from telegram import Bot

from app.models.models import RankedJob
from app.utils.settings import settings


def format_job_alert(job: RankedJob) -> str:
    """Format a ranked job into a clear, scannable Telegram Markdown alert."""
    budget_line = "Thương lượng"
    curr = job.currency or "$"
    if job.budget_min is not None and job.budget_max is not None:
        budget_line = f"{curr}{job.budget_min:,.0f} - {curr}{job.budget_max:,.0f}"
    elif job.budget_max is not None:
        budget_line = f"Tối đa {curr}{job.budget_max:,.0f}"
    elif job.budget_min is not None:
        budget_line = f"Tối thiểu {curr}{job.budget_min:,.0f}"

    matched = ", ".join(job.matched_skills) if job.matched_skills else "Không"
    missing = ", ".join(job.missing_skills) if job.missing_skills else "Không"
    url_line = f"\n🔗 [Xem job trên Upwork]({job.url})" if job.url else ""

    return (
        f"🎯 *[Freelance Job Fit Radar]* Phát hiện Job mới!\n\n"
        f"📌 *Tiêu đề:* `{job.title}`\n"
        f"⭐ *Độ phù hợp:* `{job.fit_score}%`\n"
        f"💰 *Ngân sách:* {budget_line}\n"
        f"✅ *Kỹ năng khớp:* `{matched}`\n"
        f"⚠️ *Kỹ năng thiếu:* `{missing}`"
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

