from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String, nullable=True)
    balance = Column(Integer, default=0)
    daily_case_time = Column(DateTime, nullable=True)
    last_income_time = Column(DateTime, nullable=True)  # время последнего сбора дохода

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    rarity = Column(String)
    image_url = Column(String)
    sell_price = Column(Integer)
    case_type = Column(String, default="обычный")
    is_event = Column(Boolean, default=False)
    description = Column(String, nullable=True)

class UserCard(Base):
    __tablename__ = "user_cards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    card_id = Column(Integer, ForeignKey("cards.id"))
    count = Column(Integer, default=1)

class EventCase(Base):
    __tablename__ = "event_cases"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    photo_url = Column(String, nullable=True)
    price = Column(Integer)
    is_active = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

class EventCaseCard(Base):
    __tablename__ = "event_case_cards"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("event_cases.id"))
    card_id = Column(Integer, ForeignKey("cards.id"))
