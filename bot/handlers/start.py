from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот для отслеживания оплаты серверов.\n\n"
        "Команды:\n"
        "/add — добавить сервер\n"
        "/list — список серверов\n"
        "/upcoming — ближайшие оплаты\n"
        "/setchat — привязать чат для уведомлений\n"
        "/cancel — отменить текущее действие"
    )
