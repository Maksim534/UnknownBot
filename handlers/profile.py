from aiogram import types, Router, F
from database import get_user_cards_list, get_balance, get_user
from keyboards.inline import back_to_cases_keyboard

router = Router()

@router.callback_query(F.data == "my_cards")
async def my_cards(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cards = await get_user_cards_list(user_id)
    if not cards:
        text = "🎴 У тебя пока нет карт. Открой кейс, чтобы получить первую!"
        await callback.message.edit_text(text, reply_markup=back_to_cases_keyboard())
        return

    groups = {}
    for card, count in cards:
        groups.setdefault(card.rarity, []).append((card, count))

    text = "🎴 <b>Твои карты:</b>\n\n"
    for rarity, items in groups.items():
        text += f"<b>{rarity.upper()}</b>\n"
        for card, count in items:
            text += f"• {card.name} x{count}\n"
        text += "\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_cases_keyboard())
    await callback.answer()
