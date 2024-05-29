import asyncio
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from dbconnection import DBConnection
from models import session, Subscription, SubscriptionType, User
from utils import get_schedule_from_subscriptions

load_dotenv()
bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()


async def send_schedule_to_subscribers():
    users = session.query(User).all()
    tomorrow = datetime.now().date() + timedelta(days=1)
    # Отправка расписания каждому подписчику

    for user in users:
        user_subs = user.subscriptions
        await bot.send_message(user.id,
                               get_schedule_from_subscriptions(user.username, user_subs, tomorrow),
                               parse_mode=ParseMode.HTML
                               )


def clear_subscriptions():
    subs = session.query(Subscription).all()
    client = DBConnection().client
    for sub in subs:
        sel = client.СоздатьСелектор()
        if sub.entity_type == SubscriptionType.GROUP:
            sel.УстановитьКоллекцию("Справочники.Группы")
            sel.ДобавитьОтбор("Совмещение", False)

        if sub.entity_type == SubscriptionType.TEACHER:
            sel.УстановитьКоллекцию("Справочники.Преподаватели")

        sel.ДобавитьОтбор("Код", sub.entity_id)

        try:
            sel.ВыгрузитьРезультат()
        except:
            session.delete(sub)
            session.commit()


# Функция для запуска рассылки в определенное время каждый день
async def scheduled_send():
    while True:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        if now.hour == 22 and now.minute == 0 and tomorrow.weekday() != 6:
            print(f"{now}: clear_subscriptions STARTED")
            clear_subscriptions()
            print(f"{now}: send_schedule_to_subscribers STARTED")
            await send_schedule_to_subscribers()


        # Ждем 1 минуту перед следующей проверкой
        await asyncio.sleep(delay=60)
