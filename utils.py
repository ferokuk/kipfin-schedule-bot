from datetime import datetime

import brom

from dbconnection import DBConnection
from models import Subscription, SubscriptionType


def get_all_groups() -> list:
    con = DBConnection().client
    selector: brom.Селектор = con.Справочники.Группы.СоздатьСелектор()
    selector.ДобавитьОтбор("Совмещение", False)
    selector.ДобавитьОтбор("ПометкаУдаления", False)
    selector.ДобавитьСортировку("Курс")
    selector.ДобавитьСортировку("Направление")
    selector.ДобавитьСортировку("НомерГруппы")
    return selector.Выбрать().ВыгрузитьРезультат()


def get_all_teachers() -> list:
    con = DBConnection().client
    selector: brom.Селектор = con.Справочники.Преподаватели.СоздатьСелектор()
    selector.ДобавитьОтбор("ПометкаУдаления", False)
    selector.ДобавитьСортировку("Наименование")
    return selector.Выбрать().ВыгрузитьРезультат()


def get_schedule(group: str, schedule: brom.ДокументСсылка, date: datetime = datetime.now()) -> str:
    header = f"<b>{group} — {schedule.Дата.strftime('%d.%m.%Y')}:</b>"
    res = f""""""
    for class_number in range(1, 8):
        current_class_schedule = "".join([f"\n<i>{row.Преподаватель}</i> — {row.Аудитория}"
                                          for row in schedule[f"Пара{class_number}"]
                                          if group in row.Группа.Наименование
                                          ])
        if not current_class_schedule:
            continue
        res += f"\n\n<b>{class_number}. {get_class_time(class_number, date)}</b> " + current_class_schedule
    if not res:
        return f"Пар для <b>{group}</b> на {schedule.Дата.strftime('%d.%m.%Y')} нет."
    return header + res


def check_schedule_by_date(date: datetime) -> brom.ДокументСсылка | None:
    con = DBConnection()
    selector: brom.Селектор = con.client.Документы.СоставлениеРасписания.СоздатьСелектор()
    try:
        selector.ДобавитьОтбор("Опубликовать", True)
        selector.ДобавитьОтбор("Дата", date)
        schedule = selector.ВыгрузитьРезультат()[0]
        return schedule
    except AttributeError:
        return None


def get_teacher_schedule(teacher_full_name: str, schedule: brom.ДокументСсылка, date: datetime = datetime.now()) -> str:
    header = f"""<b>{teacher_full_name} — {schedule.Дата.strftime('%d.%m.%Y')}:</b>"""
    res = ""
    for class_number in range(1, 8):
        current_class_schedule = "".join([f"\n<i>{row.Группа}</i> — {row.Аудитория}"
                                          for row in schedule[f"Пара{class_number}"]
                                          if teacher_full_name in row.Преподаватель.Наименование
                                          ])
        if not current_class_schedule:
            continue
        res += f"\n\n<b>{class_number}. {get_class_time(class_number, date)}</b> " + current_class_schedule
    if not res:
        return f"Пар для преподавателя <b>{teacher_full_name}</b> на {schedule.Дата.strftime('%d.%m.%Y')} нет."
    return header + res


def get_class_time(class_number: int, date: datetime) -> str:
    schedule = {
        1: "08:30-10:00",
        2: "10:10-11:40",
        3: "12:20-13:50" if date.weekday() != 5 else "12:00-13:30",
        4: "14:00-15:30" if date.weekday() != 5 else "13:40-15:10",
        5: "15:50-17:20" if date.weekday() != 5 else "15:20-16:50",
        6: "17:30-19:00" if date.weekday() != 5 else "17:00-18:30",
        7: "19:10-20:40" if date.weekday() != 5 else "18:40-20:10"
    }
    return schedule.get(class_number)


def get_group_by_id(group_id: int) -> str:
    con = DBConnection()
    group_selector: brom.Селектор = con.client.Справочники.Группы.СоздатьСелектор()
    group_selector.ДобавитьОтбор("Код", group_id)
    return group_selector.ВыгрузитьРезультат()[-1].Наименование


def get_teacher_by_id(teacher_id: int) -> str:
    con = DBConnection()
    group_selector: brom.Селектор = con.client.Справочники.Преподаватели.СоздатьСелектор()
    group_selector.ДобавитьОтбор("Код", teacher_id)
    return group_selector.ВыгрузитьРезультат()[-1].Наименование


def get_teacher_id_by_name(teacher_name: int) -> int:
    con = DBConnection()
    group_selector: brom.Селектор = con.client.Справочники.Преподаватели.СоздатьСелектор()
    group_selector.ДобавитьОтбор("Наименование", teacher_name)
    return group_selector.ВыгрузитьРезультат()[-1].Код


def get_schedule_from_subscriptions(username: str, subs: list[Subscription], date: datetime.date, schedule: brom.ДокументСсылка) -> str:
    
    res = f"<b>{username if username == 'Пользователь' else '@' + username}</b>, Ваши подписки:\n"
    if not subs:
        return f"<b>{username if username == 'Пользователь' else '@' + username}</b>, у вас нет подписок."
    teacher_schedule = "<b>Преподаватели: \n</b>"
    group_schedule = "<b>Группы: \n</b>"
    try:
        all_groups = get_all_groups()
        all_teachers = get_all_teachers()
        for sub in subs:
            match sub.entity_type:
                case SubscriptionType.GROUP:
                    group = next((item for item in all_groups if int(item.Код) == sub.entity_id), None)
                    today_schedule = get_schedule(group.Наименование, schedule, date) + "\n"
                    group_schedule += f"{today_schedule} {'-':->60}\n"
                    
                case SubscriptionType.TEACHER:
                    teacher = next((item for item in all_teachers if int(item.Код) == sub.entity_id), None)
                    today_schedule = get_teacher_schedule(teacher.Наименование, schedule, date) + "\n"
                    teacher_schedule += f"{today_schedule} {'-':->60}\n"
                    
    except Exception as e:
        print(f"Произошла ошибка при получении расписания по подпискам: {e}")
        return f"Произошла ошибка при получении расписания по подпискам"
    return res + teacher_schedule + "\n" + group_schedule


def get_greeting_message():
    match datetime.now().hour:
        case h if 5 <= h < 12:
            return "🌅 Доброе утро"
        case h if 12 <= h < 18:
            return "☀️ Добрый день"
        case h if 18 <= h < 23:
            return "🌇 Добрый вечер"
        case _:
            return "🌙 Доброй ночи"
