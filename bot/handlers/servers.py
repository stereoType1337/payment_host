from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import models
from bot.keyboards.inline import (
    currency_kb,
    hoster_list_kb,
    hoster_select_kb,
    payment_type_kb,
)

router = Router()


# ── FSM States ───────────────────────────────────────────

class AddServer(StatesGroup):
    hoster_select = State()   # inline keyboard: pick existing hoster or "new"
    hoster_new = State()      # text input: type new hoster name
    server_name = State()
    payment_day = State()
    payment_type = State()
    monthly_cost = State()
    count = State()
    currency = State()


# ── Commands (registered FIRST so they aren't eaten by FSM) ──

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("Нечего отменять.")
        return
    await state.clear()
    await message.answer("Действие отменено.")


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await state.clear()
    hosters = await models.list_hosters()
    if hosters:
        await state.set_state(AddServer.hoster_select)
        hoster_names = [h["hoster"] for h in hosters]
        await message.answer(
            "Выберите хостер или создайте новый:\n\n/cancel — отменить",
            reply_markup=hoster_select_kb(hoster_names),
        )
    else:
        await state.set_state(AddServer.hoster_new)
        await message.answer("Введите название хостера (например, Hetzner):\n\n/cancel — отменить")


@router.message(Command("list"))
async def cmd_list(message: Message, state: FSMContext):
    await state.clear()
    hosters = await models.list_hosters()
    if not hosters:
        await message.answer("Список серверов пуст. Добавьте сервер командой /add")
        return
    await message.answer("Ваши хостеры:", reply_markup=hoster_list_kb(hosters))


@router.message(Command("upcoming"))
async def cmd_upcoming(message: Message, state: FSMContext):
    await state.clear()
    payments = await models.get_upcoming_payments(14)
    if not payments:
        await message.answer("Нет предстоящих оплат в ближайшие 14 дней.")
        return
    lines = []
    for p in payments:
        cost_str = _format_cost(p["monthly_cost"], p["currency"], p.get("count", 1)) if p["monthly_cost"] else "—"
        ptype_label = "Инвойс" if p["payment_type"] == "invoice" else "Авто"
        lines.append(
            f"• {p['due_date'].strftime('%d.%m.%Y')} — {p['hoster']} / {p['server_name']}\n"
            f"  {cost_str} | {ptype_label} | {p['status']}"
        )
    await message.answer("Ближайшие оплаты (14 дней):\n\n" + "\n\n".join(lines))


# ── FSM: hoster selection (callback) ─────────────────────

@router.callback_query(AddServer.hoster_select, F.data.startswith("addh:"))
async def fsm_hoster_select(callback: CallbackQuery, state: FSMContext):
    choice = callback.data[5:]  # everything after "addh:"
    if choice == "__new__":
        await state.set_state(AddServer.hoster_new)
        await callback.message.edit_text("Введите название хостера:\n\n/cancel — отменить")
    else:
        await state.update_data(hoster=choice)
        await state.set_state(AddServer.server_name)
        await callback.message.edit_text("Введите имя/описание сервера:")
    await callback.answer()


# ── FSM: text steps ───────────────────────────────────────

@router.message(AddServer.hoster_new)
async def fsm_hoster_new(message: Message, state: FSMContext):
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
    await callback.message.edit_text("Введите стоимость за единицу в месяц (число, или 0 если неизвестна):")
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
    await state.set_state(AddServer.count)
    await message.answer("Количество серверов (введите 1 если один):")


@router.message(AddServer.count)
async def fsm_count(message: Message, state: FSMContext):
    try:
        count = int(message.text.strip())
        if count < 1:
            raise ValueError
    except ValueError:
        await message.answer("Введите целое число больше 0:")
        return
    await state.update_data(count=count)
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
        count=data["count"],
    )

    cost_str = ""
    if server["monthly_cost"] is not None:
        cost_str = f"\nСтоимость: {_format_cost(server['monthly_cost'], server['currency'], server['count'])}"

    ptype_label = "Инвойс" if server["payment_type"] == "invoice" else "Автосписание"
    count_str = f"\nКол-во: {server['count']}" if server["count"] > 1 else ""
    await callback.message.edit_text(
        f"Сервер добавлен!\n\n"
        f"Хостер: {server['hoster']}\n"
        f"Сервер: {server['server_name']}\n"
        f"День оплаты: {server['payment_day']}\n"
        f"Тип: {ptype_label}"
        f"{count_str}"
        f"{cost_str}"
    )
    await callback.answer()
    await state.clear()


# ── Helpers ──────────────────────────────────────────────

CURRENCY_SYMBOLS = {"RUB": "₽", "USD": "$", "EUR": "€"}


def _format_cost(amount, currency: str, count: int = 1) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency in ("USD", "EUR"):
        unit = f"{symbol}{amount}"
    else:
        unit = f"{amount} {symbol}"
    if count > 1:
        total = amount * count
        if currency in ("USD", "EUR"):
            total_str = f"{symbol}{total}"
        else:
            total_str = f"{total} {symbol}"
        return f"{unit} ×{count} = {total_str}"
    return unit
