from collections import defaultdict
from datetime import datetime
from icecream import ic
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
import json

from starlette.responses import JSONResponse

from bot import bot
from models import session, Subscription, SubscriptionType
from utils import get_class_time

load_dotenv()

app = FastAPI()


@app.post('/upload/')
async def get_schedule_updates(request: Request):
    if 'Content-Length' not in request.headers:
        raise HTTPException(status_code=400, detail="No Content-Length header")
    content_length = int(request.headers['Content-Length'])
    if content_length <= 0:
        raise HTTPException(status_code=400, detail="Empty content")
    received_data = await request.body()
    received_data = received_data.decode('utf-8')
    try:
        data_object = json.loads(received_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    formatted_data = json.dumps(data_object, indent=4, ensure_ascii=False)
    await detect_changes(data_object)
    return JSONResponse(content={"message": "File content printed and saved successfully"})


def process_schedule_teacher(schedule):
    teacher_schedule = defaultdict(list)
    for period, classes in schedule.items():
        for class_info in classes:
            teacher = class_info.get('Преподаватель', "Нет").strip()
            teacher_id = class_info.get('КодПреподавателя', -1)
            group = class_info.get('Группа', "Нет")
            room = class_info.get('Аудитория', -1)
            # Assuming 'ПараX' corresponds to class_number in your other code
            class_number = int(period.split('Пара')[1])
            teacher_schedule[(teacher, teacher_id)].append({
                'group': group,
                'room': room,
                'class_number': class_number
            })
    return teacher_schedule


def process_schedule_group(schedule):
    group_schedule = defaultdict(list)
    for period, classes in schedule.items():
        for class_info in classes:
            group = class_info.get('Группа', "Нет").strip()
            group_id = class_info.get('КодГруппы', -1)
            teacher = class_info.get('Преподаватель', "Нет")
            room = class_info.get('Аудитория', -1)
            # Assuming 'ПараX' corresponds to class_number in your other code
            class_number = int(period.split('Пара')[1])
            group_schedule[(group, group_id)].append({
                'teacher': teacher,
                'room': room,
                'class_number': class_number
            })
            group_schedule[(group, group_id)].sort(key=lambda item: item['class_number'])
    return group_schedule


async def detect_changes(schedule_with_schanges: dict):
    old_schedule = process_schedule_teacher(schedule_with_schanges['СтароеРасписание'])
    new_schedule = process_schedule_teacher(schedule_with_schanges['НовоеРасписание'])
    for teacher, teacher_id in set(old_schedule.keys()).union(new_schedule.keys()):

        old_classes = set((class_info['group'], class_info['room'], class_info['class_number']) for class_info
                          in old_schedule.get((teacher, teacher_id), []))
        new_classes = set((class_info['group'], class_info['room'], class_info['class_number']) for class_info
                          in new_schedule.get((teacher, teacher_id), []))
        # Find differences
        added = new_classes - old_classes
        removed = old_classes - new_classes
        # Example of integrating changes into schedule string
        if not added and not removed:
            continue
        date = datetime.strptime(schedule_with_schanges['Дата'], '%Y-%m-%dT%H:%M:%S')
        schedule_string = get_teacher_schedule_from_json(new_schedule, teacher, date, added, removed)
        subs_to_teacher = session.query(Subscription) \
            .where(Subscription.entity_id == teacher_id,
                   Subscription.entity_type == SubscriptionType.TEACHER) \
            .all()
        for sub in subs_to_teacher:
            username = sub.user.username if sub.user.username == 'Пользователь' else '@' + sub.user.username
            await bot.send_message(sub.user.id,
                                   f"<b>{username}</b>, произошли изменения в расписании!\n" + schedule_string,
                                   parse_mode=ParseMode.HTML
                                   )
        # print(f"Преподаватель: {teacher}")
        # if added:
        #     print(f"  Добавлены пары: {added}")
        # if removed:
        #     print(f"  Удалены пары: {removed}")

    old_schedule = process_schedule_group(schedule_with_schanges['СтароеРасписание'])
    new_schedule = process_schedule_group(schedule_with_schanges['НовоеРасписание'])
    full_schedule = set(old_schedule.keys()).union(new_schedule.keys())
    for group, group_id in full_schedule:
        old_classes = set((class_info['teacher'], class_info['room'], class_info['class_number']) for class_info
                          in old_schedule.get((group, group_id), []))
        new_classes = set((class_info['teacher'], class_info['room'], class_info['class_number']) for class_info
                          in new_schedule.get((group, group_id), []))
        added = new_classes - old_classes
        removed = old_classes - new_classes
        if not added and not removed:
            continue
        date = datetime.strptime(schedule_with_schanges['Дата'], '%Y-%m-%dT%H:%M:%S')
        if "," in group:
            # ЕСЛИ ЕСТЬ ЗАПЯТАЯ, ТО СОВМЕЩЁННАЯ. РАЗБИВАЕМ
            groups = group.split(", ")
            # ДЛЯ КАЖДОЙ ГРУППЫ В СОВМЕЩЁНКЕ НАХОДИМ ЕЁ КОД ДЛЯ ПОЛУЧЕНИЯ ПОДПИСОК
            for sub_group in groups:
                sub_group_id = [s for s in full_schedule if s[0] == sub_group][0][1]
                ic(sub_group, sub_group_id)
                await handle_group(new_schedule, sub_group, sub_group_id, date, added, removed)
            # ДАЛЕЕ КАЖДУЮ ГРУППЫ ОБРАБАТЫВАЕМ КАК ОБЫЧНО
        else:
            await handle_group(new_schedule, group, group_id, date, added, removed)


async def handle_group(new_schedule, group, group_id, date, added, removed):
    schedule_string = get_group_schedule_from_json(new_schedule, group, date, added, removed)
    subs_to_teacher = session.query(Subscription) \
        .where(Subscription.entity_id == group_id,
               Subscription.entity_type == SubscriptionType.GROUP) \
        .all()
    for sub in subs_to_teacher:
        username = sub.user.username if sub.user.username == 'Пользователь' else '@' + sub.user.username
        await bot.send_message(sub.user.id,
                               f"<b>{username}</b>, произошли изменения в расписании!\n" + schedule_string,
                               parse_mode=ParseMode.HTML
                               )
    # print(f"Группа: {group}")
    # if added:
    #     print(f"  Добавлены пары: {added}")
    # if removed:
    #     print(f"  Удалены пары: {removed}")


def get_teacher_schedule_from_json(schedule_json: dict, teacher: str, date: datetime,
                                   added_classes: set, removed_classes: set) -> str:
    header = f"<b>{teacher} — {date.strftime('%d.%m.%Y')}:</b>"
    res = ""
    for (teacher_name, teacher_id), schedule in schedule_json.items():
        if teacher_name != teacher:
            continue

        for class_info in schedule:
            group = class_info['group']
            room = class_info['room']
            class_number = class_info['class_number']
            class_time = get_class_time(class_number, date)
            # Check if the current class is in added or removed sets
            if (group, room, class_number) in added_classes:
                res += f"\n\n<b>{class_number}. {class_time} (Изменено)</b>\n<i>{group}</i> — {room}"
            elif (group, room, class_number) in removed_classes:
                res += f"\n\n<s><b>{class_number}. {class_time} (Удалено)</b>\n<i>{group}</i> — {room}</s>"
            else:
                res += f"\n\n<b>{class_number}. {class_time}</b>\n<i>{group}</i> — {room}"

    if not res:
        return f"Пар для преподавателя <b>{teacher}</b> на {date.strftime('%d.%m.%Y')} нет."
    return header + res


def get_group_schedule_from_json(schedule_json: dict, group: str, date: datetime,
                                 added_classes: set, removed_classes: set) -> str:
    header = f"<b>{group} — {date.strftime('%d.%m.%Y')}:</b>"
    res = ""

    # Step 1: Accumulate all matching schedules
    accumulated_schedule = []

    for (group_name, group_id), schedule in schedule_json.items():
        if group in group_name:
            accumulated_schedule.extend(schedule)

    # Step 2: Group classes by class_number
    grouped_classes = defaultdict(list)
    for class_info in accumulated_schedule:
        class_number = class_info['class_number']
        grouped_classes[class_number].append(class_info)

    # Step 3: Process the grouped classes
    for class_number in sorted(grouped_classes.keys()):
        classes = grouped_classes[class_number]
        class_time = get_class_time(class_number, date)
        class_header = f"\n\n<b>{class_number}. {class_time}</b>"
        class_body = ""

        for class_info in classes:
            teacher = class_info['teacher']
            room = class_info['room']

            if (teacher, room, class_number) in added_classes:
                class_body += f"\n<i>{teacher}</i> — {room} (Изменено)"
            elif (teacher, room, class_number) in removed_classes:
                class_body += f"\n<s><i>{teacher}</i> — {room} (Удалено)</s>"
            else:
                class_body += f"\n<i>{teacher}</i> — {room}"

        res += class_header + class_body

    if not res:
        return f"Пар для <b>{group}</b> на {date.strftime('%d.%m.%Y')} нет."
    return header + res


if __name__ == '__main__':
    # res = get_schedule_from_json(schedule_json=data["НовоеРасписание"],
    #                              group="2ОИБАС-1122",
    #                              date=datetime.strptime(data['Дата'], '%Y-%m-%dT%H:%M:%S'))
    pass
