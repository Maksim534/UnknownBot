from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_cards_list, get_balance, get_user
from keyboards.inline import back_to_cases_keyboard, main_menu_keyboard

router = Router()

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

def card_banner_keyboard(rarity, index, total, card_id):
    kb = []
    nav = []
    if total > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"prev_{rarity}_{index}"))
        nav.append(InlineKeyboardButton(text=f"{index+1}/{total}", callback_data="ignore"))
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"next_{rarity}_{index}"))
        kb.append(nav)
    kb.append([
        InlineKeyboardButton(text="💰 Продать", callback_data=f"sell_card_{rarity}_{index}_{card_id}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_rarity")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.callback_query(F.data == "my_cards")
async def my_cards(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cards = await get_user_cards_list(user_id)
    if not cards:
        # Если карт нет – показываем текст с кнопкой назад
        await callback.message.delete()
        await callback.message.answer(
            "🎴 У тебя пока нет карт. Открой кейс, чтобы получить первую!",
            reply_markup=back_to_cases_keyboard()
        )
        await callback.answer()
        return
    # Удаляем текущее сообщение и отправляем новое текстовое с выбором редкости
    await callback.message.delete()
    await callback.message.answer(
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
    # Показываем первую карту с фото
    await show_card(callback, filtered, 0, rarity)

async def show_card(callback, filtered, index, rarity):
    card, count = filtered[index]
    total = len(filtered)
    text = (
        f"🖼️ <b>{card.name}</b>\n"
        f"⭐ Редкость: {card.rarity}\n"
        f"💰 Прибыль: {card.sell_price} монет\n"
        f"📦 У тебя: {count} шт.\n\n"
        f"<i>{card.description or ''}</i>"
    )
    kb = card_banner_keyboard(rarity, index, total, card.id)
    # Удаляем предыдущее сообщение и отправляем новое с фото
    await callback.message.delete()
    if card.image_url:
        await callback.message.answer_photo(
            photo=card.image_url,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=kb
        )

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
        await callback.message.delete()
        await callback.message.answer("🎴 У тебя пока нет карт.")
        return
    await callback.message.delete()
    await callback.message.answer(
        "🎴 <b>Выбери редкость:</b>",
        parse_mode="HTML",
        reply_markup=rarity_selection_keyboard(cards)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🎴 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

# ===== ПРОДАЖА КАРТЫ =====
@router.callback_query(F.data.startswith("sell_card_"))
async def sell_card(callback: types.CallbackQuery):
    _, rarity, index_str, card_id_str = callback.data.split("_")
    card_id = int(card_id_str)
    user_id = callback.from_user.id

    from database import get_user_card, update_balance, add_card_to_user
    user_card = await get_user_card(user_id, card_id)
    if not user_card or user_card.count <= 0:
        await callback.answer("❌ У тебя нет этой карты.", show_alert=True)
        return

    from database import async_session
    from models import Card
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(select(Card).where(Card.id == card_id))
        card = result.scalar_one_or_none()
        if not card:
            await callback.answer("❌ Карта не найдена.", show_alert=True)
            return

    if user_card.count > 1:
        user_card.count -= 1
        await add_card_to_user(user_id, card_id)  # уменьшит количество
    else:
        from database import async_session
        async with async_session() as session:
            await session.delete(user_card)
            await session.commit()

    await update_balance(user_id, card.sell_price)
    await callback.answer(f"💰 Карта продана за {card.sell_price} монет!", show_alert=True)

    # Обновляем отображение
    cards = await get_user_cards_list(user_id)
    filtered = [(c, count) for c, count in cards if c.rarity == rarity]
    if filtered:
        await show_card(callback, filtered, int(index_str), rarity)
    else:
        await callback.message.delete()
        await callback.message.answer(
            "🎴 У тебя больше нет карт этой редкости.",
            reply_markup=back_to_cases_keyboard()
        )

@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    await callback.answer()
