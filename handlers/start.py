from aiogram import types, Router
from aiogram.filters import Command
from keyboards.inline import main_menu_keyboard
from database import register_user

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
        "• 🎉 Участвовать в ивентах с эксклюзивными картами\n\n"
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
        "💰 <b>Как заработать монеты:</b>\n"
        "• Продажа карт (скоро)\n"
        "• Компенсация за дубликаты\n"
        "• Участие в ивентах и квестах (скоро)\n\n"
        "Если возникнут вопросы, пиши разработчику: @dev"
    )
    await message.answer(text, parse_mode="HTML")
