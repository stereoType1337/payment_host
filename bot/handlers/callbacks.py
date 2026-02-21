from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import models
from bot.keyboards.inline import confirm_delete_kb, server_actions_kb, server_list_kb

router = Router()

CURRENCY_SYMBOLS = {"RUB": "₽", "USD": "$", "EUR": "€"}


def _format_cost(amount, currency: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency in ("USD", "EUR"):
        return f"{symbol}{amount}"
    return f"{amount} {symbol}"


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
        cost_str = f"Стоимость: {_format_cost(server['monthly_cost'], server['currency'])}\n"

    ptype_label = "Инвойс" if server["payment_type"] == "invoice" else "Автосписание"
    await callback.message.edit_text(
        f"Хостер: {server['hoster']}\n"
        f"Сервер: {server['server_name']}\n"
        f"День оплаты: {server['payment_day']}\n"
        f"Тип: {ptype_label}\n"
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
    deleted = await models.delete_server(server_id)
    if deleted:
        await callback.answer("Сервер удалён", show_alert=True)
    else:
        await callback.answer("Сервер не найден", show_alert=True)
    servers = await models.list_servers()
    if servers:
        await callback.message.edit_text("Ваши серверы:", reply_markup=server_list_kb(servers))
    else:
        await callback.message.edit_text("Список серверов пуст.")


# ── Back to list ─────────────────────────────────────────

@router.callback_query(F.data == "srv_back")
async def cb_back(callback: CallbackQuery):
    servers = await models.list_servers()
    if servers:
        await callback.message.edit_text("Ваши серверы:", reply_markup=server_list_kb(servers))
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
