from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from database import async_session
from models import Promo, PromoActiv, User
from config import ADMIN_IDS

router = Router()


class PromoStates(StatesGroup):
    waiting_name = State()
    waiting_summ = State()
    waiting_activ = State()
    waiting_delete = State()


def promo_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="promo_create")],
        [InlineKeyboardButton(text="📋 Список", callback_data="promo_list")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="promo_delete")],
        [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")],
    ])


async def activate_promo(message: types.Message, code: str):
    code = code.strip()
    if not code:
        await message.answer("🎟️ Укажи код промокода.")
        return
    user_id = message.from_user.id
    async with async_session() as session:
        result = await session.execute(select(Promo).where(Promo.name == code))
        promo = result.scalar_one_or_none()
        if not promo:
            await message.answer("❌ Такого промокода нет.")
            return
        if promo.activ <= 0:
            await message.answer("⌛ Лимит активаций этого промокода уже исчерпан.")
            return
        used = await session.execute(select(PromoActiv).where(PromoActiv.name == code, PromoActiv.user_id == user_id))
        if used.scalar_one_or_none():
            await message.answer("🔒 Ты уже активировал этот промокод.")
            return
        user_result = await session.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            user = User(user_id=user_id, username=message.from_user.username)
            session.add(user)
            await session.flush()
        user.balance += promo.summ
        promo.activ -= 1
        session.add(PromoActiv(user_id=user_id, name=code))
        await session.commit()
        await message.answer(
            "🎁 <b>Промокод активирован!</b>\n\n"
            f"Ты получил <b>+{promo.summ:,} 🪙</b>.".replace(",", " "),
            parse_mode="HTML",
        )


@router.message(F.text.lower().startswith("промо "))
async def activate_promo_text(message: types.Message):
    await activate_promo(message, message.text.split(maxsplit=1)[1])


@router.message(Command("промо"))
async def activate_promo_command(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("🎟️ Использование: <code>/промо КОД</code>", parse_mode="HTML")
        return
    await activate_promo(message, args[1])


@router.callback_query(F.data == "admin_promo")
async def admin_promo_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await callback.message.edit_text(
        "🎟️ <b>Промокоды</b>\n\nСоздавай одноразовые или массовые коды на монеты.",
        parse_mode="HTML",
        reply_markup=promo_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "promo_create")
async def promo_create_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("🎟️ <b>Создание промокода</b>\n\n1/3 — Введи код без пробелов.", parse_mode="HTML")
    await state.set_state(PromoStates.waiting_name)
    await callback.answer()


@router.message(PromoStates.waiting_name)
async def promo_get_name(message: types.Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name or " " in name or len(name) > 40:
        await message.answer("❌ Код должен быть без пробелов и не длиннее 40 символов.")
        return
    async with async_session() as session:
        exists = await session.execute(select(Promo).where(Promo.name == name))
        if exists.scalar_one_or_none():
            await message.answer("❌ Такой промокод уже существует.")
            return
    await state.update_data(name=name)
    await state.set_state(PromoStates.waiting_summ)
    await message.answer("2/3 — Сколько монет выдавать за код? 🪙")


@router.message(PromoStates.waiting_summ)
async def promo_get_summ(message: types.Message, state: FSMContext):
    try:
        summ = int(message.text.strip())
        if summ <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("❌ Введи положительное целое число.")
        return
    await state.update_data(summ=summ)
    await state.set_state(PromoStates.waiting_activ)
    await message.answer("3/3 — Сколько всего раз можно активировать код?")


@router.message(PromoStates.waiting_activ)
async def promo_get_activ(message: types.Message, state: FSMContext):
    try:
        activ = int(message.text.strip())
        if activ <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("❌ Введи положительное целое число.")
        return
    data = await state.get_data()
    async with async_session() as session:
        session.add(Promo(name=data["name"], summ=data["summ"], activ=activ, data="balance"))
        await session.commit()
    await state.clear()
    await message.answer(
        "✅ <b>Промокод создан!</b>\n\n"
        f"🎟️ Код: <code>{data['name']}</code>\n"
        f"🪙 Награда: <b>{data['summ']:,} 🪙</b>\n"
        f"👥 Активаций: <b>{activ}</b>".replace(",", " "),
        parse_mode="HTML",
        reply_markup=promo_keyboard(),
    )


@router.callback_query(F.data == "promo_list")
async def promo_list(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    async with async_session() as session:
        result = await session.execute(select(Promo).order_by(Promo.id.desc()))
        promos = result.scalars().all()
    if not promos:
        text = "📋 <b>Промокодов пока нет.</b>"
    else:
        lines = ["📋 <b>Промокоды</b>\n"]
        for promo in promos:
            lines.append(f"• <code>{promo.name}</code> — {promo.summ:,} 🪙 · осталось {promo.activ}".replace(",", " "))
        text = "\n".join(lines)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=promo_keyboard())
    await callback.answer()


@router.callback_query(F.data == "promo_delete")
async def promo_delete_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await callback.message.edit_text("🗑 Введи точное название промокода, который нужно удалить.")
    await state.set_state(PromoStates.waiting_delete)
    await callback.answer()


@router.message(PromoStates.waiting_delete)
async def promo_delete_execute(message: types.Message, state: FSMContext):
    name = (message.text or "").strip()
    async with async_session() as session:
        result = await session.execute(select(Promo).where(Promo.name == name))
        promo = result.scalar_one_or_none()
        if not promo:
            await message.answer("❌ Промокод не найден.")
            await state.clear()
            return
        await session.delete(promo)
        await session.commit()
    await state.clear()
    await message.answer(f"✅ Промокод <code>{name}</code> удалён.", parse_mode="HTML", reply_markup=promo_keyboard())
