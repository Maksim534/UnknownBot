import asyncio
import logging
from bot import bot, dp
from handlers import start, cases, profile, admin

async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(start.router)
    dp.include_router(cases.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
