import datetime

from aiogram import Bot

from bot import models
from bot.keyboards.inline import payment_auto_kb, payment_invoice_kb

CURRENCY_SYMBOLS = {"RUB": "₽", "USD": "$", "EUR": "€"}


def _format_cost(amount, currency: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency in ("USD", "EUR"):
        return f"{symbol}{amount}"
    return f"{amount} {symbol}"


async def send_notification(bot: Bot, payment: dict, days_left: int) -> None:
    chat_id = await models.get_setting("notify_chat_id")
    if not chat_id:
        return

    ptype = payment["payment_type"]
    cost_str = _format_cost(payment["monthly_cost"], payment["currency"]) if payment["monthly_cost"] else "—"
    date_str = payment["due_date"].strftime("%d.%m.%Y")

    if ptype == "invoice":
        if days_left == 3:
            header = "⚠️ Оплата через 3 дня"
        else:
            header = "🔴 Оплата завтра!"
        ptype_label = "Инвойс"
        kb = payment_invoice_kb(payment["id"])
    else:
        if days_left == 3:
            header = "ℹ️ Автосписание через 3 дня"
            ptype_label = "Автосписание"
            kb = None
        else:
            header = "ℹ️ Автосписание завтра"
            ptype_label = "Автосписание"
            kb = payment_auto_kb(payment["id"])

    text = (
        f"{header}\n\n"
        f"Хостер: {payment['hoster']}\n"
        f"Сервер: {payment['server_name']}\n"
        f"Сумма: {cost_str}\n"
        f"Тип: {ptype_label}\n"
        f"Дата: {date_str}"
    )

    await bot.send_message(chat_id=int(chat_id), text=text, reply_markup=kb)


async def send_problem_reminder(bot: Bot, payment: dict) -> None:
    chat_id = await models.get_setting("notify_chat_id")
    if not chat_id:
        return

    cost_str = _format_cost(payment["monthly_cost"], payment["currency"]) if payment["monthly_cost"] else "—"
    date_str = payment["due_date"].strftime("%d.%m.%Y")

    text = (
        f"🔁 Напоминание: проблема с оплатой\n\n"
        f"Хостер: {payment['hoster']}\n"
        f"Сервер: {payment['server_name']}\n"
        f"Сумма: {cost_str}\n"
        f"Дата: {date_str}"
    )

    kb = payment_auto_kb(payment["id"])
    await bot.send_message(chat_id=int(chat_id), text=text, reply_markup=kb)
