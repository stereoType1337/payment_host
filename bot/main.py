import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import config
from bot.db import close_db, init_db
from bot.handlers import callbacks, servers, settings, start
from bot.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(servers.router)
    dp.include_router(callbacks.router)
    dp.include_router(settings.router)

    await init_db()
    logger.info("Database connected")

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
