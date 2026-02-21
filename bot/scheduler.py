import calendar
import datetime
import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import models
from bot.notifications import send_notification, send_problem_reminder

logger = logging.getLogger(__name__)


async def generate_monthly_payments() -> None:
    today = datetime.date.today()
    servers = await models.list_servers(active_only=True)
    last_day = calendar.monthrange(today.year, today.month)[1]

    for s in servers:
        pay_day = min(s["payment_day"], last_day)
        due_date = today.replace(day=pay_day)
        await models.ensure_payment(s["id"], due_date)


async def check_and_notify(bot: Bot) -> None:
    today = datetime.date.today()

    await generate_monthly_payments()

    payments = await models.get_pending_notifications()

    for p in payments:
        days_left = (p["due_date"] - today).days

        if days_left == 3 and not p["notified_3d"]:
            await send_notification(bot, p, days_left=3)
            await models.set_notified(p["id"], days=3)

        elif days_left <= 1 and not p["notified_1d"]:
            await send_notification(bot, p, days_left=1)
            await models.set_notified(p["id"], days=1)

    logger.info("Daily payment check completed")


async def check_problems(bot: Bot) -> None:
    pool = models.get_pool()
    rows = await pool.fetch(
        """
        SELECT p.*, s.hoster, s.server_name, s.monthly_cost, s.currency, s.payment_type
        FROM payments p
        JOIN servers s ON s.id = p.server_id
        WHERE p.status = 'problem' AND s.is_active = TRUE
        """
    )
    for row in rows:
        await send_problem_reminder(bot, dict(row))


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    scheduler.add_job(
        check_and_notify,
        "cron",
        hour=9,
        minute=0,
        kwargs={"bot": bot},
        id="daily_check",
        replace_existing=True,
    )

    scheduler.add_job(
        check_problems,
        "interval",
        hours=12,
        kwargs={"bot": bot},
        id="problem_reminder",
        replace_existing=True,
    )

    return scheduler
