import asyncio
import os
import brom
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from dbconnection import DBConnection
import psycopg2 as pg

load_dotenv()
bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()


def on_startup():
    conn = pg.connect()


def get_schedule(group: str) -> str:
    con = DBConnection().client
    selector: brom.Селектор = con.Документы.СоставлениеРасписания.СоздатьСелектор()
    selector.Выбрать().Где("Дата", "Минимум(Дата)")
    schedule = selector.ВыгрузитьРезультат()
    res = f"""Расписане на {schedule.Дата.strftime('%d.%m.%Y')} для группы {group}"""
    for class_number in range(1, int(os.getenv("MAX_LESSONS")) + 1):
        for row in getattr(schedule, f"Пара{class_number}"):
            if row.Группа.Наименование == group:
                res += f"\n{class_number}) {row.Преподаватель} - {row.Аудитория.Наименование}"
    return res


@dp.message(CommandStart())
async def start_handler(message: Message):
    try:
        con = DBConnection().client
        selector: brom.Селектор = con.Справочники.Группы.СоздатьСелектор()
        all_groups = selector.Выбрать().ВыгрузитьРезультат()
        builder = InlineKeyboardBuilder()
        builder.adjust(5, 6)
        for group in all_groups:
            builder.button(text=group.Наименование, callback_data=f"set:{group.Наименование}")
        await message.answer("Выберите группу: ", reply_markup=builder.as_markup())
    except Exception as e:
        print(f"EXCEPTION WITH CONNECTION:\n{e}\nchat_id={message.chat.id}")
        await message.answer("Произошла ошибка\nПовторите попытку позже")
        return


@dp.message()
async def group_handler(message: Message):
    try:
        con = DBConnection().client
        selector: brom.Селектор = con.Справочники.Группы.СоздатьСелектор()
        all_groups = selector.Выбрать().ВыгрузитьРезультат()
        if message.text.upper() not in all_groups:
            await message.answer(f"""
            Группы {message.text} не существует.
            Возможно вы забыли дефис между направлением и номером?
            Правильный формат: 1ОИБАС-1222, 3ИСИП-620
            """)
            return
        await message.answer(get_schedule(message.text))

    except Exception as e:
        print(f"EXCEPTION WITH CONNECTION:\n{e}\nchat_id={message.chat.id}")
        await message.answer("Произошла ошибка\nПовторите попытку позже")
        return


async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
