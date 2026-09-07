from aiogram import types, Router
from aiogram.filters import Command
from keyboards.inline import main_menu_keyboard
from database import register_user, claim_income, get_balance

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    await register_user(user_id, username)

    text = (
        "🎴 <b>Добро пожаловать в Anime Card Collector!</b>\n\n"
        "Здесь ты можешь собирать уникальные карты аниме-девушек,\n"
        "открывать кейсы и получать награды.\n\n"
        "🔥 <b>Что ты можешь делать:</b>\n"
        "• 📦 Открывать кейсы и выбивать карты\n"
        "• 💰 Получать монеты за дубликаты (20% от стоимости)\n"
        "• 🎉 Участвовать в ивентах с эксклюзивными картами\n"
        "• 💸 Пассивный доход с каждой карты!\n\n"
        "Выбери действие ниже:"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())

@router.message(Command("help"))
async def cmd_help(message: types.Message):
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
    await message.answer(text, parse_mode="HTML")

# ===== КНОПКА "ДОХОД" =====
from aiogram import F

@router.callback_query(F.data == "claim_income")
async def claim_income_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    earned = await claim_income(user_id)
    balance = await get_balance(user_id)
    if earned == 0:
        await callback.message.answer(
            "⏳ Нет накопленного дохода.\n"
            "Подожди немного, карты приносят монеты каждую минуту.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await callback.message.answer(
            f"💰 <b>Доход получен!</b>\n\n"
            f"Ты заработал <b>{earned} монет</b> за время отсутствия.\n"
            f"Твой баланс: <b>{balance} монет</b>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    await callback.answer()
