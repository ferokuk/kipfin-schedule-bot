import logging
import os

from dotenv import load_dotenv
from sqlalchemy import String, Column, Integer, BigInteger, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

load_dotenv()
Base = declarative_base()
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String, unique=True)

    # Связь с подписками на рассылки для групп
    group_subscriptions = relationship('GroupSubscription', back_populates='user')

    # Связь с подписками на рассылки для преподавателей
    teacher_subscriptions = relationship('TeacherSubscription', back_populates='user')

# Модель для подписок на рассылки для групп
class GroupSubscription(Base):
    __tablename__ = 'group_subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    group = Column(String)

    user = relationship('User', back_populates='group_subscriptions')

# Модель для подписок на рассылки для преподавателей
class TeacherSubscription(Base):
    __tablename__ = 'teacher_subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    teacher = Column(String)

    user = relationship('User', back_populates='teacher_subscriptions')


username = os.getenv("POSTGRES_USERNAME")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")
dbname = os.getenv("POSTGRES_DBNAME")

engine = create_engine(f'postgresql://{username}:{password}@{host}:{port}/{dbname}', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

