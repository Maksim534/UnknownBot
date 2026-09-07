from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, delete
from database import async_session
from models import Promo, PromoActiv, User
from config import ADMIN_IDS

router = Router()

class PromoStates(StatesGroup):
    waiting_name = State()
    waiting_summ = State()
    waiting_activ = State()
    waiting_delete = State()

# ===== ОБРАБОТЧИК СООБЩЕНИЙ "промо <код>" =====
@router.message(F.text.lower().startswith("промо "))
async def activate_promo_text(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Использование: промо <код>")
        return
    code = parts[1].strip()
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(Promo).where(Promo.name == code))
        promo = result.scalar_one_or_none()
        if not promo:
            await message.answer("❌ Промокод не найден.")
            return
        if promo.activ <= 0:
            await message.answer("❌ Промокод уже использован.")
            return
        result2 = await session.execute(
            select(PromoActiv).where(PromoActiv.name == code, PromoActiv.user_id == user_id)
        )
        if result2.scalar_one_or_none():
            await message.answer("❌ Ты уже активировал этот промокод.")
            return
        user_result = await session.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.balance += promo.summ
        promo.activ -= 1
        session.add(PromoActiv(user_id=user_id, name=code))
        await session.commit()
        await message.answer(f"✅ Промокод активирован! Ты получил {promo.summ} монет.")

# ===== КОМАНДА /промо (на случай привычки) =====
@router.message(Command("промо"))
async def activate_promo_command(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /промо <код>")
        return
    code = args[1]
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(Promo).where(Promo.name == code))
        promo = result.scalar_one_or_none()
        if not promo:
            await message.answer("❌ Промокод не найден.")
            return
        if promo.activ <= 0:
            await message.answer("❌ Промокод уже использован.")
            return
        result2 = await session.execute(
            select(PromoActiv).where(PromoActiv.name == code, PromoActiv.user_id == user_id)
        )
        if result2.scalar_one_or_none():
            await message.answer("❌ Ты уже активировал этот промокод.")
            return
        user_result = await session.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.balance += promo.summ
        promo.activ -= 1
        session.add(PromoActiv(user_id=user_id, name=code))
        await session.commit()
        await message.answer(f"✅ Промокод активирован! Ты получил {promo.summ} монет.")

# ===== АДМИНСКАЯ ЧАСТЬ =====

# Меню промокодов из админки
@router.callback_query(F.data == "admin_promo")
async def admin_promo(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await callback.message.edit_text(
        "🎟️ <b>Управление промокодами</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать промокод", callback_data="promo_create")],
            [InlineKeyboardButton(text="🗑️ Удалить промокод", callback_data="promo_delete")],
            [InlineKeyboardButton(text="📋 Список промокодов", callback_data="promo_list")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "promo_create")
async def promo_create_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await callback.message.edit_text("Введите название промокода (латиница, без пробелов):")
    await state.set_state(PromoStates.waiting_name)
    await callback.answer()

@router.message(PromoStates.waiting_name)
async def promo_get_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await message.answer("Введите сумму (монеты):")
    await state.set_state(PromoStates.waiting_summ)

@router.message(PromoStates.waiting_summ)
async def promo_get_summ(message: types.Message, state: FSMContext):
    try:
        summ = int(message.text)
        await state.update_data(summ=summ)
        await message.answer("Введите количество активаций (сколько раз можно использовать):")
        await state.set_state(PromoStates.waiting_activ)
    except ValueError:
        await message.answer("❌ Введите число.")

@router.message(PromoStates.waiting_activ)
async def promo_get_activ(message: types.Message, state: FSMContext):
    try:
        activ = int(message.text)
        data = await state.get_data()
        async with async_session() as session:
            promo = Promo(name=data["name"], summ=data["summ"], activ=activ, data="users/balance")
            session.add(promo)
            await session.commit()
        await message.answer(
            f"✅ Промокод <b>{data['name']}</b> создан!\n"
            f"Сумма: {data['summ']} монет\n"
            f"Активаций: {activ}",
            parse_mode="HTML"
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число.")

@router.callback_query(F.data == "promo_list")
async def promo_list(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    async with async_session() as session:
        result = await session.execute(select(Promo))
        promos = result.scalars().all()
    if not promos:
        text = "📋 Список промокодов пуст."
    else:
        text = "📋 <b>Список промокодов:</b>\n\n"
        for p in promos:
            text += f"• <b>{p.name}</b> — {p.summ} монет, осталось активаций: {p.activ}\n"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_admin_panel())

@router.callback_query(F.data == "promo_delete")
async def promo_delete_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await callback.message.edit_text("Введите название промокода, который хотите удалить:")
    await state.set_state(PromoStates.waiting_delete)
    await callback.answer()

@router.message(PromoStates.waiting_delete)
async def promo_delete_execute(message: types.Message, state: FSMContext):
    name = message.text.strip()
    async with async_session() as session:
        result = await session.execute(select(Promo).where(Promo.name == name))
        promo = result.scalar_one_or_none()
        if not promo:
            await message.answer("❌ Промокод не найден.")
            await state.clear()
            return
        await session.delete(promo)
        await session.commit()
    await message.answer(f"✅ Промокод <b>{name}</b> удалён.", parse_mode="HTML")
    await state.clear()

# ===== ВСПОМОГАТЕЛЬНАЯ КЛАВИАТУРА =====
def back_to_admin_panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_panel")]
    ])
