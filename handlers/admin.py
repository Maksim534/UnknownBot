from aiogram import types, Router, F
from aiogram.filters import Command
from config import ADMIN_IDS
from database import get_all_events, toggle_event, get_event_by_id, get_event_cards
from keyboards.inline import admin_menu_keyboard, event_management_keyboard

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещён.")
        return
    await message.answer("⚙️ <b>Админ-панель</b>", parse_mode="HTML", reply_markup=admin_menu_keyboard())

@router.callback_query(F.data == "admin_events")
async def admin_events(callback: types.CallbackQuery):
    events = await get_all_events()
    await callback.message.edit_text("🎯 <b>Управление ивентами</b>", parse_mode="HTML", reply_markup=event_management_keyboard(events))
    await callback.answer()

@router.callback_query(F.data == "admin_panel")
async def admin_panel_back(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ <b>Админ-панель</b>", parse_mode="HTML", reply_markup=admin_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_event_"))
async def toggle_event_callback(callback: types.CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    await toggle_event(event_id)
    await callback.answer("✅ Статус ивента изменён!")
    events = await get_all_events()
    await callback.message.edit_reply_markup(reply_markup=event_management_keyboard(events))

@router.callback_query(F.data.startswith("view_event_"))
async def view_event(callback: types.CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    event = await get_event_by_id(event_id)
    cards = await get_event_cards(event_id)
    card_list = "\n".join([f"• {c.name} ({c.rarity})" for c in cards])
    text = (
        f"📸 <b>{event.name}</b>\n"
        f"💰 Цена: {event.price} монет\n"
        f"Статус: {'🟢 Активен' if event.is_active else '🔴 Выключен'}\n\n"
        f"<b>Персонажи:</b>\n{card_list}"
    )
    if event.photo_url:
        await callback.message.answer_photo(photo=event.photo_url, caption=text, parse_mode="HTML")
    else:
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
