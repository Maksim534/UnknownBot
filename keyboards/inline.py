from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Как играть", callback_data="how_to_play")],
        [InlineKeyboardButton(text="📦 Кейсы", callback_data="cases_menu"),
         InlineKeyboardButton(text="🎴 Мои карты", callback_data="my_cards")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="show_balance"),
         InlineKeyboardButton(text="💸 Доход", callback_data="claim_income")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])


def cases_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Ежедневный кейс · бесплатно", callback_data="daily_case")],
        [InlineKeyboardButton(text="📦 Обычный · 100 🪙", callback_data="normal_case")],
        [InlineKeyboardButton(text="🔴 Редкий · 8 000 🪙", callback_data="rare_case")],
        [InlineKeyboardButton(text="🟣 Мифический · 60 000 🪙", callback_data="mythic_case")],
        [InlineKeyboardButton(text="🌟 Ультра-легендарный · 2 000 000 🪙", callback_data="ultra_case")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")]
    ])


def event_cases_keyboard(events):
    kb = []
    for ev in events:
        kb.append([
            InlineKeyboardButton(
                text=f"🎉 {ev.name} · {ev.price:,} 🪙".replace(",", " "),
                callback_data=f"event_case_{ev.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton(text="🖥 Хостинг", callback_data="admin_hosting")],
        [InlineKeyboardButton(text="🎟️ Промокоды", callback_data="admin_promo"),
         InlineKeyboardButton(text="🎯 Ивенты", callback_data="admin_events")],
        [InlineKeyboardButton(text="📣 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🚪 Закрыть", callback_data="admin_exit")]
    ])


def event_management_keyboard(events):
    kb = []
    kb.append([InlineKeyboardButton(text="➕ Создать ивент", callback_data="event_create")])
    for ev in events:
        status = "🟢 Выключить" if ev.is_active else "⚫ Включить"
        kb.append([
            InlineKeyboardButton(text=f"🎯 {ev.name}", callback_data=f"view_event_{ev.id}"),
            InlineKeyboardButton(text=status, callback_data=f"toggle_event_{ev.id}")
        ])
        kb.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_event_{ev.id}")])
    kb.append([InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def event_create_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="event_create_cancel")]
    ])


def back_to_cases_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к кейсам", callback_data="back_to_cases")]
    ])


def back_to_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")]
    ])


def case_result_keyboard(case_type: str, price: int, is_daily: bool = False, event_id: int | None = None):
    kb = []
    if not is_daily:
        if event_id is not None:
            callback = f"spin_event_again_{event_id}_{price}"
        else:
            callback = f"spin_again_{case_type}_{price}"
        kb.append([InlineKeyboardButton(text="🎰 Открыть ещё раз", callback_data=callback)])
    kb.append([InlineKeyboardButton(text="🔙 Назад к кейсам", callback_data="back_to_cases")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def broadcast_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Запустить рассылку", callback_data="broadcast_send")],
        [InlineKeyboardButton(text="✏️ Переделать", callback_data="broadcast_restart")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
    ])
