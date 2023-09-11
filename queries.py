import pythoncom
import win32com.client
from brom import *


def execute_query(q: str):
    client = БромКлиент(r"A:\1С FULL\BD\Диплом")
    print(client.ПолучитьИнформациюОСистеме())
    # V83_CONN_STRING = r'File="A:\1С FULL\BD\Диплом"'
    # pythoncom.CoInitialize()
    # V83 = win32com.client.Dispatch("V83.COMConnector").Connect(V83_CONN_STRING)
    # query = V83.NewObject("Query", q)
    # res = query.Execute().Choose()
    return None