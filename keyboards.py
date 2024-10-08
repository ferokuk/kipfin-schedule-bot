from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ru_weekdays, ITEMS_PER_PAGE
from models import Subscription, SubscriptionType


def create_inline_group_keyboard(current_page: int, all_groups: list) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    groups_chunks = [all_groups[i:i + ITEMS_PER_PAGE] for i in range(0, len(all_groups), ITEMS_PER_PAGE)]
    row = []
    for group in groups_chunks[current_page]:
        btn = InlineKeyboardButton(text=str(group.Наименование), callback_data=str(int(group.Код)))
        row.append(btn)
        if len(row) == 2:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    prev_btn = InlineKeyboardButton(text="⬅️Предыдущая", callback_data="prev_page_groups")
    next_btn = InlineKeyboardButton(text="Следующая➡️", callback_data="next_page_groups")
    # Добавляем кнопки навигации
    if 0 < current_page < len(groups_chunks) - 1:
        keyboard.inline_keyboard.append(
            [prev_btn, next_btn]
        )
    else:
        if current_page > 0:
            keyboard.inline_keyboard.append([prev_btn])
        if current_page < len(groups_chunks) - 1:
            keyboard.inline_keyboard.append([next_btn])
    keyboard.inline_keyboard += [[get_start_button()], [get_schedule_type_button()]]
    return keyboard


def create_inline_teacher_keyboard(current_page: int, all_teachers: list) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    groups_chunks = [all_teachers[i:i + ITEMS_PER_PAGE] for i in range(0, len(all_teachers), ITEMS_PER_PAGE)]
    for teacher in groups_chunks[current_page]:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(text=str(teacher.Наименование), callback_data=str(int(teacher.Код)))
            ]
        )
    prev_btn = InlineKeyboardButton(text="⬅️Предыдущая", callback_data="prev_page_teachers")
    next_btn = InlineKeyboardButton(text="Следующая➡️", callback_data="next_page_teachers")
    if 0 < current_page < len(groups_chunks) - 1:
        keyboard.inline_keyboard.append(
            [prev_btn, next_btn]
        )
    else:
        # Добавляем кнопки навигации
        if current_page > 0:
            keyboard.inline_keyboard.append([prev_btn])
        if current_page < len(groups_chunks) - 1:
            keyboard.inline_keyboard.append([next_btn])
    keyboard.inline_keyboard += [[get_start_button()], [get_schedule_type_button()]]
    return keyboard


def create_inline_date_keyboard(date: datetime) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=[])
    for i in range(3, -1, -1):  # Итерируемся сегодня от сегодня до сегодня - 4 дня
        current_date = date - timedelta(days=i)
        # Если день недели не воскресенье, добавляем кнопку
        if current_date.weekday() != 6:
            # Форматируем дату и день недели на русском
            date_text = current_date.strftime('%d.%m.%Y')
            day_of_week = ru_weekdays[current_date.weekday()]  # Получаем название дня недели на русском
            if current_date.day == date.day and current_date.month == date.month and current_date.year == date.year:
                button_text = f"➡️{date_text} ({day_of_week})"
            else:
                button_text = f"{date_text} ({day_of_week})"
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=button_text, callback_data=date_text)])
        # Добавляем кнопку для завтрашнего дня, если завтра не воскресенье
    tomorrow_delta = 1 if (date + timedelta(days=1)).weekday() != 6 else 2
    current_date = date + timedelta(days=tomorrow_delta)
    date_text = current_date.strftime('%d.%m.%Y')
    day_of_week = ru_weekdays[current_date.weekday()]
    button_text = f"{date_text} ({day_of_week})"
    keyboard.inline_keyboard.append([InlineKeyboardButton(text=button_text, callback_data=date_text)])
    return keyboard


def create_inline_schedule_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Преподаватель", callback_data="teacher")
            ],
            [
                InlineKeyboardButton(text="Группа", callback_data="group")
            ],
            [
                get_start_button()
            ],
        ])


def get_start_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(text="↩️ Вернуться к выбору даты", callback_data="start")


def get_schedule_type_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(text="↩️ Вернуться к выбору вида расписания", callback_data="schedule_type")


def subscribe_to_schedule(entity_id: int, entity_type: str, entity_name: str | None = None) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=f"✅ Подписаться на {entity_name if entity_name else 'расписание '}",
                                callback_data=f"sub_{entity_type}_{entity_id}")


def unsubscribe_to_schedule(entity_id: int, entity_type: str, entity_name: str | None = None) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=f"❌ Отписаться от {entity_name if entity_name else 'расписания '}",
                                callback_data=f"unsub_{entity_type}_{entity_id}")


def create_subs_handler_keyboard(subs: list[Subscription], all_teachers: list,
                                 all_groups: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                unsubscribe_to_schedule(
                sub.entity_id,
                SubscriptionType(sub.entity_type).value,
                next((item for item in all_teachers if int(item.Код) == sub.entity_id)).Наименование
                if sub.entity_type == SubscriptionType.TEACHER
                else
                next((item for item in all_groups if int(item.Код) == sub.entity_id)).Наименование
            )]
            for sub in subs
        ])


def create_nav_keyboard(entity_id: int | str | None, schedule_type: str, is_subscribed: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                unsubscribe_to_schedule(entity_id, schedule_type)
            ]
            if is_subscribed else
            [
                subscribe_to_schedule(entity_id, schedule_type)
            ],
            [
                get_start_button()
            ],
            [
                get_schedule_type_button()
            ],
            [
                InlineKeyboardButton(
                    text=f"↩️ Вернуться к выбору {'группы' if schedule_type == 'group' else 'преподавателя'}",
                    callback_data="open_teachers_nav" if schedule_type == 'teacher' else "open_groups_nav")
            ],
        ])


def create_subscriptions_keyboard(today: datetime, tomorrow: datetime) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{today.strftime('%d.%m.%Y')} ({ru_weekdays[today.weekday()]})",
                                  callback_data="show_today_subs")],
            [InlineKeyboardButton(text=f"{tomorrow.strftime('%d.%m.%Y')} ({ru_weekdays[tomorrow.weekday()]})",
                                  callback_data="show_tomorrow_subs")],
        ]
    )
