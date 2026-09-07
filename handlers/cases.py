from datetime import datetime, timedelta
from aiogram import types, Router, F
from aiogram.exceptions import TelegramBadRequest
from database import (
    get_balance, update_balance,
    get_daily_case_time, set_daily_case_time,
    get_random_card_by_case, get_random_event_card,
    get_all_events, get_event_by_id
)
from keyboards.inline import (
    cases_menu_keyboard, event_cases_keyboard, main_menu_keyboard,
    case_result_keyboard
)
from utils.helpers import process_case_open

router = Router()

# ===== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ОТКРЫТИЯ КЕЙСА (без удаления сообщения) =====
async def handle_case_open(callback: types.CallbackQuery, case_type: str, price: int, is_daily=False):
    user_id = callback.from_user.id
    balance = await get_balance(user_id)

    if not is_daily:
        if balance < price:
            await callback.answer(f"❌ Недостаточно монет! Нужно {price}.", show_alert=True)
            return
        await update_balance(user_id, -price)

    card = await get_random_card_by_case(case_type)
    if not card:
        await callback.answer("❌ Нет карт в этом кейсе.", show_alert=True)
        return

    # Отправляем результат (сообщение с картой)
    await process_case_open(user_id, card, callback, case_type, price, is_daily)

    if is_daily:
        await set_daily_case_time(user_id, datetime.now())

# ===== КЕЙСЫ =====
@router.callback_query(F.data == "how_to_play")
async def how_to_play(callback: types.CallbackQuery):
    text = (
        "📖 <b>Как играть?</b>\n\n"
        "1. Открывай кейсы и получай карты.\n"
        "2. Каждая карта имеет свою редкость и цену.\n"
        "3. Если выпадает дубликат — ты получаешь 20% от стоимости карты.\n"
        "4. Участвуй в ивентах, чтобы получить эксклюзивные карты.\n"
        "5. Следи за новостями и акциями!"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cases_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "help")
async def help_callback(callback: types.CallbackQuery):
    text = (
        "❓ <b>Помощь</b>\n\n"
        "🎴 <b>Как играть:</b>\n"
        "• Нажми «📦 Кейсы» и выбери кейс для открытия\n"
        "• Каждый день доступен бесплатный ежедневный кейс\n"
        "• При выпадении дубликата ты получаешь 20% от стоимости карты\n"
        "• В ивентовых кейсах можно получить эксклюзивные карты\n\n"
        "💰 <b>Доход:</b>\n"
        "• Каждая карта приносит монеты в минуту\n"
        "• Обычная — 1 монета/мин, редкая — 5, эпическая — 15, легендарная — 50, мифическая — 150, ультралегендарная — 500\n"
        "• Заходи в раздел «💰 Доход» и забирай накопленное!\n\n"
        "❓ Вопросы? Пиши разработчику: @dev"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cases_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "cases_menu")
async def show_cases_menu(callback: types.CallbackQuery):
    events = await get_all_events()
    active_events = [ev for ev in events if ev.is_active]
    if active_events:
        text = "📦 <b>Кейсы</b>\n\n🎉 <b>Активные ивенты:</b>"
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=event_cases_keyboard(active_events))
    else:
        await callback.message.edit_text("📦 <b>Выбери кейс для открытия:</b>", parse_mode="HTML", reply_markup=cases_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "back_to_cases")
async def back_to_cases(callback: types.CallbackQuery):
    await callback.message.delete()
    events = await get_all_events()
    active_events = [ev for ev in events if ev.is_active]
    if active_events:
        text = "📦 <b>Кейсы</b>\n\n🎉 <b>Активные ивенты:</b>"
        await callback.message.answer(text, parse_mode="HTML", reply_markup=event_cases_keyboard(active_events))
    else:
        await callback.message.answer("📦 <b>Выбери кейс для открытия:</b>", parse_mode="HTML", reply_markup=cases_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("🎴 <b>Главное меню</b>", parse_mode="HTML", reply_markup=main_menu_keyboard())
    await callback.answer()

# ===== ОТКРЫТИЕ КЕЙСОВ =====
@router.callback_query(F.data == "daily_case")
async def daily_case(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    last_time = await get_daily_case_time(user_id)
    now = datetime.now()
    if last_time and now - last_time < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - last_time)
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        await callback.answer(f"⏳ Ещё не доступен! Осталось {hours}ч {minutes}мин.", show_alert=True)
        return
    # Удаляем меню кейсов
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await handle_case_open(callback, "обычный", 0, is_daily=True)

@router.callback_query(F.data == "normal_case")
async def normal_case(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await handle_case_open(callback, "обычный", 100)

@router.callback_query(F.data == "rare_case")
async def rare_case(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await handle_case_open(callback, "редкий", 8000)

@router.callback_query(F.data == "mythic_case")
async def mythic_case(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await handle_case_open(callback, "мифический", 60000)

@router.callback_query(F.data == "ultra_case")
async def ultra_case(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await handle_case_open(callback, "ультралегендарный", 2000000)

# ===== ИВЕНТОВЫЕ КЕЙСЫ =====
@router.callback_query(F.data.startswith("event_case_"))
async def event_case(callback: types.CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    event = await get_event_by_id(event_id)
    if not event or not event.is_active:
        await callback.answer("❌ Этот ивент уже закончился.", show_alert=True)
        return
    user_id = callback.from_user.id
    balance = await get_balance(user_id)
    if balance < event.price:
        await callback.answer(f"❌ Недостаточно монет! Нужно {event.price}.", show_alert=True)
        return
    await update_balance(user_id, -event.price)
    card = await get_random_event_card(event_id)
    if not card:
        await callback.answer("❌ В этом ивенте нет карт.", show_alert=True)
        return
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await process_case_open(user_id, card, callback, case_type="ивент", price=event.price, is_daily=False)

# ===== КНОПКА "КРУТИТЬ ЕЩЁ РАЗ" =====
@router.callback_query(F.data.startswith("spin_again_"))
async def spin_again(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("❌ Ошибка.", show_alert=True)
        return
    case_type = parts[2]
    try:
        price = int(parts[3])
    except (IndexError, ValueError):
        price = 0

    # Удаляем текущее сообщение с результатом
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    # Открываем кейс снова (не ежедневный)
    await handle_case_open(callback, case_type, price, is_daily=False)
