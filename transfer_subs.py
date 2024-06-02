import sqlite3

from dbconnection import DBConnection
from models import User, session, Subscription, SubscriptionType
from utils import get_all_groups, get_all_teachers


def transfer_subs():
    connection_sqlite = sqlite3.connect('database.db')
    cursor = connection_sqlite.cursor()
    cursor.execute('SELECT * FROM user;')
    users = cursor.fetchall()
    subs = cursor.execute('SELECT * FROM subscribe;').fetchall()
    connection_sqlite.close()
    print("started users")
    for user in users:
        try:
            new_postgres_user = User(id=user[0], username="Пользователь")
            session.add(new_postgres_user)
            session.commit()
        except:
            continue
    all_groups = get_all_groups()
    all_teachers = get_all_teachers()
    print("started subs")
    for sub in subs:
        user_id = sub[-1]

        # если есть группа
        if sub[1]:
            try:
                entity_id = next((item for item in all_groups if item["name"] == sub[1]))["id"]
                new_sub = Subscription(user_id=user_id, entity_id=entity_id, entity_type=SubscriptionType.GROUP)
                session.add(new_sub)
                session.commit()
            except Exception as e:
                print(e)
                pass
        if sub[2]:
            try:
                entity_id = next((item for item in all_teachers if sub[2] in item["name"]))["id"]
                new_sub = Subscription(user_id=user_id, entity_id=entity_id, entity_type=SubscriptionType.TEACHER)
                session.add(new_sub)
                session.commit()
            except Exception as e:
                print(e)
                pass


if __name__ == "__main__":
    transfer_subs()
