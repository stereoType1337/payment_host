from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import models
from bot.keyboards.inline import (
    currency_kb,
    payment_type_kb,
    server_list_kb,
)

router = Router()


# ── FSM States ───────────────────────────────────────────

class AddServer(StatesGroup):
    hoster = State()
    server_name = State()
    payment_day = State()
    payment_type = State()
    monthly_cost = State()
    currency = State()


# ── /add ─────────────────────────────────────────────────

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await state.set_state(AddServer.hoster)
    await message.answer("Введите название хостера (например, Hetzner):")


@router.message(AddServer.hoster)
async def fsm_hoster(message: Message, state: FSMContext):
    await state.update_data(hoster=message.text.strip())
    await state.set_state(AddServer.server_name)
    await message.answer("Введите имя/описание сервера:")


@router.message(AddServer.server_name)
async def fsm_server_name(message: Message, state: FSMContext):
    await state.update_data(server_name=message.text.strip())
    await state.set_state(AddServer.payment_day)
    await message.answer("Введите день оплаты (1–31):")


@router.message(AddServer.payment_day)
async def fsm_payment_day(message: Message, state: FSMContext):
    try:
        day = int(message.text.strip())
        if not 1 <= day <= 31:
            raise ValueError
    except ValueError:
        await message.answer("Введите число от 1 до 31:")
        return
    await state.update_data(payment_day=day)
    await state.set_state(AddServer.payment_type)
    await message.answer("Тип оплаты:", reply_markup=payment_type_kb())


@router.callback_query(AddServer.payment_type, F.data.startswith("ptype:"))
async def fsm_payment_type(callback: CallbackQuery, state: FSMContext):
    ptype = callback.data.split(":")[1]
    await state.update_data(payment_type=ptype)
    await state.set_state(AddServer.monthly_cost)
    await callback.message.edit_text("Введите стоимость в месяц (число, или 0 если неизвестна):")
    await callback.answer()


@router.message(AddServer.monthly_cost)
async def fsm_monthly_cost(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        cost = Decimal(text)
        if cost < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        await message.answer("Введите корректное число (например, 49.00):")
        return
    await state.update_data(monthly_cost=cost if cost > 0 else None)
    await state.set_state(AddServer.currency)
    await message.answer("Валюта:", reply_markup=currency_kb())


@router.callback_query(AddServer.currency, F.data.startswith("cur:"))
async def fsm_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split(":")[1]
    data = await state.get_data()
    data["currency"] = currency

    server = await models.add_server(
        hoster=data["hoster"],
        server_name=data["server_name"],
        payment_day=data["payment_day"],
        payment_type=data["payment_type"],
        monthly_cost=data["monthly_cost"],
        currency=data["currency"],
    )

    cost_str = ""
    if server["monthly_cost"] is not None:
        cost_str = f"\nСтоимость: {_format_cost(server['monthly_cost'], server['currency'])}"

    ptype_label = "Инвойс" if server["payment_type"] == "invoice" else "Автосписание"
    await callback.message.edit_text(
        f"Сервер добавлен!\n\n"
        f"Хостер: {server['hoster']}\n"
        f"Сервер: {server['server_name']}\n"
        f"День оплаты: {server['payment_day']}\n"
        f"Тип: {ptype_label}"
        f"{cost_str}"
    )
    await callback.answer()
    await state.clear()


# ── /list ────────────────────────────────────────────────

@router.message(Command("list"))
async def cmd_list(message: Message):
    servers = await models.list_servers()
    if not servers:
        await message.answer("Список серверов пуст. Добавьте сервер командой /add")
        return
    await message.answer("Ваши серверы:", reply_markup=server_list_kb(servers))


# ── /upcoming ────────────────────────────────────────────

@router.message(Command("upcoming"))
async def cmd_upcoming(message: Message):
    payments = await models.get_upcoming_payments(14)
    if not payments:
        await message.answer("Нет предстоящих оплат в ближайшие 14 дней.")
        return
    lines = []
    for p in payments:
        cost_str = _format_cost(p["monthly_cost"], p["currency"]) if p["monthly_cost"] else "—"
        ptype_label = "Инвойс" if p["payment_type"] == "invoice" else "Авто"
        lines.append(
            f"• {p['due_date'].strftime('%d.%m.%Y')} — {p['hoster']} / {p['server_name']}\n"
            f"  {cost_str} | {ptype_label} | {p['status']}"
        )
    await message.answer("Ближайшие оплаты (14 дней):\n\n" + "\n\n".join(lines))


# ── Helpers ──────────────────────────────────────────────

CURRENCY_SYMBOLS = {"RUB": "₽", "USD": "$", "EUR": "€"}


def _format_cost(amount, currency: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency in ("USD", "EUR"):
        return f"{symbol}{amount}"
    return f"{amount} {symbol}"
