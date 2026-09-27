# create_event.py
import asyncio
from database import async_session
from models import Card, EventCase, EventCaseCard
from sqlalchemy import select

# ===== НАСТРОЙКИ ИВЕНТА =====
EVENT_NAME = "Махиру кейс"
EVENT_PRICE = 15000
EVENT_PHOTO = "https://example.com/mahiru_case.jpg"  # можно оставить None

# ===== СПИСОК ПЕРСОНАЖЕЙ =====
# Каждый персонаж: (имя, редкость, ссылка на фото, цена продажи, описание)
CARDS = [
    ("Махиру", "ультралегендарная", "https://i.ibb.co/21MnB2Dy/image.png", 200000, "Богиня света."),
    ("Аманэ Фудзимия", "ультралегендарная", "https://i.ibb.co/V0tChcfj/image.png", 150000, "Владычица тьмы."),
    ("Ицуки Акадзава", "мифическая", "https://i.ibb.co/R4hL8jMt/image.png", 50000, "Хранительница грёз."),
    ("Сайо сина", "мифическая", "https://i.ibb.co/h1ZnYtNv/image.png", 50000, "Мастер иллюзий."),
    ("Сихоко Фудзимия", "обычная", "https://i.ibb.co/nM7JQ0kN/image.png", 1000, "Милая сестра."),
    ("Сюто Фудзимия", "легендарная", "https://example.com/syuto.jpg", 1000, "Теневой воин."),
    ("Читосэ Сиракава", "редкая", "https://example.com/chitose.jpg", 300, "Искусная лучница."),
    ("Юта Кадоваки", "эпическая", "https://example.com/yuta.jpg", 800, "Маг стихий.")
]

# ========================================
# САМ СКРИПТ СОЗДАНИЯ ИВЕНТА
# ========================================
async def main():
    async with async_session() as session:
        # 1. Добавляем карты, если их нет
        card_ids = []
        for name, rarity, image_url, sell_price, description in CARDS:
            # Проверяем, есть ли уже такая карта
            result = await session.execute(select(Card).where(Card.name == name))
            card = result.scalar_one_or_none()
            if card:
                print(f"Карта '{name}' уже существует (ID: {card.id}). Использую существующую.")
                card_ids.append(card.id)
            else:
                # Создаём новую карту (is_event = True, чтобы не выпадала в обычных кейсах)
                new_card = Card(
                    name=name,
                    rarity=rarity,
                    image_url=image_url,
                    sell_price=sell_price,
                    case_type="обычный",  # неважно, т.к. is_event = True
                    is_event=True,
                    description=description
                )
                session.add(new_card)
                await session.flush()  # чтобы получить ID
                card_ids.append(new_card.id)
                print(f"Карта '{name}' добавлена (ID: {new_card.id}).")

        # 2. Создаём ивент
        event = EventCase(
            name=EVENT_NAME,
            photo_url=EVENT_PHOTO,
            price=EVENT_PRICE,
            is_active=False  # по умолчанию выключен
        )
        session.add(event)
        await session.flush()
        event_id = event.id
        print(f"Ивент '{EVENT_NAME}' создан с ID: {event_id}")

        # 3. Привязываем карты к ивенту
        for card_id in card_ids:
            event_card = EventCaseCard(event_id=event_id, card_id=card_id)
            session.add(event_card)

        await session.commit()
        print(f"✅ Ивент '{EVENT_NAME}' успешно создан! В нём {len(card_ids)} карт.")
        print(f"Теперь вы можете включить его в админ-панели (/admin -> Ивенты).")

if __name__ == "__main__":
    asyncio.run(main())
