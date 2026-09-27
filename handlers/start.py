from aiogram import types, Router, F
from aiogram.filters import Command
from keyboards.inline import main_menu_keyboard
from database import register_user, claim_income, get_balance

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await register_user(message.from_user.id, message.from_user.username)
    text = (
        "🎴 <b>Добро пожаловать в Anime Card Collector!</b>\n\n"
        "Собирай персонажей, открывай кейсы и превращай коллекцию в источник монет. 🪙\n\n"
        "🔥 <b>Тебя ждёт:</b>\n"
        "• 📦 кейсы разных уровней\n"
        "• 🎴 коллекция карт\n"
        "• 🎉 временные ивенты\n"
        "• 💸 пассивный доход\n"
        "• 🎟️ промокоды и бонусы\n\n"
        "Выбирай раздел ниже и начинай собирать коллекцию 👇"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "❓ <b>Помощь</b>\n\n"
        "📦 Открывай кейсы → получай карты.\n"
        "🎴 Дубликаты дают компенсацию.\n"
        "💸 Карты постепенно приносят пассивный доход.\n"
        "🎉 Ивенты содержат отдельные наборы карт.\n"
        "🎟️ Промокоды вводятся как <code>промо КОД</code>.\n\n"
        "Приятной игры! ✨",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "show_balance")
async def show_balance(callback: types.CallbackQuery):
    balance = await get_balance(callback.from_user.id)
    await callback.message.edit_text(
        "💰 <b>Твой баланс</b>\n\n"
        f"У тебя <b>{balance:,} 🪙</b>.".replace(",", " "),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "claim_income")
async def claim_income_callback(callback: types.CallbackQuery):
    earned = await claim_income(callback.from_user.id)
    balance = await get_balance(callback.from_user.id)
    if earned == 0:
        text = "⏳ <b>Пока нечего забирать.</b>\n\nКарты ещё не успели накопить новый доход."
    else:
        text = (
            "💸 <b>Доход получен!</b>\n\n"
            f"+<b>{earned:,} 🪙</b> за время отсутствия.\n"
            f"Текущий баланс: <b>{balance:,} 🪙</b>".replace(",", " ")
        )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())
    await callback.answer()
