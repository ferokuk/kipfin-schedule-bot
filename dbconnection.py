import os
import brom
from sqlalchemy import select
from models import *
from brom import *
from dotenv import load_dotenv
load_dotenv()


class DBConnection:
    __instance = None
    client = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        try:
            self.client = БромКлиент(os.getenv("CONNECTION_STRING"), os.getenv("USER"), os.getenv("PASSWORD"))

        except Exception as e:
            print(f"EXCEPTION WHILE CONNECTING:\n{e}")

    def execute_query(self, query) -> list[dict]:
        # if self.client is None:
        #     raise ConnectionError("NOT CONNECTED")
        try:
            res = [dict(list(row)) for row in self.client.СоздатьЗапрос(query).Выполнить()]
            return res
        except Exception as e:
            print(f"EXCEPTION WITH QUERY:\n{e}")
            return []

