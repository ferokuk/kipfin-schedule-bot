import asyncio
import os
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv
from config import ITEMS_PER_PAGE
import psycopg2 as pg
from keyboards import create_inline_group_keyboard, create_inline_date_keyboard, create_inline_schedule_type_keyboard, \
    create_inline_teacher_keyboard, get_nav_keyboard
from models import Base, engine, session, User, TeacherSubscription, GroupSubscription
from states import UserState
from utils import get_schedule, get_all_groups, check_schedule_by_date, get_all_teachers, get_teacher_schedule, \
    get_group_by_id, get_teacher_by_id, get_teacher_id_by_name

load_dotenv()
bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()
current_page_dict = dict()


@dp.callback_query(lambda query: query.data in ["prev_page_groups", "next_page_groups"])
async def navigation_groups(query: types.CallbackQuery, state: FSMContext):
    current_page = current_page_dict.get(query.message.chat.id, 0)
    data = await state.get_data()
    chosen_date = data.get("date")
    groups = data.get("all_groups")
    total_pages = len(groups) // ITEMS_PER_PAGE + 1
    if query.data == "prev_page":
        current_page = max(current_page - 1, 0)
    elif query.data == "next_page":
        current_page = min(current_page + 1, total_pages - 1)
    current_page_dict[query.message.chat.id] = current_page
    # Обновляем клавиатуру с помощью новой страницы

    await bot.edit_message_text(f"Вы указали дату {chosen_date}. \n"
                                f"Теперь выберите группу или введите её название в соответствии с названием в ЭлЖур. \n"
                                f"Текущая страница: <b>{current_page + 1} из {total_pages}</b>",
                                parse_mode=ParseMode.HTML,
                                chat_id=query.message.chat.id,
                                message_id=query.message.message_id)
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        reply_markup=create_inline_group_keyboard(current_page, groups))


@dp.callback_query(lambda query: query.data in ["prev_page_teachers", "next_page_teachers"])
async def navigation_teachers(query: types.CallbackQuery, state: FSMContext):
    current_page = current_page_dict.get(query.message.chat.id, 0)
    data = await state.get_data()
    chosen_date = data.get("date")
    teachers = data.get("all_teachers")
    total_pages = len(teachers) // ITEMS_PER_PAGE + 1
    if query.data == "prev_page_teachers":
        current_page = max(current_page - 1, 0)
    elif query.data == "next_page_teachers":
        current_page = min(current_page + 1, total_pages - 1)
    current_page_dict[query.message.chat.id] = current_page
    # Обновляем клавиатуру с помощью новой страницы
    await bot.edit_message_text(f"Вы указали дату {chosen_date}. \n"
                                f"Теперь выберите преподавателя или введите его ФИО. \n"
                                f"Текущая страница: <b>{current_page + 1} из {total_pages}</b>",
                                parse_mode=ParseMode.HTML,
                                chat_id=query.message.chat.id,
                                message_id=query.message.message_id)
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        reply_markup=create_inline_teacher_keyboard(current_page, teachers))


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserState.date)
    current_page_dict[message.chat.id] = 0
    if session.query(User).filter_by(id=message.from_user.id).first() is None:
        new_user = User(id=message.from_user.id, username=message.from_user.username)
        session.add(new_user)
        session.commit()
    await state.update_data(all_groups=get_all_groups())
    await message.answer("Выберите дату или напишите её в формате дд.мм.гггг: ",
                         reply_markup=create_inline_date_keyboard(datetime.now()))


@dp.callback_query(lambda query: query.data == "start")
async def back_to_start(query: types.CallbackQuery, state: FSMContext):
    await start_handler(query.message, state)


@dp.callback_query(UserState.schedule_type)
async def process_schedule_type(query: types.CallbackQuery, state: FSMContext):
    schedule_type = query.data
    if schedule_type == "teacher":
        await state.set_state(UserState.teacher)
        teachers = get_all_teachers()
        data = await state.update_data(all_teachers=teachers, schedule_type=schedule_type, teacher=schedule_type)
        total_pages = len(teachers) // ITEMS_PER_PAGE + 1
        keyboard = create_inline_teacher_keyboard(0, teachers)
        chosen_date = data.get("date")
        await query.message.answer(f"Вы указали дату {chosen_date}. \n"
                                   f"Теперь выберите преподавателя или введите его ФИО. \n"
                                   f"Текущая страница: <b>1 из {total_pages}</b>",
                                   reply_markup=keyboard,
                                   parse_mode=ParseMode.HTML)

    if schedule_type == "group":
        await state.set_state(UserState.group)
        groups = get_all_groups()
        data = await state.update_data(all_groups=groups, schedule_type=schedule_type, group=schedule_type)
        chosen_date = data.get("date")
        total_pages = len(groups) // ITEMS_PER_PAGE + 1
        keyboard = create_inline_group_keyboard(0, groups)
        await query.message.answer(f"Вы указали дату {chosen_date}. \n"
                                   f"Теперь выберите группу или введите её название в соответствии с названием в ЭлЖур. \n"
                                   f"Текущая страница: <b>1 из {total_pages}</b>",
                                   reply_markup=keyboard,
                                   parse_mode=ParseMode.HTML)


