import asyncio
import platform
import time
from datetime import datetime

from aiogram import types, Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select, text

from config import ADMIN_IDS
from database import (
    async_session, get_all_events, toggle_event, get_event_by_id, get_event_cards,
    get_all_cards, create_event, delete_event, get_admin_stats, get_all_user_ids,
)
from models import Card
from keyboards.inline import (
    admin_menu_keyboard, event_management_keyboard, event_create_cancel_keyboard,
    broadcast_confirm_keyboard,
)

router = Router()
START_TIME = time.monotonic()


class EventCreateStates(StatesGroup):
    name = State()
    price = State()
    photo = State()
    cards = State()


class BroadcastStates(StatesGroup):
    content = State()
    button_text = State()
    button_url = State()
    confirm = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def fmt_num(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def admin_home_text() -> str:
    return (
        "⚙️ <b>Панель администратора</b>\n\n"
        "Здесь можно управлять экономикой, ивентами, промокодами и рассылками.\n\n"
        "🛡 Доступ только для владельца и назначенных администраторов."
    )


@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У тебя нет доступа к панели администратора.")
        return
    await message.answer(admin_home_text(), parse_mode="HTML", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin_panel")
async def admin_panel_back(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await callback.message.edit_text(admin_home_text(), parse_mode="HTML", reply_markup=admin_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_exit")
async def admin_exit(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await callback.message.edit_text("👋 <b>Админ-панель закрыта.</b>", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    stats = await get_admin_stats()
    text_value = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{fmt_num(stats['users'])}</b>\n"
        f"🎴 Карт в базе: <b>{fmt_num(stats['cards'])}</b>\n"
        f"🃏 Собрано карт: <b>{fmt_num(stats['user_cards'])}</b>\n"
        f"🎯 Всего ивентов: <b>{fmt_num(stats['events'])}</b>\n"
        f"🟢 Активных ивентов: <b>{fmt_num(stats['active_events'])}</b>\n"
        f"🎟️ Промокодов: <b>{fmt_num(stats['promos'])}</b>\n"
        f"🪙 Монет на балансах: <b>{fmt_num(stats['total_balance'])}</b>\n\n"
        f"🕒 Обновлено: <b>{datetime.now():%d.%m.%Y %H:%M:%S}</b>"
    )
    await callback.message.edit_text(text_value, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")],
    ]))
    await callback.answer()


@router.callback_query(F.data == "admin_hosting")
async def admin_hosting(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    uptime = int(time.monotonic() - START_TIME)
    days, rem = divmod(uptime, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        db_status = "🟢 подключена"
    except Exception as exc:
        db_status = f"🔴 ошибка: {type(exc).__name__}"

    text_value = (
        "🖥 <b>Состояние хостинга</b>\n\n"
        f"🤖 Бот: <b>запущен</b>\n"
        f"⏱ Аптайм: <b>{days}д {hours}ч {minutes}м {seconds}с</b>\n"
        f"💾 База данных: <b>{db_status}</b>\n"
        f"🐍 Python: <b>{platform.python_version()}</b>\n"
        f"🖥 ОС: <b>{platform.system()}</b>\n"
        f"🆔 PID: <b>{__import__('os').getpid()}</b>"
    )
    await callback.message.edit_text(text_value, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Проверить ещё раз", callback_data="admin_hosting")],
        [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")],
    ]))
    await callback.answer()


# ===== ИВЕНТЫ =====
@router.callback_query(F.data == "admin_events")
async def admin_events(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    events = await get_all_events()
    await callback.message.edit_text(
        "🎯 <b>Управление ивентами</b>\n\n"
        "Создавай временные кейсы и включай их тогда, когда нужно.",
        parse_mode="HTML",
        reply_markup=event_management_keyboard(events),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_event_"))
async def toggle_event_callback(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    event_id = int(callback.data.split("_")[2])
    status = await toggle_event(event_id)
    await callback.answer("🟢 Ивент включён!" if status else "⚫ Ивент выключен!")
    events = await get_all_events()
    await callback.message.edit_reply_markup(reply_markup=event_management_keyboard(events))


@router.callback_query(F.data.startswith("view_event_"))
async def view_event(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    event_id = int(callback.data.split("_")[2])
    event = await get_event_by_id(event_id)
    if not event:
        await callback.answer("❌ Ивент не найден.", show_alert=True)
        return
    cards = await get_event_cards(event_id)
    card_list = "\n".join(f"• {c.name} — {c.rarity}" for c in cards) or "— карт нет —"
    text_value = (
        f"🎯 <b>{event.name}</b>\n\n"
        f"💰 Цена открытия: <b>{fmt_num(event.price)} 🪙</b>\n"
        f"📌 Статус: <b>{'🟢 активен' if event.is_active else '⚫ выключен'}</b>\n"
        f"🃏 Карт: <b>{len(cards)}</b>\n\n"
        f"<b>Содержимое:</b>\n{card_list}"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К ивентам", callback_data="admin_events")]
    ])
    if event.photo_url:
        await callback.message.answer_photo(photo=event.photo_url, caption=text_value, parse_mode="HTML", reply_markup=markup)
    else:
        await callback.message.edit_text(text_value, parse_mode="HTML", reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("delete_event_"))
async def delete_event_callback(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    event_id = int(callback.data.split("_")[2])
    if await delete_event(event_id):
        await callback.answer("🗑 Ивент удалён.", show_alert=True)
    else:
        await callback.answer("❌ Ивент не найден.", show_alert=True)
    events = await get_all_events()
    await callback.message.edit_reply_markup(reply_markup=event_management_keyboard(events))


@router.callback_query(F.data == "event_create")
async def event_create_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await state.clear()
    await state.set_state(EventCreateStates.name)
    await callback.message.edit_text("🎯 <b>Создание ивента</b>\n\n1/4 — Напиши название ивента.", parse_mode="HTML", reply_markup=event_create_cancel_keyboard())
    await callback.answer()


@router.message(EventCreateStates.name)
async def event_create_name(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    name = (message.text or "").strip()
    if not name or len(name) > 80:
        await message.answer("❌ Название должно быть от 1 до 80 символов.")
        return
    await state.update_data(name=name)
    await state.set_state(EventCreateStates.price)
    await message.answer("2/4 — Введи цену открытия кейса в монетах 🪙.")


@router.message(EventCreateStates.price)
async def event_create_price(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        price = int(message.text.strip())
        if price < 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("❌ Введи целое число от 0 и выше.")
        return
    await state.update_data(price=price)
    await state.set_state(EventCreateStates.photo)
    await message.answer("3/4 — Пришли ссылку на картинку кейса. Если картинка не нужна — отправь <code>-</code>.", parse_mode="HTML")


@router.message(EventCreateStates.photo)
async def event_create_photo(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    photo = (message.text or "").strip()
    if photo == "-":
        photo = None
    elif not (photo.startswith("http://") or photo.startswith("https://")):
        await message.answer("❌ Нужна ссылка, начинающаяся с http:// или https://, либо <code>-</code>.", parse_mode="HTML")
        return
    await state.update_data(photo=photo)
    await state.set_state(EventCreateStates.cards)
    cards = await get_all_cards()
    names = "\n".join(f"• {c.name}" for c in cards)
    await message.answer(
        "4/4 — Напиши имена карт через запятую.\n\n"
        "Доступные карты:\n" + names,
    )


@router.message(EventCreateStates.cards)
async def event_create_cards(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    requested = [x.strip() for x in (message.text or "").split(",") if x.strip()]
    if not requested:
        await message.answer("❌ Укажи хотя бы одну карту.")
        return
    cards = await get_all_cards()
    by_name = {c.name.casefold(): c for c in cards}
    selected = []
    missing = []
    for name in requested:
        card = by_name.get(name.casefold())
        if card and card.id not in selected:
            selected.append(card.id)
        elif not card:
            missing.append(name)
    if missing:
        await message.answer("❌ Не найдены карты:\n" + "\n".join(f"• {x}" for x in missing))
        return
    data = await state.get_data()
    event_id = await create_event(data["name"], data["price"], data.get("photo"), selected)
    await state.clear()
    await message.answer(
        f"✅ <b>Ивент создан!</b>\n\n"
        f"🎯 {data['name']}\n"
        f"💰 {fmt_num(data['price'])} 🪙\n"
        f"🃏 Карт: {len(selected)}\n\n"
        "Ивент пока выключен. Включить его можно в разделе «🎯 Ивенты».",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "event_create_cancel")
async def event_create_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    events = await get_all_events()
    await callback.message.edit_text("🎯 <b>Управление ивентами</b>", parse_mode="HTML", reply_markup=event_management_keyboard(events))
    await callback.answer("Создание отменено.")


# ===== РАССЫЛКА =====
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await state.clear()
    await state.set_state(BroadcastStates.content)
    await callback.message.edit_text(
        "📣 <b>Новая рассылка</b>\n\n"
        "Отправь <b>одно сообщение</b> для рассылки: текст или фото с подписью.\n"
        "После этого можно добавить inline-кнопку со ссылкой.\n\n"
        "Пример: 🖼 фото + текст + кнопка «Открыть» → ссылка.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(BroadcastStates.content)
async def broadcast_content(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(source_chat_id=message.chat.id, source_message_id=message.message_id)
    await state.set_state(BroadcastStates.button_text)
    await message.answer("🔘 Напиши текст кнопки или отправь <code>-</code>, если кнопка не нужна.", parse_mode="HTML")


@router.message(BroadcastStates.button_text)
async def broadcast_button_text(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    value = (message.text or "").strip()
    if value == "-":
        await state.update_data(button_text=None)
        await state.set_state(BroadcastStates.confirm)
        await show_broadcast_preview(message, state)
        return
    if not value or len(value) > 64:
        await message.answer("❌ Текст кнопки должен быть от 1 до 64 символов.")
        return
    await state.update_data(button_text=value)
    await state.set_state(BroadcastStates.button_url)
    await message.answer("🔗 Теперь отправь ссылку кнопки, например <code>https://t.me/...</code>.", parse_mode="HTML")


@router.message(BroadcastStates.button_url)
async def broadcast_button_url(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    url = (message.text or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer("❌ Ссылка должна начинаться с http:// или https://.")
        return
    await state.update_data(button_url=url)
    await state.set_state(BroadcastStates.confirm)
    await show_broadcast_preview(message, state)


async def show_broadcast_preview(message: types.Message, state: FSMContext):
    data = await state.get_data()
    button = "без кнопки"
    if data.get("button_text"):
        button = f"«{data['button_text']}» → {data.get('button_url')}"
    await message.answer(
        "👀 <b>Предпросмотр настроек</b>\n\n"
        f"🔘 Кнопка: {button}\n\n"
        "Само исходное сообщение будет скопировано пользователям без добавления подписи от бота.",
        parse_mode="HTML",
        reply_markup=broadcast_confirm_keyboard(),
    )


@router.callback_query(F.data == "broadcast_send")
async def broadcast_send(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    data = await state.get_data()
    if not data.get("source_message_id"):
        await callback.answer("❌ Сообщение для рассылки потеряно.", show_alert=True)
        await state.clear()
        return

    users = await get_all_user_ids()
    markup = None
    if data.get("button_text"):
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=data["button_text"], url=data["button_url"])]
        ])

    await callback.message.edit_text(
        f"📣 <b>Рассылка запущена</b>\n\n👥 Получателей: <b>{len(users)}</b>\n⏳ Отправляю...",
        parse_mode="HTML",
    )
    success = 0
    failed = 0
    for user_id in users:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=data["source_chat_id"],
                message_id=data["source_message_id"],
                reply_markup=markup,
            )
            success += 1
            await asyncio.sleep(0.04)
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1

    await state.clear()
    await callback.message.answer(
        "✅ <b>Рассылка завершена</b>\n\n"
        f"📨 Доставлено: <b>{success}</b>\n"
        f"⚠️ Не доставлено: <b>{failed}</b>",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "broadcast_restart")
async def broadcast_restart(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(BroadcastStates.content)
    await callback.message.edit_text("📣 Отправь новое сообщение для рассылки — текст или фото с подписью.", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(admin_home_text(), parse_mode="HTML", reply_markup=admin_menu_keyboard())
    await callback.answer("Рассылка отменена.")
