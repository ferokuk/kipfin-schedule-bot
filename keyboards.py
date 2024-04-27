from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ru_weekdays, ITEMS_PER_PAGE


def create_inline_group_keyboard(current_page: int, all_groups: list[dict]) -> InlineKeyboardMarkup:
    # all_groups = get_all_groups()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[get_start_button()], [get_schedule_type_button()]])
    groups_chunks = [all_groups[i:i + ITEMS_PER_PAGE] for i in range(0, len(all_groups), ITEMS_PER_PAGE)]
    for group in groups_chunks[current_page]:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=group["name"], callback_data=group["id"])])
    # Добавляем кнопки навигации
    if current_page > 0:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="prev_page_groups")])
    if current_page < len(groups_chunks) - 1:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Вперёд", callback_data="next_page_groups")])

    return keyboard


def create_inline_teacher_keyboard(current_page: int, all_teachers: list[dict]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[get_start_button()], [get_schedule_type_button()]])
    groups_chunks = [all_teachers[i:i + ITEMS_PER_PAGE] for i in range(0, len(all_teachers), ITEMS_PER_PAGE)]
    for teacher in groups_chunks[current_page]:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=teacher["name"], callback_data=teacher["id"])])
    # Добавляем кнопки навигации
    if current_page > 0:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="prev_page_teachers")])
    if current_page < len(groups_chunks) - 1:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Вперёд", callback_data="next_page_teachers")])

    return keyboard


def create_inline_date_keyboard(date: datetime):
    keyboard = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=[])
    for i in range(4, -1, -1):  # Итерируемся сегодня от сегодня до сегодня - 4 дня
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
    tomorrow = date + timedelta(days=1)
    if tomorrow.weekday() != 6:
        tomorrow_text = tomorrow.strftime('%d.%m.%Y')
        tomorrow_day_of_week = ru_weekdays[tomorrow.weekday()]
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=f"{tomorrow_text} ({tomorrow_day_of_week})", callback_data=tomorrow_text)])
    return keyboard


def create_inline_schedule_type_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                get_start_button()
            ],
            [
                InlineKeyboardButton(text="Преподаватель", callback_data="teacher")
            ],
            [
                InlineKeyboardButton(text="Группа", callback_data="group")
            ]
        ])


def get_start_button():
    return InlineKeyboardButton(text="Вернуться к выбору даты", callback_data="start")


def get_schedule_type_button():
    return InlineKeyboardButton(text="Вернуться к выбору вида расписания", callback_data="schedule_type")


def subscribe_to_schedule(entity: str):
    return InlineKeyboardButton(text="Подписаться на расписание", callback_data=f"sub_{entity}")



def get_nav_keyboard(entity: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [get_start_button()],
        [get_schedule_type_button()],
        [subscribe_to_schedule(entity)]
        # [InlineKeyboardButton(text=text, callback_data=callback)] не работает
    ])