@dp.callback_query(lambda query: query.data == "schedule_type")
async def back_to_schedule_type(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chosen_date = data.get("date")
    await state.set_state(UserState.schedule_type)
    await query.message.answer(f"Вы указали дату {chosen_date}. \n"
                               f"Выберите вид расписания: \n",
                               reply_markup=create_inline_schedule_type_keyboard()
                               )


async def process_date_input(chosen_date: str, state: FSMContext, message_or_query):
    date_pattern = re.compile(r'\d{2}\.\d{2}\.\d{4}')  # Паттерн для поиска даты формата dd.mm.yyyy
    if not date_pattern.match(chosen_date):
        await message_or_query.answer(
            f"Некорректный формат даты. Пожалуйста, укажите дату в формате дд.мм.гггг. \n"
            f"Например: {datetime.now().strftime('%d.%m.%Y')}",
            reply_markup=create_inline_date_keyboard(datetime.now()))
        return

    if not check_schedule_by_date(datetime.strptime(chosen_date, "%d.%m.%Y")):
        await message_or_query.answer(f"Расписания на выбранную дату нет")
        await start_handler(message_or_query, state)
        return

    data = await state.update_data(date=chosen_date)
    await state.set_state(UserState.schedule_type)
    await message_or_query.answer(f"Вы указали дату {chosen_date}. \n"
                                  f"Выберите вид расписания: \n",
                                  reply_markup=create_inline_schedule_type_keyboard()
                                  )


@dp.callback_query(UserState.date)
async def process_date(query: types.CallbackQuery, state: FSMContext):
    await process_date_input(query.data, state, query.message)


@dp.message(UserState.date)
async def process_date_text(message: Message, state: FSMContext):
    await process_date_input(message.text.strip(), state, message)


async def process_group_input(group_input: str, state: FSMContext, message_or_query):
    try:
        current_page = current_page_dict.get(message_or_query.chat.id, 0)
        group = group_input.strip().upper()
        data = await state.get_data()
        groups = data.get("all_groups", [])
        if not any([group in {d.get("name"), d.get("id")} for d in groups]):
            await message_or_query.answer(f"Группы {group} не существует. \n"
                                          f"Возможно вы забыли дефис между направлением и номером? \n"
                                          f"Правильный формат: 1ОИБАС-1222, 3ИСИП-620",
                                          reply_markup=create_inline_group_keyboard(current_page, groups))
            return
        data = await state.update_data(group=group)
        date = datetime.strptime(data["date"], "%d.%m.%Y")
        group = get_group_by_id(int(data["group"])) if data["group"].isnumeric() else data["group"]
        await message_or_query.answer(get_schedule(group=group, date=date),
                                      parse_mode=ParseMode.HTML,
                                      reply_markup=get_nav_keyboard(group))
        await state.set_state(UserState.end)
    except Exception as e:
        print(f"ОШИБКА ПРИ ПОЛУЧЕНИИ РАСПИСАНИЯ: {e}")
        await message_or_query.answer("Произошла ошибка\nПовторите попытку позже")


async def process_teacher_input(teacher_input: str, state: FSMContext, message_or_query):
    try:
        current_page = current_page_dict.get(message_or_query.chat.id, 0)
        teacher = teacher_input.strip()
        data = await state.get_data()
        teachers = data.get("all_teachers", [])
        if not any(teacher in {d.get("id"), d.get("name")} for d in teachers):
            await message_or_query.answer(f"Преподавателя {teacher} не существует. \n",
                                          reply_markup=create_inline_teacher_keyboard(current_page, teachers))
            return
        data = await state.update_data(teacher=teacher)
        date = datetime.strptime(data["date"], "%d.%m.%Y")
        teacher = get_teacher_by_id(int(data["teacher"])) if data["teacher"].isnumeric() else data["teacher"]
        teacher_id = data["teacher"] if data["teacher"].isnumeric() else get_teacher_id_by_name(data["teacher"])
        await message_or_query.answer(
            get_teacher_schedule(teacher_full_name=teacher, date=date),
            parse_mode=ParseMode.HTML, reply_markup=get_nav_keyboard(teacher_id))
        await state.set_state(UserState.end)
    except Exception as e:
        print(f"ОШИБКА ПРИ ПОЛУЧЕНИИ РАСПИСАНИЯ: {e}")
        await message_or_query.answer("Произошла ошибка\nПовторите попытку позже")


@dp.callback_query(UserState.group)
async def process_group(query: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.update_data(group=query.data)
        await process_group_input(query.data, state, query.message)
    except Exception as e:
        print(f"ОШИБКА ПРИ ПОЛУЧЕНИИ РАСПИСАНИЯ: {e}")
        await query.message.answer("Произошла ошибка\nПовторите попытку позже")


@dp.message(UserState.group)
async def process_group_text(message: Message, state: FSMContext):
    await process_group_input(message.text, state, message)


@dp.callback_query(UserState.teacher)
async def process_teacher(query: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.update_data(teacher=query.data)
        await process_teacher_input(query.data, state, query.message)
    except Exception as e:
        print(f"ОШИБКА ПРИ ПОЛУЧЕНИИ РАСПИСАНИЯ: {e}")
        await query.message.answer("Произошла ошибка\nПовторите попытку позже")


@dp.message(UserState.teacher)
async def process_teacher_text(message: Message, state: FSMContext):
    await process_teacher_input(message.text, state, message)


@dp.callback_query(UserState.end, F.data.startswith("sub_"))
async def subscribe_callback_handler(query: types.CallbackQuery):
    entity = query.data.split("_")[1]
    if entity.isnumeric():
        data = get_teacher_by_id(int(entity))
        new_sub = TeacherSubscription(user_id=query.message.chat.id, teacher=data)
    else:
        data = entity
        new_sub = GroupSubscription(user_id=query.message.chat.id, group=data)
    session.add(new_sub)
    session.commit()


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Bot started")
    asyncio.run(main())
