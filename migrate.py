# migrate.py
import asyncio
from database import engine
from models import Base, Promo, PromoActiv

async def migrate():
    async with engine.begin() as conn:
        # Создаём только таблицы promo и promo_activ
        await conn.run_sync(Base.metadata.create_all, tables=[Promo.__table__, PromoActiv.__table__])
    print("✅ Таблицы promo и promo_activ созданы.")

if __name__ == "__main__":
    asyncio.run(migrate())
