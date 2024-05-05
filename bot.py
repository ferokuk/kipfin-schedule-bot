import asyncio
import os
from datetime import datetime, timedelta

import aiogram.filters
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv

from config import ITEMS_PER_PAGE, HELP_TEXT
from keyboards import create_inline_group_keyboard, create_inline_date_keyboard, create_inline_schedule_type_keyboard, \
    create_inline_teacher_keyboard, create_nav_keyboard, create_subscriptions_keyboard
from models import Base, engine, session, User, TeacherSubscription, GroupSubscription
from schedule_sender import scheduled_send
from states import UserState
from utils import get_schedule, get_all_groups, check_schedule_by_date, get_all_teachers, get_teacher_schedule, \
    get_group_by_id, get_teacher_by_id, get_schedule_from_subscriptions

load_dotenv()
bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()
current_page_dict = dict()


@dp.callback_query(F.data.startswith("sub_"))
async def subscribe_callback_handler(query: types.CallbackQuery, state: FSMContext):
    entity = query.data.split("_")[1]
    if entity.isnumeric():
        data = get_teacher_by_id(int(entity))
        new_sub = TeacherSubscription(user_id=query.message.chat.id, teacher=data)
    else:
        data = entity
        new_sub = GroupSubscription(user_id=query.message.chat.id, group=data)
    session.add(new_sub)
    session.commit()
    data = await state.get_data()
    schedule_type = data.get("schedule_type")
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        reply_markup=create_nav_keyboard(entity, schedule_type, False))


@dp.callback_query(F.data.startswith("unsub_"))
async def unsubscribe_callback_handler(query: types.CallbackQuery, state: FSMContext):
    entity = query.data.split("_")[1]
    if entity.isnumeric():
        teacher = get_teacher_by_id(int(entity))
        sub = session.query(TeacherSubscription).filter_by(user_id=query.message.chat.id, teacher=teacher).first()
    else:
        sub = session.query(GroupSubscription).filter_by(user_id=query.message.chat.id, group=entity).first()
    session.delete(sub)
    session.commit()
    data = await state.get_data()
    schedule_type = data.get("schedule_type")
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        reply_markup=create_nav_keyboard(entity, schedule_type, True))


@dp.callback_query(lambda query: query.data in ["prev_page_groups", "next_page_groups", "open_groups_nav"])
async def navigation_groups(query: types.CallbackQuery, state: FSMContext):
    current_page = current_page_dict.get(query.message.chat.id, 0)
    data = await state.get_data()
    chosen_date = data.get("date")
    groups = data.get("all_groups", [])
    if not groups:
        return
    total_pages = len(groups) // ITEMS_PER_PAGE + 1
    if query.data == "prev_page_groups":
        current_page = max(current_page - 1, 0)
    elif query.data == "next_page_groups":
        current_page = min(current_page + 1, total_pages - 1)
    current_page_dict[query.message.chat.id] = current_page
    # Обновляем клавиатуру с помощью новой страницы

    await bot.edit_message_text(f"Вы указали дату {chosen_date}. \n"
                                f"Теперь выберите группу \n"
                                f"Текущая страница: <b>{current_page + 1} из {total_pages}</b>",
                                parse_mode=ParseMode.HTML,
                                chat_id=query.message.chat.id,
                                message_id=query.message.message_id)
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        reply_markup=create_inline_group_keyboard(current_page, groups))


