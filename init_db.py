import asyncio
from database import init_db, async_session
from models import Card
from data.cards_data import cards
from sqlalchemy import select, update

async def load_or_update_cards():
    async with async_session() as session:
        # Получаем все существующие карты по имени
        result = await session.execute(select(Card))
        existing_cards = {card.name: card for card in result.scalars().all()}

        added = 0
        updated = 0

        for card_id, card_data in cards.items():
            name = card_data["name"]
            if name in existing_cards:
                # Карта уже есть — обновляем данные
                card = existing_cards[name]
                card.rarity = card_data["rarity"]
                card.image_url = card_data["image_url"]
                card.sell_price = card_data["sell_price"]
                card.case_type = card_data.get("case_type", "обычный")
                card.is_event = card_data.get("is_event", False)
                card.description = card_data.get("description", "")
                updated += 1
            else:
                # Новая карта — добавляем
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
        print(f"✅ Добавлено {added} новых карт, обновлено {updated} существующих.")

async def main():
    await init_db()
    await load_or_update_cards()
    print("✅ База данных синхронизирована с cards_data.py.")

if __name__ == "__main__":
    asyncio.run(main())
