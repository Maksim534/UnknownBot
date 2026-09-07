import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from models import Base, User, Card, UserCard, EventCase, EventCaseCard
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
            await session.commit()
        return user

async def get_balance(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        return user.balance if user else 0

async def update_balance(user_id: int, amount: int):
    """Обновляет баланс пользователя (исправлено)"""
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
    "ультралегендарная": 500
}

async def get_last_income_time(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        return user.last_income_time if user else datetime.now()

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
    total_per_minute = 0
    for card, count in cards:
        income_per_card = RARITY_INCOME.get(card.rarity, 0)
        total_per_minute += income_per_card * count
    return total_per_minute

async def claim_income(user_id: int):
    last_time = await get_last_income_time(user_id)
    now = datetime.now()
    diff = now - last_time
    minutes = diff.total_seconds() / 60
    if minutes < 1:
        return 0

    per_minute = await calculate_income(user_id)
    earned = per_minute * minutes
    earned = int(earned)

    if earned > 0:
        await update_balance(user_id, earned)
        await set_last_income_time(user_id, now)
    return earned

# ===== КАРТЫ =====
async def get_cards_by_case_type(case_type: str, event_only=False):
    async with async_session() as session:
        query = select(Card).where(Card.case_type == case_type, Card.is_event == event_only)
        result = await session.execute(query)
        return result.scalars().all()

async def get_random_card_by_case(case_type: str):
    cards = await get_cards_by_case_type(case_type, event_only=False)
    if not cards:
        return None
    return random.choice(cards)

async def get_all_cards():
    async with async_session() as session:
        result = await session.execute(select(Card))
        return result.scalars().all()

# ===== ПОЛЬЗОВАТЕЛЬСКИЕ КАРТЫ =====
async def get_user_card(user_id: int, card_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(UserCard).where(UserCard.user_id == user_id, UserCard.card_id == card_id)
        )
        return result.scalar_one_or_none()

async def add_card_to_user(user_id: int, card_id: int):
    async with async_session() as session:
        # Проверяем, есть ли уже такая карта у пользователя
        result = await session.execute(
            select(UserCard).where(UserCard.user_id == user_id, UserCard.card_id == card_id)
        )
        user_card = result.scalar_one_or_none()
        if user_card:
            user_card.count += 1
        else:
            user_card = UserCard(user_id=user_id, card_id=card_id, count=1)
            session.add(user_card)
        await session.commit()

# ===== ИВЕНТЫ =====
async def get_all_events():
    async with async_session() as session:
        result = await session.execute(select(EventCase))
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
    return random.choice(cards)
