import asyncio
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from models import session, TeacherSubscription, GroupSubscription
from utils import get_schedule, get_teacher_schedule

load_dotenv()
bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()


async def send_schedule_to_subscribers():
    teachers_subs = session.query(TeacherSubscription).all()
    groups_subs = session.query(GroupSubscription).all()
    tomorrow = datetime.now() + timedelta(days=1)
    # Отправка расписания каждому подписчику
    for sub in groups_subs:
        await bot.send_message(sub.user_id,
                               get_schedule(sub.group, tomorrow),
                               parse_mode=ParseMode.HTML
                               )

    for sub in teachers_subs:
        await bot.send_message(sub.user_id,
                               get_teacher_schedule(sub.teacher, tomorrow),
                               parse_mode=ParseMode.HTML
                               )


# Функция для запуска рассылки в определенное время каждый день
async def scheduled_send():
    print("scheduled_send STARTED")
    while True:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        if now.hour == 22 and now.minute == 0 and tomorrow.weekday() != 6:
            print("send_schedule_to_subscribers STARTED")
            await send_schedule_to_subscribers()

        # Ждем 1 минуту перед следующей проверкой
        await asyncio.sleep(delay=60)
