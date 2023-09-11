import os
import time

from dotenv import load_dotenv
import brom
import requests
from sqlalchemy import select
from models import *
from queries import *
from dbconnection import DBConnection


if __name__ == "__main__":
    load_dotenv()
    con = DBConnection()
    selector: brom.Селектор = con.client.Документы.СоставлениеРасписания.СоздатьСелектор()
    selector.Выбрать()
    schedule = selector.ВыгрузитьРезультат()[0]
    group = "3ИСИП-720"
    res = f"""Расписане на {schedule.Дата.strftime('%d.%m.%Y')} для группы {group}"""
    for class_number in range(1, int(os.getenv("MAX_LESSONS")) + 1):
        for row in getattr(schedule, f"Пара{class_number}"):
            if row.Группа.Наименование == group:
                res += f"\n{class_number}) {row.Преподаватель} - {row.Аудитория.Наименование}"
    print(res)
