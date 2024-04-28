import os
from datetime import datetime

import brom

from dbconnection import DBConnection


def get_all_groups() -> list[dict]:
    con = DBConnection().client
    selector: brom.Селектор = con.Справочники.Группы.СоздатьСелектор()
    selector.ДобавитьОтбор("Совмещение", False)
    selector.ДобавитьОтбор("ПометкаУдаления", False)
    return [{"name": g.Наименование, "id": str(int(g.Код))} for g in selector.Выбрать().ВыгрузитьРезультат()]


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
        return f"Расписания на {date.strftime('%d.%m.%Y')} нет."
    schedule = schedules[-1]
    header = f"Расписание для <b>{group}</b> на {schedule.Дата.strftime('%d.%m.%Y')}"
    res = f""""""
    for class_number in range(1, int(os.getenv("MAX_LESSONS")) + 1):
        current_class_schedule = ""
        for row in getattr(schedule, f"Пара{class_number}"):
            if group in str(row.Группа.Наименование):
                teacher = str(row.Преподаватель or "Нет").strip()
                classroom = str(row.Аудитория.Наименование or "Нет").strip()
                current_class_schedule += f"\n<i>{teacher}</i> - {classroom}"
        if current_class_schedule:
            res += f"\n{class_number}. <b>{get_class_time(class_number, date)}</b> " + current_class_schedule
    if not res:
        return f"Пар для <b>{group}</b> на {schedule.Дата.strftime('%d.%m.%Y')} нет"
    return header + res


def check_schedule_by_date(date: datetime) -> bool:
    con = DBConnection()
    selector: brom.Селектор = con.client.Документы.СоставлениеРасписания.СоздатьСелектор()
    return any([date.day == d.Дата.day and
                date.month == d.Дата.month and
                date.year == d.Дата.year
                for d in selector.Выполнить().ВыгрузитьРезультат()])


def get_teacher_schedule(teacher_full_name: str, date: datetime = None) -> str:
    con = DBConnection()
    selector: brom.Селектор = con.client.Документы.СоставлениеРасписания.СоздатьСелектор()
    schedules = [s for s in selector.Выполнить().ВыгрузитьРезультат() if date.day == s.Дата.day and
                 date.month == s.Дата.month and
                 date.year == s.Дата.year
                 ]
    if not schedules:
        return f"Расписания на {date.strftime('%d.%m.%Y')} нет."
    schedule = schedules[-1]
    teacher_full_name = teacher_full_name.strip()
    header = f"""Расписание на {schedule.Дата.strftime('%d.%m.%Y')} для преподавателя <b>{teacher_full_name}</b>"""
    res = ""
    for class_number in range(1, int(os.getenv("MAX_LESSONS")) + 1):
        current_class_schedule = ""
        for row in getattr(schedule, f"Пара{class_number}"):
            if teacher_full_name == row.Преподаватель.Наименование:
                group = str(row.Группа.Наименование).strip()
                classroom = str(row.Аудитория.Наименование).strip()
                current_class_schedule += f"\n<i>{group}</i> - {classroom}"
        if current_class_schedule:
            res += f"\n{class_number}. <b>{get_class_time(class_number, date)}</b> " + current_class_schedule
    if not res:
        return f"Пар для <b>{teacher_full_name}</b> на {schedule.Дата.strftime('%d.%m.%Y')} нет"
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


def create_schedule_with_subscriptions(teachers: list[str], groups: list[str]) -> str:
    pass