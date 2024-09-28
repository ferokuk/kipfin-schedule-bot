import sqlite3
from sqlite3 import IntegrityError

from icecream import ic
from sqlalchemy import create_engine, select, func, delete, and_
from sqlalchemy.exc import PendingRollbackError
from sqlalchemy.orm import sessionmaker, aliased

from dbconnection import DBConnection
from models import User, session, Subscription, SubscriptionType
from utils import get_all_groups, get_all_teachers


def delete_duplicates():
    # Find duplicates
    subq = (
        session.query(
            Subscription.user_id,
            Subscription.entity_id,
            Subscription.entity_type,
            func.count(Subscription.id).label('count')
        )
        .group_by(Subscription.user_id, Subscription.entity_id, Subscription.entity_type)
        .having(func.count(Subscription.id) > 1)
        .subquery()
    )

    # Create alias for main Subscription table
    sub_alias = aliased(Subscription)

    # Join with duplicates subquery to get the IDs of duplicate rows
    duplicates = (
        session.query(sub_alias.id)
        .join(subq, and_(
            sub_alias.user_id == subq.c.user_id,
            sub_alias.entity_id == subq.c.entity_id,
            sub_alias.entity_type == subq.c.entity_type
        ))
        .order_by(sub_alias.id)
        .all()
    )

    # Flatten list of duplicate IDs
    duplicate_ids = [d[0] for d in duplicates]

    # Use set to keep track of which duplicates to keep
    seen = set()
    to_delete = []

    for duplicate_id in duplicate_ids:
        subscription = session.query(Subscription).get(duplicate_id)
        key = (subscription.user_id, subscription.entity_id, subscription.entity_type)

        if key in seen:
            to_delete.append(duplicate_id)
        else:
            seen.add(key)

    # Delete duplicates
    if to_delete:
        session.query(Subscription).filter(Subscription.id.in_(to_delete)).delete(synchronize_session=False)
        session.commit()

    # Close the session
    session.close()


def transfer_subs():
    # Connect to the SQLite database
    connection_sqlite = sqlite3.connect('database.db')
    cursor = connection_sqlite.cursor()

    # Fetch users from SQLite
    cursor.execute('SELECT * FROM user;')
    users = cursor.fetchall()

    # Optionally, fetch subscriptions if needed
    subs = cursor.execute('SELECT * FROM subscribe;').fetchall()

    # Close SQLite connection
    connection_sqlite.close()

    # Print the number of users fetched
    ic("started users")
    ic(len(users))

    # Iterate over users and add to PostgreSQL
    for i, user in enumerate(users):
        try:
            # Log user info
            ic(f"Processing user {i}: {user}")

            # Create new PostgreSQL user object
            new_postgres_user = User(id=user[0], username="Пользователь")

            # Add and commit user to PostgreSQL
            session.add(new_postgres_user)
            session.commit()
        except (IntegrityError, PendingRollbackError) as e:
            # Log the exception and rollback the session
            ic(f"Error occurred for user {i}: {e}")
            session.rollback()
        except Exception as e:
            # General exception handling
            ic(f"Unexpected error for user {i}: {e}")
            session.rollback()

    session.query(Subscription).delete(synchronize_session=False)
    session.commit()

    # Close the session
    all_groups = get_all_groups()
    all_teachers = get_all_teachers()
    ic("started subs")
    ic(len(subs))

    for i, sub in enumerate(subs):
        user_id = sub[-1]
        try:
            # если есть группа
            if sub[1]:
                entity_id = next((item for item in all_groups if str(item.Наименование) == sub[1])).Код
                if session.query(Subscription) \
                        .where(Subscription.user_id == user_id,
                               Subscription.entity_id == int(entity_id),
                               Subscription.entity_type == SubscriptionType.GROUP).first() is not None:
                    continue
                ic(user_id, int(entity_id))
                new_sub = Subscription(user_id=user_id, entity_id=int(entity_id), entity_type=SubscriptionType.GROUP)
                session.add(new_sub)
                session.commit()
            if sub[2]:
                entity_id = next((item for item in all_teachers if sub[2] in str(item.Наименование))).Код
                if session.query(Subscription) \
                        .where(Subscription.user_id == user_id,
                               Subscription.entity_id == int(entity_id),
                               Subscription.entity_type == SubscriptionType.TEACHER).first() is not None:
                    continue
                ic(user_id, int(entity_id))
                new_sub = Subscription(user_id=user_id, entity_id=int(entity_id), entity_type=SubscriptionType.TEACHER)
                session.add(new_sub)
                session.commit()
        except (IntegrityError, PendingRollbackError) as e:
            # Log the exception and rollback the session
            ic(f"Error occurred for sub {i}: {e}")
            session.rollback()
        except Exception as e:
            # General exception handling
            ic(f"Unexpected error for sub {i}: {e}")
            session.rollback()
    # delete_duplicates()
    session.close()


if __name__ == "__main__":
    transfer_subs()
