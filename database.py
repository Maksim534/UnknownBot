from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, func
from models import Base, User, Card, UserCard, EventCase, EventCaseCard
from config import DB_URL
from datetime import datetime

engine = create_async_engine(DB_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_user(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

async def register_user(user_id: int, username: str = None):
    async with async_session() as session:
        user = await get_user(user_id)
        if not user:
            user = User(user_id=user_id, username=username)
            session.add(user)
            await session.commit()
        return user

async def get_balance(user_id: int):
    user = await get_user(user_id)
    return user.balance if user else 0

async def update_balance(user_id: int, amount: int):
    async with async_session() as session:
        user = await get_user(user_id)
        if user:
            user.balance += amount
            await session.commit()

async def get_daily_case_time(user_id: int):
    user = await get_user(user_id)
    return user.daily_case_time if user else None

async def set_daily_case_time(user_id: int, time: datetime):
    async with async_session() as session:
        user = await get_user(user_id)
        if user:
            user.daily_case_time = time
            await session.commit()

async def get_user_card(user_id: int, card_id: int):
    async with async_session() as session:
        result = await session.execute(select(UserCard).where(UserCard.user_id == user_id, UserCard.card_id == card_id))
        return result.scalar_one_or_none()

async def add_card_to_user(user_id: int, card_id: int):
    async with async_session() as session:
        user_card = await get_user_card(user_id, card_id)
        if user_card:
            user_card.count += 1
        else:
            user_card = UserCard(user_id=user_id, card_id=card_id, count=1)
            session.add(user_card)
        await session.commit()

async def get_cards_by_case_type(case_type: str):
    async with async_session() as session:
        result = await session.execute(select(Card).where(Card.case_type == case_type, Card.is_event == False))
        return result.scalars().all()

async def get_random_card_by_case(case_type: str):
    cards = await get_cards_by_case_type(case_type)
    if not cards:
        return None
    return random.choice(cards)

async def get_user_cards_list(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Card, UserCard.count)
            .join(UserCard, Card.id == UserCard.card_id)
            .where(UserCard.user_id == user_id)
        )
        return result.all()

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
        event = await get_event_by_id(event_id)
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
