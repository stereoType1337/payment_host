from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot import models

router = Router()


@router.message(Command("setchat"))
async def cmd_setchat(message: Message):
    chat_id = str(message.chat.id)
    await models.set_setting("notify_chat_id", chat_id)
    await message.answer(
        f"Уведомления будут отправляться в этот чат (ID: {chat_id})."
    )
