from datetime import datetime, timedelta
from aiogram import types, Router, F
from aiogram.exceptions import TelegramBadRequest
from database import (
    get_balance, update_balance, get_daily_case_time, set_daily_case_time,
    get_random_card_by_case, get_random_event_card, get_active_events, get_event_by_id,
)
from keyboards.inline import cases_menu_keyboard, event_cases_keyboard, main_menu_keyboard, case_result_keyboard
from utils.helpers import process_case_open

router = Router()


async def render_cases_menu(callback: types.CallbackQuery, delete=False):
    events = await get_active_events()
    text = "📦 <b>Кейсы</b>\n\n"
    if events:
        text += "🎉 <b>Сейчас доступны ивенты:</b>"
    else:
        text += "Выбирай кейс и попробуй получить редкую карту!"

    if delete:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(text, parse_mode="HTML", reply_markup=cases_menu_keyboard())
        if events:
            await callback.message.answer("🎯 <b>Ивентовые кейсы</b>", parse_mode="HTML", reply_markup=event_cases_keyboard(events))
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cases_menu_keyboard())
        if events:
            await callback.message.answer("🎯 <b>Ивентовые кейсы</b>", parse_mode="HTML", reply_markup=event_cases_keyboard(events))


async def handle_case_open(callback: types.CallbackQuery, case_type: str, price: int, is_daily=False):
    user_id = callback.from_user.id
    balance = await get_balance(user_id)

    if not is_daily and balance < price:
        await callback.answer(
            f"❌ Недостаточно монет. Нужно {price:,} 🪙, а у тебя {balance:,} 🪙.".replace(",", " "),
            show_alert=True,
        )
        return

    card = await get_random_card_by_case(case_type)
    if not card:
        await callback.answer("⚠️ В этом кейсе пока нет доступных карт.", show_alert=True)
        return

    if not is_daily:
        await update_balance(user_id, -price)

    await process_case_open(user_id, card, callback, case_type, price, is_daily)
    if is_daily:
        await set_daily_case_time(user_id, datetime.now())


@router.callback_query(F.data == "how_to_play")
async def how_to_play(callback: types.CallbackQuery):
    text = (
        "📖 <b>Как играть</b>\n\n"
        "🎴 Открывай кейсы и собирай коллекцию.\n"
        "⭐ Чем выше редкость — тем ценнее карта и её пассивный доход.\n"
        "🔄 Дубликаты автоматически превращаются в компенсацию.\n"
        "🎉 Следи за ивентами — там могут появляться отдельные карты.\n"
        "💰 Собирай доход и используй монеты для новых открытий."
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cases_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: types.CallbackQuery):
    text = (
        "❓ <b>Помощь</b>\n\n"
        "📦 <b>Кейсы</b> — источник новых карт.\n"
        "🎴 <b>Мои карты</b> — твоя коллекция.\n"
        "💰 <b>Баланс</b> — доступные монеты.\n"
        "💸 <b>Доход</b> — накопления от собранных карт.\n\n"
        "🎟️ Промокод можно активировать сообщением <code>промо КОД</code>.\n\n"
        "Если что-то работает неправильно — сообщи администрации."
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cases_menu")
async def show_cases_menu(callback: types.CallbackQuery):
    await render_cases_menu(callback)
    await callback.answer()


@router.callback_query(F.data == "back_to_cases")
async def back_to_cases(callback: types.CallbackQuery):
    await render_cases_menu(callback, delete=True)
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("🎴 <b>Главное меню</b>\n\nВыбирай, что будем делать!", parse_mode="HTML", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "daily_case")
async def daily_case(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    last_time = await get_daily_case_time(user_id)
    now = datetime.now()
    if last_time and now - last_time < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - last_time)
        total_seconds = int(remaining.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        await callback.answer(f"⏳ Бесплатный кейс будет доступен через {hours}ч {minutes}мин.", show_alert=True)
        return
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await handle_case_open(callback, "обычный", 0, is_daily=True)


async def paid_case(callback, case_type, price):
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await handle_case_open(callback, case_type, price)


@router.callback_query(F.data == "normal_case")
async def normal_case(callback: types.CallbackQuery):
    await paid_case(callback, "обычный", 100)


@router.callback_query(F.data == "rare_case")
async def rare_case(callback: types.CallbackQuery):
    await paid_case(callback, "редкий", 8000)


@router.callback_query(F.data == "mythic_case")
async def mythic_case(callback: types.CallbackQuery):
    await paid_case(callback, "мифический", 60000)


@router.callback_query(F.data == "ultra_case")
async def ultra_case(callback: types.CallbackQuery):
    await paid_case(callback, "ультралегендарный", 2000000)


@router.callback_query(F.data.startswith("event_case_"))
async def event_case(callback: types.CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    event = await get_event_by_id(event_id)
    if not event or not event.is_active:
        await callback.answer("❌ Этот ивент сейчас недоступен.", show_alert=True)
        return

    card = await get_random_event_card(event_id)
    if not card:
        await callback.answer("⚠️ В этом ивенте пока нет карт.", show_alert=True)
        return

    user_id = callback.from_user.id
    balance = await get_balance(user_id)
    if balance < event.price:
        await callback.answer(
            f"❌ Не хватает монет. Нужно {event.price:,} 🪙.".replace(",", " "),
            show_alert=True,
        )
        return

    await update_balance(user_id, -event.price)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await process_case_open(user_id, card, callback, "ивент", event.price, False, event_id=event_id)


@router.callback_query(F.data.startswith("spin_again_"))
async def spin_again(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) != 4:
        await callback.answer("❌ Не удалось повторить открытие.", show_alert=True)
        return
    case_type = parts[2]
    price = int(parts[3])
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await handle_case_open(callback, case_type, price, is_daily=False)


@router.callback_query(F.data.startswith("spin_event_again_"))
async def spin_event_again(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) != 5:
        await callback.answer("❌ Не удалось повторить открытие.", show_alert=True)
        return
    event_id = int(parts[3])
    price = int(parts[4])
    event = await get_event_by_id(event_id)
    if not event or not event.is_active:
        await callback.answer("❌ Этот ивент уже недоступен.", show_alert=True)
        return
    card = await get_random_event_card(event_id)
    if not card:
        await callback.answer("⚠️ В ивенте закончились карты.", show_alert=True)
        return
    if await get_balance(callback.from_user.id) < price:
        await callback.answer("❌ Недостаточно монет для нового открытия.", show_alert=True)
        return
    await update_balance(callback.from_user.id, -price)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await process_case_open(callback.from_user.id, card, callback, "ивент", price, False, event_id=event_id)
