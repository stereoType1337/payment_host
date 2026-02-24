from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import models
from bot.keyboards.inline import (
    confirm_delete_kb,
    hoster_list_kb,
    hoster_servers_kb,
    server_actions_kb,
)

router = Router()

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


# ── Hoster list ───────────────────────────────────────────

@router.callback_query(F.data.startswith("hstr:"))
async def cb_hoster_servers(callback: CallbackQuery):
    hoster = callback.data[5:]  # everything after "hstr:"
    servers = await models.list_servers_by_hoster(hoster)
    if not servers:
        await callback.answer("Нет серверов у этого хостера", show_alert=True)
        return
    await callback.message.edit_text(
        f"Серверы хостера {hoster}:",
        reply_markup=hoster_servers_kb(servers),
    )
    await callback.answer()


# ── Server info ──────────────────────────────────────────

@router.callback_query(F.data.startswith("srv_info:"))
async def cb_server_info(callback: CallbackQuery):
    server_id = int(callback.data.split(":")[1])
    server = await models.get_server(server_id)
    if not server:
        await callback.answer("Сервер не найден", show_alert=True)
        return

    cost_str = ""
    if server["monthly_cost"] is not None:
        cost_str = f"Стоимость: {_format_cost(server['monthly_cost'], server['currency'], server.get('count', 1))}\n"

    count = server.get("count", 1)
    count_str = f"Кол-во: {count}\n" if count > 1 else ""
    ptype_label = "Инвойс" if server["payment_type"] == "invoice" else "Автосписание"
    await callback.message.edit_text(
        f"Хостер: {server['hoster']}\n"
        f"Сервер: {server['server_name']}\n"
        f"День оплаты: {server['payment_day']}\n"
        f"Тип: {ptype_label}\n"
        f"{count_str}"
        f"{cost_str}",
        reply_markup=server_actions_kb(server_id),
    )
    await callback.answer()


# ── Delete server ────────────────────────────────────────

@router.callback_query(F.data.startswith("srv_del:"))
async def cb_server_delete_confirm(callback: CallbackQuery):
    server_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "Вы уверены, что хотите удалить этот сервер?",
        reply_markup=confirm_delete_kb(server_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("srv_del_yes:"))
async def cb_server_delete(callback: CallbackQuery):
    server_id = int(callback.data.split(":")[1])
    server = await models.get_server(server_id)
    hoster = server["hoster"] if server else None

    deleted = await models.delete_server(server_id)
    if deleted:
        await callback.answer("Сервер удалён", show_alert=True)
    else:
        await callback.answer("Сервер не найден", show_alert=True)

    # Try to return to the hoster's server list; fall back to hosters list
    if hoster:
        servers = await models.list_servers_by_hoster(hoster)
        if servers:
            await callback.message.edit_text(
                f"Серверы хостера {hoster}:",
                reply_markup=hoster_servers_kb(servers),
            )
            return

    hosters = await models.list_hosters()
    if hosters:
        await callback.message.edit_text("Ваши хостеры:", reply_markup=hoster_list_kb(hosters))
    else:
        await callback.message.edit_text("Список серверов пуст.")


# ── Navigation ────────────────────────────────────────────

@router.callback_query(F.data == "srv_back_list")
async def cb_back_list(callback: CallbackQuery):
    hosters = await models.list_hosters()
    if hosters:
        await callback.message.edit_text("Ваши хостеры:", reply_markup=hoster_list_kb(hosters))
    else:
        await callback.message.edit_text("Список серверов пуст.")
    await callback.answer()


@router.callback_query(F.data.startswith("srv_back_hstr:"))
async def cb_back_hoster(callback: CallbackQuery):
    server_id = int(callback.data.split(":")[1])
    server = await models.get_server(server_id)
    if server:
        hoster = server["hoster"]
        servers = await models.list_servers_by_hoster(hoster)
        if servers:
            await callback.message.edit_text(
                f"Серверы хостера {hoster}:",
                reply_markup=hoster_servers_kb(servers),
            )
            await callback.answer()
            return
    # Fall back to hosters list
    hosters = await models.list_hosters()
    if hosters:
        await callback.message.edit_text("Ваши хостеры:", reply_markup=hoster_list_kb(hosters))
    else:
        await callback.message.edit_text("Список серверов пуст.")
    await callback.answer()


# ── Payment callbacks ────────────────────────────────────

@router.callback_query(F.data.startswith("pay_done:"))
async def cb_pay_done(callback: CallbackQuery):
    payment_id = int(callback.data.split(":")[1])
    payment = await models.mark_payment(payment_id, "paid")
    if payment:
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ Отмечено как оплаченное."
        )
    await callback.answer("Оплата отмечена!")


@router.callback_query(F.data.startswith("pay_ok:"))
async def cb_pay_ok(callback: CallbackQuery):
    payment_id = int(callback.data.split(":")[1])
    payment = await models.mark_payment(payment_id, "confirmed")
    if payment:
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ Списание подтверждено."
        )
    await callback.answer("Списание подтверждено!")


@router.callback_query(F.data.startswith("pay_problem:"))
async def cb_pay_problem(callback: CallbackQuery):
    payment_id = int(callback.data.split(":")[1])
    payment = await models.mark_payment(payment_id, "problem")
    if payment:
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ Отмечена проблема. Напомню через 12 часов."
        )
    await callback.answer("Проблема зафиксирована")
