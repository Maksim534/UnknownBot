import random
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base, User, Card, UserCard, EventCase, EventCaseCard, Promo, PromoActiv
from config import DB_URL

engine = create_async_engine(DB_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ===== ПОЛЬЗОВАТЕЛИ =====
async def get_user(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()


async def register_user(user_id: int, username: str = None):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(user_id=user_id, username=username, last_income_time=datetime.now())
            session.add(user)
        else:
            user.username = username
        await session.commit()
        return user


async def get_balance(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        return user.balance if user else 0


async def update_balance(user_id: int, amount: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.balance += amount
            await session.commit()
            return True
        return False


async def get_daily_case_time(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        return user.daily_case_time if user else None


async def set_daily_case_time(user_id: int, time: datetime):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.daily_case_time = time
            await session.commit()


# ===== ДОХОД =====
RARITY_INCOME = {
    "обычная": 1,
    "редкая": 5,
    "эпическая": 15,
    "легендарная": 50,
    "мифическая": 150,
    "ультралегендарная": 500,
}

CASE_RARITY_WEIGHTS = {
    "обычный": {
        "обычная": 100,
        "редкая": 30,
        "эпическая": 8,
        "легендарная": 2,
        "мифическая": 0.5,
        "ультралегендарная": 0.1,
    },
    "редкий": {
        "обычная": 50,
        "редкая": 100,
        "эпическая": 30,
        "легендарная": 8,
        "мифическая": 2,
        "ультралегендарная": 0.5,
    },
    "мифический": {
        "обычная": 10,
        "редкая": 30,
        "эпическая": 100,
        "легендарная": 40,
        "мифическая": 15,
        "ультралегендарная": 3,
    },
    "ультралегендарный": {
        "обычная": 2,
        "редкая": 5,
        "эпическая": 20,
        "легендарная": 80,
        "мифическая": 100,
        "ультралегендарная": 50,
    },
}


def get_weights_for_case(case_type: str):
    return CASE_RARITY_WEIGHTS.get(case_type, CASE_RARITY_WEIGHTS["обычный"])


async def get_last_income_time(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        return user.last_income_time if user and user.last_income_time else datetime.now()


async def set_last_income_time(user_id: int, time: datetime):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.last_income_time = time
            await session.commit()


async def get_user_cards_list(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Card, UserCard.count)
            .join(UserCard, Card.id == UserCard.card_id)
            .where(UserCard.user_id == user_id)
        )
        return result.all()


async def calculate_income(user_id: int):
    cards = await get_user_cards_list(user_id)
    return sum(RARITY_INCOME.get(card.rarity, 0) * count for card, count in cards)


async def claim_income(user_id: int):
    last_time = await get_last_income_time(user_id)
    now = datetime.now()
    minutes = (now - last_time).total_seconds() / 60
    if minutes < 1:
        return 0

    earned = int(await calculate_income(user_id) * minutes)
    if earned > 0:
        await update_balance(user_id, earned)
        await set_last_income_time(user_id, now)
    return earned


# ===== КАРТЫ =====
async def get_cards_by_case_type(case_type: str, event_only=False):
    async with async_session() as session:
        result = await session.execute(
            select(Card).where(Card.case_type == case_type, Card.is_event == event_only)
        )
        return result.scalars().all()


async def get_random_card_by_case(case_type: str):
    cards = await get_cards_by_case_type(case_type, event_only=False)
    if not cards:
        return None
    weights = [get_weights_for_case(case_type).get(card.rarity, 10) for card in cards]
    return random.choices(cards, weights=weights, k=1)[0]


async def get_all_cards():
    async with async_session() as session:
        result = await session.execute(select(Card).order_by(Card.id))
        return result.scalars().all()


async def get_card_by_id(card_id: int):
    async with async_session() as session:
        result = await session.execute(select(Card).where(Card.id == card_id))
        return result.scalar_one_or_none()


# ===== ПОЛЬЗОВАТЕЛЬСКИЕ КАРТЫ =====
async def get_user_card(user_id: int, card_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(UserCard).where(UserCard.user_id == user_id, UserCard.card_id == card_id)
        )
        return result.scalar_one_or_none()


async def add_card_to_user(user_id: int, card_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(UserCard).where(UserCard.user_id == user_id, UserCard.card_id == card_id)
        )
        user_card = result.scalar_one_or_none()
        if user_card:
            user_card.count += 1
        else:
            session.add(UserCard(user_id=user_id, card_id=card_id, count=1))
        await session.commit()


# ===== ИВЕНТЫ =====
async def get_all_events():
    async with async_session() as session:
        result = await session.execute(select(EventCase).order_by(EventCase.id.desc()))
        return result.scalars().all()


async def get_active_events():
    async with async_session() as session:
        result = await session.execute(
            select(EventCase).where(EventCase.is_active.is_(True)).order_by(EventCase.id.desc())
        )
        return result.scalars().all()


async def get_event_by_id(event_id: int):
    async with async_session() as session:
        result = await session.execute(select(EventCase).where(EventCase.id == event_id))
        return result.scalar_one_or_none()


async def toggle_event(event_id: int):
    async with async_session() as session:
        result = await session.execute(select(EventCase).where(EventCase.id == event_id))
        event = result.scalar_one_or_none()
        if event:
            event.is_active = not event.is_active
            await session.commit()
            return event.is_active
        return None


async def create_event(name: str, price: int, photo_url: str | None, card_ids: list[int]):
    async with async_session() as session:
        event = EventCase(name=name, price=price, photo_url=photo_url, is_active=False)
        session.add(event)
        await session.flush()
        for card_id in card_ids:
            session.add(EventCaseCard(event_id=event.id, card_id=card_id))
        await session.commit()
        return event.id


async def delete_event(event_id: int):
    async with async_session() as session:
        await session.execute(EventCaseCard.__table__.delete().where(EventCaseCard.event_id == event_id))
        result = await session.execute(select(EventCase).where(EventCase.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            return False
        await session.delete(event)
        await session.commit()
        return True


async def get_event_cards(event_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Card)
            .join(EventCaseCard, Card.id == EventCaseCard.card_id)
            .where(EventCaseCard.event_id == event_id)
        )
        return result.scalars().all()


async def get_random_event_card(event_id: int):
    cards = await get_event_cards(event_id)
    if not cards:
        return None
    weights = [get_weights_for_case("ультралегендарный").get(card.rarity, 10) for card in cards]
    return random.choices(cards, weights=weights, k=1)[0]


# ===== СТАТИСТИКА / АДМИН =====
async def get_admin_stats():
    async with async_session() as session:
        users = await session.scalar(select(func.count(User.id))) or 0
        cards = await session.scalar(select(func.count(Card.id))) or 0
        user_cards = await session.scalar(select(func.coalesce(func.sum(UserCard.count), 0))) or 0
        active_events = await session.scalar(
            select(func.count(EventCase.id)).where(EventCase.is_active.is_(True))
        ) or 0
        events = await session.scalar(select(func.count(EventCase.id))) or 0
        promos = await session.scalar(select(func.count(Promo.id))) or 0
        total_balance = await session.scalar(select(func.coalesce(func.sum(User.balance), 0))) or 0
        return {
            "users": users,
            "cards": cards,
            "user_cards": user_cards,
            "active_events": active_events,
            "events": events,
            "promos": promos,
            "total_balance": total_balance,
        }


async def get_all_user_ids():
    async with async_session() as session:
        result = await session.execute(select(User.user_id))
        return [row[0] for row in result.all() if row[0]]
