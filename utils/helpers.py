from database import get_user_card, add_card_to_user, update_balance
from keyboards.inline import case_result_keyboard


async def process_case_open(
    user_id,
    card,
    callback,
    case_type: str,
    price: int,
    is_daily: bool = False,
    event_id: int | None = None,
):
    user_card = await get_user_card(user_id, card.id)
    result_keyboard = case_result_keyboard(case_type, price, is_daily, event_id=event_id)

    if user_card:
        compensation = int(card.sell_price * 0.2)
        await update_balance(user_id, compensation)
        caption = (
            "🔄 <b>Дубликат!</b>\n\n"
            f"Тебе снова выпала <b>{card.name}</b>.\n"
            f"💰 Компенсация: <b>+{compensation:,} 🪙</b>".replace(",", " ")
        )
    else:
        await add_card_to_user(user_id, card.id)
        caption = (
            "🎉 <b>Новая карта!</b>\n\n"
            f"⭐ <b>{card.name}</b>\n"
            f"🏷 Редкость: <b>{card.rarity}</b>\n"
            f"💰 Стоимость: <b>{card.sell_price:,} 🪙</b>\n\n"
            f"<i>{card.description or 'Уникальная карта коллекции.'}</i>"
        )

    if card.image_url:
        await callback.message.answer_photo(
            photo=card.image_url,
            caption=caption,
            parse_mode="HTML",
            reply_markup=result_keyboard,
        )
    else:
        await callback.message.answer(caption, parse_mode="HTML", reply_markup=result_keyboard)
