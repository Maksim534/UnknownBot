import asyncio
import json
from database import init_db, async_session
from models import Card

async def load_cards():
    async with async_session() as session:
        # Проверяем, есть ли уже карты
        from sqlalchemy import select
        result = await session.execute(select(Card).limit(1))
        if result.scalar_one_or_none():
            print("📦 Карты уже загружены.")
            return

        with open("data/cards.json", "r", encoding="utf-8") as f:
            cards_data = json.load(f)
        for data in cards_data:
            card = Card(
                name=data["name"],
                rarity=data["rarity"],
                image_url=data["image_url"],
                sell_price=data["sell_price"],
                case_type=data.get("case_type", "обычный"),
                is_event=data.get("is_event", False),
                description=data.get("description", "")
            )
            session.add(card)
        await session.commit()
        print(f"✅ Загружено {len(cards_data)} карт.")

async def main():
    await init_db()
    await load_cards()
    print("✅ База данных инициализирована.")

if __name__ == "__main__":
    asyncio.run(main())
