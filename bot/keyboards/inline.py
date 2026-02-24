from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def hoster_list_kb(hosters: list[dict]) -> InlineKeyboardMarkup:
    """Top-level list: one button per hoster with server count."""
    buttons = []
    for h in hosters:
        n = h["count"]
        label = f"{h['hoster']}  ({n} серв.)"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"hstr:{h['hoster']}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def hoster_servers_kb(servers: list[dict]) -> InlineKeyboardMarkup:
    """Servers inside a hoster + back button."""
    buttons = []
    for s in servers:
        label = s["server_name"]
        if s.get("count", 1) > 1:
            label += f" ×{s['count']}"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"srv_info:{s['id']}"),
        ])
    buttons.append([
        InlineKeyboardButton(text="« Назад", callback_data="srv_back_list"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def hoster_select_kb(hosters: list[str]) -> InlineKeyboardMarkup:
    """Used in /add flow: pick existing hoster or create new."""
    buttons = []
    for h in hosters:
        buttons.append([
            InlineKeyboardButton(text=h, callback_data=f"addh:{h}"),
        ])
    buttons.append([
        InlineKeyboardButton(text="+ Новый хостер", callback_data="addh:__new__"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def server_actions_kb(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Удалить", callback_data=f"srv_del:{server_id}"),
        ],
        [
            InlineKeyboardButton(text="« Назад", callback_data=f"srv_back_hstr:{server_id}"),
        ],
    ])


def confirm_delete_kb(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да, удалить", callback_data=f"srv_del_yes:{server_id}"),
            InlineKeyboardButton(text="Отмена", callback_data=f"srv_back_hstr:{server_id}"),
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