@dp.callback_query(lambda query: query.data in ["prev_page_teachers", "next_page_teachers", "open_teachers_nav"])
async def navigation_teachers(query: types.CallbackQuery, state: FSMContext):
    current_page = current_page_dict.get(query.message.chat.id, 0)
    data = await state.get_data()
    chosen_date = data.get("date")
    teachers = data.get("all_teachers", [])
    if not teachers:
        return
    total_pages = len(teachers) // ITEMS_PER_PAGE + 1
    if query.data == "prev_page_teachers":
        current_page = max(current_page - 1, 0)
    elif query.data == "next_page_teachers":
        current_page = min(current_page + 1, total_pages - 1)
    current_page_dict[query.message.chat.id] = current_page
    # Обновляем клавиатуру с помощью новой страницы
    await bot.edit_message_text(f"Вы указали дату {chosen_date}. \n"
                                f"Теперь выберите преподавателя \n"
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
    user = session.query(User).filter_by(id=message.chat.id).first()
    if user is None:
        new_user = User(id=message.chat.id, username=message.from_user.username)
        session.add(new_user)
        session.commit()
    else:
        user.username = message.from_user.username
        session.add(user)
        session.commit()
    await message.answer("Выберите дату: ",
                         reply_markup=create_inline_date_keyboard(datetime.now()))


@dp.message(aiogram.filters.Command(commands=["info"]))
async def help_handler(message: Message):
    await message.answer(HELP_TEXT, parse_mode=ParseMode.HTML)


@dp.message(aiogram.filters.Command(commands=["subscriptions"]))
async def subscriptions_handler(message: Message):
    teachers_subs = session.query(TeacherSubscription).filter_by(user_id=message.chat.id).all()
    groups_subs = session.query(GroupSubscription).filter_by(user_id=message.chat.id).all()
    tomorrow_delta = 1 if (datetime.now() + timedelta(days=1)).weekday() != 6 else 2
    today_date = datetime.now()
    tomorrow_date = datetime.now() + timedelta(days=tomorrow_delta)

    # если сегодня воскресенье
    if today_date.weekday() == 6:
        res = get_schedule_from_subscriptions(
            message.from_user.username,
            teachers_subs,
            groups_subs,
            tomorrow_date,
        )
        # без клавиатуры, тк есть расписание только на завтра
        await message.answer(res,
                             parse_mode=ParseMode.HTML,
                             )
        return

    res = get_schedule_from_subscriptions(
        message.from_user.username,
        teachers_subs,
        groups_subs,
        tomorrow_date,
    )
    await message.answer(res,
                         parse_mode=ParseMode.HTML,
                         reply_markup=create_subscriptions_keyboard(today_date, tomorrow_date)
                         )


@dp.callback_query(F.data.in_(["show_tomorrow_subs", "show_today_subs"]))
async def keyboard_subscriptions_handler(query: types.CallbackQuery):
    teachers_subs = session.query(TeacherSubscription).filter_by(user_id=query.message.chat.id).all()
    groups_subs = session.query(GroupSubscription).filter_by(user_id=query.message.chat.id).all()
    tomorrow_delta = 1 if (datetime.now() + timedelta(days=1)).weekday() != 6 else 2
    tomorrow_date = datetime.now() + timedelta(days=tomorrow_delta)
    today_date = datetime.now()
    if query.data == "show_tomorrow_subs":
        date = tomorrow_date
    else:
        date = today_date
    res = get_schedule_from_subscriptions(
        query.message.chat.username,
        teachers_subs,
        groups_subs,
        date,
    )
    await bot.edit_message_text(res,
                                chat_id=query.message.chat.id,
                                message_id=query.message.message_id,
                                parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        reply_markup=create_subscriptions_keyboard(today_date, tomorrow_date))


@dp.callback_query(lambda query: query.data == "start")
async def back_to_start(query: types.CallbackQuery, state: FSMContext):
    current_page_dict[query.message.chat.id] = 0
    await state.clear()
    await state.set_state(UserState.date)
    await bot.edit_message_text("Выберите дату: ",
                                chat_id=query.message.chat.id,
                                message_id=query.message.message_id)
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        reply_markup=create_inline_date_keyboard(datetime.now()))


@dp.callback_query(UserState.schedule_type)
async def process_schedule_type(query: types.CallbackQuery, state: FSMContext):
    schedule_type = query.data
    if schedule_type == "teacher":
        await state.set_state(UserState.teacher)
        teachers = get_all_teachers()
        data = await state.update_data(all_teachers=teachers, schedule_type=schedule_type, teacher=schedule_type)
        total_pages = len(teachers) // ITEMS_PER_PAGE + 1
        keyboard = create_inline_teacher_keyboard(current_page_dict.get(query.message.chat.id, 0), teachers)
        chosen_date = data.get("date")
        await bot.edit_message_text(f"Вы указали дату {chosen_date}. \n"
                                    f"Теперь выберите преподавателя \n"
                                    f"Текущая страница: <b>1 из {total_pages}</b>",
                                    parse_mode=ParseMode.HTML,
                                    chat_id=query.message.chat.id,
                                    message_id=query.message.message_id)
        await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=keyboard, )

    if schedule_type == "group":
        await state.set_state(UserState.group)
        groups = get_all_groups()
        data = await state.update_data(all_groups=groups, schedule_type=schedule_type, group=schedule_type)
        chosen_date = data.get("date")
        total_pages = len(groups) // ITEMS_PER_PAGE + 1
        keyboard = create_inline_group_keyboard(current_page_dict.get(query.message.chat.id, 0), groups)
        await bot.edit_message_text(f"Вы указали дату {chosen_date}. \n"
                                    f"Теперь выберите группу \n"
                                    f"Текущая страница: <b>1 из {total_pages}</b>",
                                    parse_mode=ParseMode.HTML,
                                    chat_id=query.message.chat.id,
                                    message_id=query.message.message_id)
        await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=keyboard, )


