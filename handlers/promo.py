from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import async_session
from models import Promo, PromoActiv, User
from sqlalchemy import select, update
from config import ADMIN_IDS
from keyboards.inline import admin_menu_keyboard, back_to_admin_keyboard

router = Router()

class PromoStates(StatesGroup):
    waiting_name = State()
    waiting_summ = State()
    waiting_activ = State()
    waiting_delete = State()

# ===== ПОЛЬЗОВАТЕЛЬ: АКТИВАЦИЯ ПРОМОКОДА =====
@router.message(Command("промокод"))
async def activate_promo(message: types.Message, state: FSMContext):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /promo <код>")
        return
    code = args[1]
    user_id = message.from_user.id

    async with async_session() as session:
        # Проверяем, существует ли промокод
        result = await session.execute(select(Promo).where(Promo.name == code))
        promo = result.scalar_one_or_none()
        if not promo:
            await message.answer("❌ Промокод не найден.")
            return
        if promo.activ <= 0:
            await message.answer("❌ Промокод уже использован.")
            return
        # Проверяем, не активировал ли уже
        result2 = await session.execute(
            select(PromoActiv).where(PromoActiv.name == code, PromoActiv.user_id == user_id)
        )
        if result2.scalar_one_or_none():
            await message.answer("❌ Ты уже активировал этот промокод.")
            return
        # Начисляем монеты
        user_result = await session.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.balance += promo.summ
        # Уменьшаем количество активаций
        promo.activ -= 1
        # Записываем активацию
        session.add(PromoActiv(user_id=user_id, name=code))
        await session.commit()
        await message.answer(f"✅ Промокод активирован! Ты получил {promo.summ} монет.")
