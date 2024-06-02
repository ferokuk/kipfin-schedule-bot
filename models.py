import enum
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import String, Column, Integer, BigInteger, ForeignKey, create_engine, Enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

load_dotenv()
Base = declarative_base()
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)


class SubscriptionType(enum.Enum):
    TEACHER = "teacher"
    GROUP = "group"


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String)

    # Связь с подписками на рассылки для групп
    subscriptions = relationship('Subscription', back_populates='user')

    # Связь с подписками на рассылки для преподавателей


# Модель для подписок на рассылки для групп
class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    entity_id = Column(Integer, nullable=False)
    entity_type = Column(Enum(SubscriptionType, name="entity_type"), nullable=False)

    user = relationship('User', back_populates='subscriptions')


username = os.getenv("POSTGRES_USERNAME")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")
dbname = os.getenv("POSTGRES_DBNAME")

engine = create_engine(f'postgresql://{username}:{password}@{host}:{port}/{dbname}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
