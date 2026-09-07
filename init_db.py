import asyncio
from database import init_db, async_session
from models import Card
from data.cards_data import cards  # импортируем ваш словарь
from sqlalchemy import select

async def load_cards():
    async with async_session() as session:
        # Получаем все имена карт, которые уже есть в базе
        result = await session.execute(select(Card.name))
        existing_names = {row[0] for row in result.all()}

        added = 0
        for card_id, card_data in cards.items():
            name = card_data["name"]
            if name in existing_names:
                continue  # карта уже есть — пропускаем

            card = Card(
                name=name,
                rarity=card_data["rarity"],
                image_url=card_data["image_url"],
                sell_price=card_data["sell_price"],
                case_type=card_data.get("case_type", "обычный"),
                is_event=card_data.get("is_event", False),
                description=card_data.get("description", "")
            )
            session.add(card)
            added += 1

        await session.commit()
        print(f"✅ Добавлено {added} новых карт. Всего в базе: {len(existing_names) + added}.")

async def main():
    await init_db()
    await load_cards()
    print("✅ База данных готова.")

if __name__ == "__main__":
    asyncio.run(main())
