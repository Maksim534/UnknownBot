from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Как играть", callback_data="how_to_play")],
        [InlineKeyboardButton(text="📦 Кейсы", callback_data="cases_menu"),
         InlineKeyboardButton(text="🎴 Мои карты", callback_data="my_cards")],
        [InlineKeyboardButton(text="💰 Доход", callback_data="claim_income"),
         InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])

def cases_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Ежедневный кейс (бесплатно)", callback_data="daily_case")],
        [InlineKeyboardButton(text="📦 Обычный кейс (1 000 монет)", callback_data="normal_case")],
        [InlineKeyboardButton(text="🔴 Редкий кейс (5 000 монет)", callback_data="rare_case")],
        [InlineKeyboardButton(text="🟣 Мифический кейс (15 000 монет)", callback_data="mythic_case")],
        [InlineKeyboardButton(text="🌟 Ультра-легендарный кейс (50 000 монет)", callback_data="ultra_case")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def event_cases_keyboard(events):
    kb = []
    for ev in events:
        kb.append([InlineKeyboardButton(text=f"🎉 {ev.name} ({ev.price} монет)", callback_data=f"event_case_{ev.id}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_cases")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Ивенты", callback_data="admin_events")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Выход", callback_data="admin_exit")]
    ])

def event_management_keyboard(events):
    kb = []
    for ev in events:
        status = "🟢 Включить" if not ev.is_active else "🔴 Выключить"
        kb.append([
            InlineKeyboardButton(text=f"{ev.name} ({ev.price})", callback_data=f"view_event_{ev.id}"),
            InlineKeyboardButton(text=status, callback_data=f"toggle_event_{ev.id}")
        ])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_to_cases_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cases_menu")]
    ])

def back_to_rarity_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_rarity")]
    ])
