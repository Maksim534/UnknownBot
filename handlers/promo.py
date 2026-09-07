from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import async_session
from models import Promo, PromoActiv, User
from sqlalchemy import select
from config import ADMIN_IDS
from keyboards.inline import admin_menu_keyboard

router = Router()

class PromoStates(StatesGroup):
    waiting_name = State()
    waiting_summ = State()
    waiting_activ = State()

# ===== ОБРАБОТЧИК СООБЩЕНИЙ, НАЧИНАЮЩИХСЯ С "промо " =====
@router.message(F.text.lower().startswith("промо "))
async def activate_promo_text(message: types.Message):
    # Разбиваем сообщение на части: "промо" и код
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Использование: промо <код>")
        return
    code = parts[1].strip()
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
        promo.activ -= 1
        session.add(PromoActiv(user_id=user_id, name=code))
        await session.commit()
        await message.answer(f"✅ Промокод активирован! Ты получил {promo.summ} монет.")

# ===== АЛЬТЕРНАТИВА: КОМАНДА /промо (на случай, если кто-то привык к слешу) =====
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

# ===== АДМИН-ЧАСТЬ (создание, удаление, список промокодов) =====
# ... (код, который я уже давал ранее, остаётся без изменений)
