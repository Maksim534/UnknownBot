from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String, nullable=True)
    balance = Column(Integer, default=0)
    daily_case_time = Column(DateTime, nullable=True)  # последнее получение ежедневного кейса
    total_cards = Column(Integer, default=0)

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    name = Column(String)                 # имя персонажа
    rarity = Column(String)               # обычная, редкая, эпическая, легендарная, мифическая, ультралегендарная
    image_url = Column(String)            # ссылка на фото
    sell_price = Column(Integer)          # цена продажи (монеты)
    case_type = Column(String, default="обычный")  # из какого кейса (можно использовать для фильтрации)
    is_event = Column(Boolean, default=False)      # ивентовая карта?

class UserCard(Base):
    __tablename__ = "user_cards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    card_id = Column(Integer, ForeignKey("cards.id"))
    count = Column(Integer, default=1)

class EventCase(Base):
    __tablename__ = "event_cases"
    id = Column(Integer, primary_key=True)
    name = Column(String)                 # название ивента (например, "Махиру кейс")
    photo_url = Column(String)            # фото кейса
    price = Column(Integer)               # стоимость открытия (монеты)
    is_active = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    # список карт, которые участвуют в ивенте (храним в отдельной таблице или как JSON)
