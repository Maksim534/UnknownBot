from database import get_user_card, add_card_to_user, update_balance

async def process_case_open(user_id, card, callback):
    user_card = await get_user_card(user_id, card.id)
    if user_card:
        compensation = int(card.sell_price * 0.2)
        await update_balance(user_id, compensation)
        caption = (
            f"🔄 <b>Дубликат!</b>\n\n"
            f"Тебе выпала карта <b>{card.name}</b>, которая уже у тебя есть.\n"
            f"Ты получил компенсацию: <b>{compensation} монет</b> (20% от стоимости)."
        )
        await callback.message.answer_photo(photo=card.image_url, caption=caption, parse_mode="HTML")
    else:
        await add_card_to_user(user_id, card.id)
        caption = (
            f"🎉 <b>Поздравляю!</b>\n\n"
            f"⭐ <b>{card.name}</b>\n"
            f"Редкость: <b>{card.rarity}</b>\n"
            f"💰 Стоимость: <b>{card.sell_price} монет</b>\n\n"
            f"<i>{card.description or ''}</i>"
        )
        await callback.message.answer_photo(photo=card.image_url, caption=caption, parse_mode="HTML")
