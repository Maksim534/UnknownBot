import asyncio
import logging
from bot import bot, dp
from handlers import start, cases, profile, admin, promo
from init_db import load_or_update_cards
from database import init_db

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()                     # <-- создать таблицы
    await load_or_update_cards()        # <-- загрузить карты
    dp.include_router(start.router)
    dp.include_router(promo.router)
    dp.include_router(cases.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)
    await dp.start_polling(bot)
