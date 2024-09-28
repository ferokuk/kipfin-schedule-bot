from datetime import datetime, timedelta

import brom

from dbconnection import DBConnection
from schedule_sender import clear_subscriptions, send_schedule_to_subscribers
from utils import get_teacher_schedule, get_schedule, get_class_time, get_all_groups, get_all_teachers
import time
from functools import wraps


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record the start time
        result = func(*args, **kwargs)  # Call the function
        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time
        print(f"Выполнение функции '{func.__name__}' заняло {elapsed_time:.4f} секунд.")
        return result

    return wrapper


@timer
def test1():
    groups = ["1ИСИП-223"]
    teachers = ["Аксёнова Татьяна Геннадьевна"]
    date = datetime.datetime(2024, 5, 29)
    res = ""
    for g in groups:
        res += get_schedule(g, date)

    for t in teachers:
        res += get_teacher_schedule(t, date)

    return res


@timer
def test2(client, date, group):
    selector: brom.Селектор = client.Документы.СоставлениеРасписания.СоздатьСелектор()
    selector.ДобавитьОтбор("Дата", date)
    schedule = selector.ВыгрузитьРезультат()[0]
    header = f"Расписание для <b>{group}</b> на {schedule.Дата.strftime('%d.%m.%Y')}"
    res = f""""""
    for class_number in range(1, 8):
        current_class_schedule = "".join([f"\n<i>{row.Преподаватель}</i> - {row.Аудитория}"
                                          for row in schedule[f"Пара{class_number}"]
                                          if group in row.Группа.Наименование
                                          ])
        if not current_class_schedule:
            continue
        res += f"\n{class_number}. <b>{get_class_time(class_number, date)}</b> " + current_class_schedule
    if not res:
        return f"Пар для <b>{group}</b> на {schedule.Дата.strftime('%d.%m.%Y')} нет."
    return header + res


if __name__ == "__main__":
    send_schedule_to_subscribers()
