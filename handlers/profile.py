from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_cards_list, get_balance, get_user
from keyboards.inline import back_to_cases_keyboard

router = Router()

# ===== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ =====
def group_cards_by_rarity(cards):
    groups = {}
    for card, count in cards:
        groups.setdefault(card.rarity, []).append((card, count))
    return groups

def rarity_selection_keyboard(cards):
    groups = group_cards_by_rarity(cards)
    kb = []
    for rarity, items in groups.items():
        total = sum(count for _, count in items)
        kb.append([InlineKeyboardButton(
            text=f"{rarity.capitalize()} ({total})",
            callback_data=f"rarity_{rarity}"
        )])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def card_banner_keyboard(rarity, index, total):
    kb = []
    nav = []
    if total > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"prev_{rarity}_{index}"))
        nav.append(InlineKeyboardButton(text=f"{index+1}/{total}", callback_data="ignore"))
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"next_{rarity}_{index}"))
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_rarity")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.callback_query(F.data == "my_cards")
async def my_cards(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cards = await get_user_cards_list(user_id)
    if not cards:
        await callback.message.edit_text(
            "🎴 У тебя пока нет карт. Открой кейс, чтобы получить первую!",
            reply_markup=back_to_cases_keyboard()
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        "🎴 <b>Выбери редкость:</b>",
        parse_mode="HTML",
        reply_markup=rarity_selection_keyboard(cards)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("rarity_"))
async def show_rarity(callback: types.CallbackQuery):
    rarity = callback.data.split("_")[1]
    user_id = callback.from_user.id
    cards = await get_user_cards_list(user_id)
    filtered = [(card, count) for card, count in cards if card.rarity == rarity]
    if not filtered:
        await callback.answer("❌ У тебя нет карт этой редкости.", show_alert=True)
        return
    # сохраняем список карт в кеш? проще хранить в callback.data, но мы будем использовать индекс и редкость
    # Для простоты сохраняем в глобальную переменную? нет. Будем передавать индекс через callback.data.
    # Но нам нужен полный список. Мы будем каждый раз запрашивать из БД и фильтровать.
    # Это нормально для небольшого количества карт.
    await show_card(callback, filtered, 0, rarity)

async def show_card(callback, filtered, index, rarity):
    if not filtered:
        return
    card, count = filtered[index]
    total = len(filtered)
    text = (
        f"🖼️ <b>{card.name}</b>\n"
        f"⭐ Редкость: {card.rarity}\n"
        f"💰 Прибыль: {card.sell_price} монет\n"
        f"📦 У тебя: {count} шт.\n\n"
        f"<i>{card.description or ''}</i>"
    )
    kb = card_banner_keyboard(rarity, index, total)
    if card.image_url:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
        # Редактируем caption, а фото остается
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("next_"))
async def next_card(callback: types.CallbackQuery):
    _, rarity, index_str = callback.data.split("_")
    index = int(index_str) + 1
    user_id = callback.from_user.id
    cards = await get_user_cards_list(user_id)
    filtered = [(card, count) for card, count in cards if card.rarity == rarity]
    if index >= len(filtered):
        index = 0
    await show_card(callback, filtered, index, rarity)

@router.callback_query(F.data.startswith("prev_"))
async def prev_card(callback: types.CallbackQuery):
    _, rarity, index_str = callback.data.split("_")
    index = int(index_str) - 1
    user_id = callback.from_user.id
    cards = await get_user_cards_list(user_id)
    filtered = [(card, count) for card, count in cards if card.rarity == rarity]
    if index < 0:
        index = len(filtered) - 1
    await show_card(callback, filtered, index, rarity)

@router.callback_query(F.data == "back_to_rarity")
async def back_to_rarity(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cards = await get_user_cards_list(user_id)
    if not cards:
        await callback.message.edit_text("🎴 У тебя пока нет карт.")
        return
    await callback.message.edit_text(
        "🎴 <b>Выбери редкость:</b>",
        parse_mode="HTML",
        reply_markup=rarity_selection_keyboard(cards)
    )
    await callback.answer()

@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    await callback.answer()
