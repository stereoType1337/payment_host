from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def server_list_kb(servers: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for s in servers:
        buttons.append([
            InlineKeyboardButton(
                text=f"{s['hoster']} — {s['server_name']}",
                callback_data=f"srv_info:{s['id']}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def server_actions_kb(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Удалить", callback_data=f"srv_del:{server_id}"),
        ],
        [
            InlineKeyboardButton(text="« Назад", callback_data="srv_back"),
        ],
    ])


def confirm_delete_kb(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да, удалить", callback_data=f"srv_del_yes:{server_id}"),
            InlineKeyboardButton(text="Отмена", callback_data="srv_back"),
        ],
    ])


def payment_invoice_kb(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплачено ✓", callback_data=f"pay_done:{payment_id}")],
    ])


def payment_auto_kb(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Списание прошло ✓", callback_data=f"pay_ok:{payment_id}"),
            InlineKeyboardButton(text="Проблема ✗", callback_data=f"pay_problem:{payment_id}"),
        ],
    ])


def payment_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Инвойс (invoice)", callback_data="ptype:invoice"),
            InlineKeyboardButton(text="Автосписание (auto)", callback_data="ptype:auto"),
        ],
    ])


def currency_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="RUB ₽", callback_data="cur:RUB"),
            InlineKeyboardButton(text="USD $", callback_data="cur:USD"),
            InlineKeyboardButton(text="EUR €", callback_data="cur:EUR"),
        ],
    ])
