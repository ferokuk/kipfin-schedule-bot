import os
from datetime import datetime

import brom

from dbconnection import DBConnection


def get_all_groups() -> list[str]:
    con = DBConnection().client
    selector: brom.Селектор = con.Справочники.Группы.СоздатьСелектор()
    selector.ДобавитьОтбор("Совмещение", False)
    selector.ДобавитьОтбор("ПометкаУдаления", False)
    return [g.Наименование for g in selector.Выбрать().ВыгрузитьРезультат()]


def get_all_teachers() -> list[dict]:
    con = DBConnection().client
    selector: brom.Селектор = con.Справочники.Преподаватели.СоздатьСелектор()
    selector.ДобавитьОтбор("ПометкаУдаления", False)
    return [{"name": g.Наименование, "id": str(int(g.Код))} for g in selector.Выбрать().ВыгрузитьРезультат()]


def get_schedule(group: str, date: datetime = None) -> str:
    con = DBConnection()
    selector: brom.Селектор = con.client.Документы.СоставлениеРасписания.СоздатьСелектор()
    schedules = [s for s in selector.Выполнить().ВыгрузитьРезультат() if date.day == s.Дата.day and
                 date.month == s.Дата.month and
                 date.year == s.Дата.year
                 ]
    if not schedules:
        return f"Расписания для <b>{group}</b> на {date.strftime('%d.%m.%Y')} нет."
    schedule = schedules[-1]
    res = f"""Расписание для <b>{group}</b> на {schedule.Дата.strftime('%d.%m.%Y')}"""
    for class_number in range(1, int(os.getenv("MAX_LESSONS")) + 1):
        for row in getattr(schedule, f"Пара{class_number}"):
            if group in str(row.Группа.Наименование):
                teacher = str(row.Преподаватель or "Нет").strip()
                classroom = str(row.Аудитория.Наименование or "Нет").strip()
                res += f"\n{class_number}. <b>{get_class_time(class_number, date)}</b> <i>{teacher}</i> - {classroom}"
    if res == f"""Расписание для <b>{group}</b> на {schedule.Дата.strftime('%d.%m.%Y')}""":
        return f"Пар для <b>{group}</b> на {schedule.Дата.strftime('%d.%m.%Y')} нет"
    return res


def check_schedule_by_date(date: datetime) -> bool:
    con = DBConnection()
    selector: brom.Селектор = con.client.Документы.СоставлениеРасписания.СоздатьСелектор()
    return any([date.day == d.Дата.day and
                date.month == d.Дата.month and
                date.year == d.Дата.year
                for d in selector.Выполнить().ВыгрузитьРезультат()])


def get_teacher_schedule(teacher_id: str, date: datetime = None) -> str:
    con = DBConnection()
    selector: brom.Селектор = con.client.Документы.СоставлениеРасписания.СоздатьСелектор()
    schedules = [s for s in selector.Выполнить().ВыгрузитьРезультат() if date.day == s.Дата.day and
                 date.month == s.Дата.month and
                 date.year == s.Дата.year
                 ]
    teacher_selector: brom.Селектор = con.client.Справочники.Преподаватели.СоздатьСелектор()
    teacher_selector.ДобавитьОтбор("Код", int(teacher_id))
    teacher_full_name = teacher_selector.ВыгрузитьРезультат()[-1].Наименование
    if not schedules:
        return f"Расписания для преподавателя <b>{teacher_full_name}</b> на {date.strftime('%d.%m.%Y')} нет."
    schedule = schedules[-1]
    res = f"""Расписание на {schedule.Дата.strftime('%d.%m.%Y')} для преподавателя <b>{teacher_full_name}</b>"""
    for class_number in range(1, int(os.getenv("MAX_LESSONS")) + 1):
        for row in getattr(schedule, f"Пара{class_number}"):
            if teacher_full_name == row.Преподаватель.Наименование:
                group = str(row.Группа.Наименование).strip()
                classroom = str(row.Аудитория.Наименование).strip()
                res += f"\n{class_number}. <b>{get_class_time(class_number, date)}</b> <i>{group}</i> - {classroom}"
    if res == f"""Расписание на {schedule.Дата.strftime('%d.%m.%Y')} для преподавателя <b>{teacher_full_name}</b>""":
        return f"Пар для <b>{teacher_full_name}</b> на {schedule.Дата.strftime('%d.%m.%Y')} нет"
    return res


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
