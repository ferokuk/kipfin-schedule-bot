from aiogram.fsm.state import StatesGroup, State


class UserState(StatesGroup):
    date = State()
    group = State()
    teacher = State()
    schedule_type = State()
    my_subs = State()
    all_groups = State()
    all_teachers = State()
    end = State()