@dp.callback_query(lambda query: query.data == "schedule_type")
async def back_to_schedule_type(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chosen_date = data.get("date")
    await state.set_state(UserState.schedule_type)
    await bot.edit_message_text(f"Вы указали дату {chosen_date}. \n"
                                f"Выберите вид расписания: \n",
                                chat_id=query.message.chat.id,
                                message_id=query.message.message_id
                                )
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        reply_markup=create_inline_schedule_type_keyboard())


@dp.callback_query(UserState.date)
async def process_date(query: types.CallbackQuery, state: FSMContext):
    chosen_date = query.data
    if not check_schedule_by_date(datetime.strptime(chosen_date, "%d.%m.%Y")):
        await bot.edit_message_text(
            f"<b>Расписания на выбранную дату нет.</b>\nВыберите дату: ",
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            parse_mode=ParseMode.HTML)
        await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=create_inline_date_keyboard(datetime.now()))

        return

    data = await state.update_data(date=chosen_date)
    await state.set_state(UserState.schedule_type)
    await bot.edit_message_text(f"Вы указали дату {chosen_date}. \n"
                                f"Выберите вид расписания: \n",
                                chat_id=query.message.chat.id,
                                message_id=query.message.message_id
                                )
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        reply_markup=create_inline_schedule_type_keyboard())


@dp.callback_query(UserState.group)
async def process_group(query: types.CallbackQuery, state: FSMContext):
    try:
        current_page = current_page_dict.get(query.message.chat.id, 0)
        group = query.data
        data = await state.get_data()
        groups = data.get("all_groups", [])
        if not any([group in {d.get("name"), d.get("id")} for d in groups]):
            await query.message.answer(f"Группы {group} не существует. \n"
                                       f"Возможно вы забыли дефис между направлением и номером? \n"
                                       f"Правильный формат: 1ОИБАС-1222, 3ИСИП-620",
                                       reply_markup=create_inline_group_keyboard(current_page, groups))
            return
        data = await state.update_data(group=group)
        date = datetime.strptime(data["date"], "%d.%m.%Y")
        group = get_group_by_id(int(data["group"])) if data["group"].isnumeric() else data["group"]
        await bot.edit_message_text(get_schedule(group=group, date=date),
                                    parse_mode=ParseMode.HTML,
                                    chat_id=query.message.chat.id,
                                    message_id=query.message.message_id
                                    )
        is_subscribe = session.query(GroupSubscription).filter_by(user_id=query.message.chat.id,
                                                                  group=group).first() is None

        await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=create_nav_keyboard(group, "group", is_subscribe), )
    except Exception as e:
        print(f"ОШИБКА ПРИ ПОЛУЧЕНИИ РАСПИСАНИЯ: {e}")
        await query.message.answer("Произошла ошибка\nПовторите попытку позже")


@dp.callback_query(UserState.teacher)
async def process_teacher(query: types.CallbackQuery, state: FSMContext):
    try:
        current_page = current_page_dict.get(query.message.chat.id, 0)
        teacher = query.data
        data = await state.get_data()
        teachers = data.get("all_teachers", [])
        if not any(teacher in {d.get("id"), d.get("name")} for d in teachers):
            await query.message.answer(f"Преподавателя {teacher} не существует. \n",
                                       reply_markup=create_inline_teacher_keyboard(current_page, teachers))
            return
        data = await state.update_data(teacher=teacher)
        date = datetime.strptime(data["date"], "%d.%m.%Y")
        teacher = get_teacher_by_id(int(data["teacher"]))
        teacher_id = data["teacher"]
        await bot.edit_message_text(get_teacher_schedule(teacher_full_name=teacher, date=date),
                                    parse_mode=ParseMode.HTML,
                                    chat_id=query.message.chat.id,
                                    message_id=query.message.message_id
                                    )
        is_subscribe = session.query(TeacherSubscription).filter_by(user_id=query.message.chat.id,
                                                                    teacher=teacher).first() is None
        await bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=create_nav_keyboard(teacher_id, "teacher", is_subscribe), )

    except Exception as e:
        print(f"ОШИБКА ПРИ ПОЛУЧЕНИИ РАСПИСАНИЯ: {e}")
        await query.message.answer("Произошла ошибка\nПовторите попытку позже")


async def main() -> None:
    print("main STARTED")
    main_bot = asyncio.create_task(dp.start_polling(bot))
    await scheduled_send()
    await main_bot
    commands = [
        types.BotCommand(command="/start", description="Начать"),
        types.BotCommand(command="/info", description="Информация"),
        types.BotCommand(command="/subscriptions", description="Мои подписки"),
    ]
    await bot.set_my_commands(commands)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    asyncio.run(main())
