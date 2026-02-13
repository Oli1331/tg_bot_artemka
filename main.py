import telebot
import requests
import sqlite3
import random
import os
from dateutil.rrule import rrulestr
from icalendar import Calendar
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
answer_the_question_about_skip_true = ["Скипай.", "Нечего тебе там делать", "Чё шутишь? Скип.",
                                       "Эту пару запрещено посещать",
                                       "Чутьё подсказывает, что эту пару можно безболезненно скипать.",
                                       "Духи говорят, что эта пара тебе не нужна"]
answer_the_question_about_skip_false = ["Чё умный самый? Иди давай", "Надо идти, дружочек, надо.", "Вали на пару",
                                        "Сори братан, надо идти", "Чутьё подсказывает, что сёдня скипать нельзя",
                                        "Духи говорят, что сегодня обязательно отметят. Иди на пару короч."]
weather_smile = ("⛅️", "☀️", "☁️", "🥶", "🔆", "🏖", "🏝", "🌦", "☃️", "❄️", "⛈", "🧤🧣", "🩳👕")
headers_for_request = {
    "User-Agent": "Mozilla/5.0"
}
WEEKDAY_MAP = {
    "MO": "Понедельник",
    "TU": "Вторник",
    "WE": "Среда",
    "TH": "Четверг",
    "FR": "Пятница",
    "SA": "Суббота",
    "SU": "Воскресенье",
}
WEEKDAY_MAP_OF_NUM = {
    0: "MO",
    1: "TU",
    2: "WE",
    3: "TH",
    4: "FR",
    5: "SA",
    6: "SU"
}

connect_start = sqlite3.connect("data_base.db")
cursor = connect_start.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS user(id INTEGER PRIMARY KEY, first_name TEXT,last_name TEXT,chat_id INTEGER,UNIQUE(chat_id))")
connect_start.commit()
connect_start.close()


def format_schedule_for_day(ics_text: str, weekday: str) -> str:
    cal = Calendar.from_ical(ics_text)

    today = datetime.now().date()
    week_end = today + timedelta(days=6)

    lessons = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get("SUMMARY", "")).strip()
        location = str(component.get("LOCATION", "")).replace("Аудитория:", "").strip()
        teacher = str(component.get("DESCRIPTION", "")).replace("Преподаватель:", "").strip()

        dtstart = component.get("DTSTART").dt
        dtend = component.get("DTEND").dt

        # принудительно убираем tzinfo
        if isinstance(dtstart, datetime):
            dtstart = dtstart.replace(tzinfo=None)
            dtend = dtend.replace(tzinfo=None)

        rrule_raw = component.get("RRULE")

        if rrule_raw:
            rule = rrulestr(
                rrule_raw.to_ical().decode(),
                dtstart=dtstart
            )
            dates = rule.between(
                datetime.combine(today, datetime.min.time()),
                datetime.combine(week_end, datetime.max.time()),
                inc=True
            )

        else:
            dates = [dtstart]

        for d in dates:
            if d.strftime("%a").upper().startswith(weekday):
                lessons.append({
                    "start": d,
                    "end": d + (dtend - dtstart),
                    "teacher": teacher or "—",
                    "location": location or "—",
                    "summary": summary,
                })

    if not lessons:
        return f"📭 {WEEKDAY_MAP[weekday]}: занятий нет"

    lessons.sort(key=lambda x: x["start"])

    lines = [f"📅 {WEEKDAY_MAP[weekday]}\n"]

    for l in lessons:
        time = f"{l['start'].strftime('%H:%M')}–{l['end'].strftime('%H:%M')}"
        lines.append(
            f"🕒 {time}\n"
            f"🧑🏼‍🏫 {l['teacher']}\n"
            f"🚪 {l['location']}\n"
        )

    return "\n".join(lines).strip()


def get_schedule(number_group) -> str:
    connect = requests.get("https://table.nsu.ru/ics/group/25216", headers=headers_for_request)
    ics_text = connect.text
    if ics_text[0] == '<':
        return "Не удалось вывести расписание этой группы ❌"
    else:
        return format_schedule_for_day(ics_text, WEEKDAY_MAP_OF_NUM[datetime.now().date().weekday()])


def request_weather():
    connect_to_site = requests.get(
        "https://weather.rambler.ru/api/v3/now/?url_path=v-novosibirskom-akademgorodke&only_current=1")
    return connect_to_site.json()


def insert_in_bd(first_name, last_name, chat_id):
    connect = sqlite3.connect("data_base.db")
    sql_cursor = connect.cursor()

    sql_cursor.execute("INSERT OR IGNORE INTO user (first_name, last_name,chat_id) VALUES (?, ?,?)",
                       (first_name, last_name, chat_id))
    connect.commit()
    connect.close()


@bot.message_handler(commands=['start'])
def start(message):
    base_buttons = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("/weather")
    btn2 = telebot.types.KeyboardButton("/info")
    btn3 = telebot.types.KeyboardButton("/start")
    btn4 = telebot.types.KeyboardButton("/skip_lesson")
    btn5 = telebot.types.KeyboardButton("/schedule")

    base_buttons.add(btn2, btn4)
    base_buttons.add(btn1, btn5)
    base_buttons.add(btn3)

    bot.send_message(message.chat.id, "Hello, " + message.from_user.first_name, reply_markup=base_buttons)
    print(message.from_user.first_name)
    insert_in_bd(message.from_user.first_name, message.from_user.last_name, message.chat.id)


@bot.message_handler(commands=['weather'])
def start(message):
    mes_button = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton("Обновить🔁", callback_data="reload_weather")
    mes_button.add(btn1)
    connect_to_site = requests.get(
        "https://weather.rambler.ru/api/v3/now/?url_path=v-novosibirskom-akademgorodke&only_current=1")
    information = request_weather()
    text = (
        f"Погода {information['town']['loc_case_name']}: "
        f"{information['current_weather']['temperature']} "
        f"{weather_smile[message.message_id % len(weather_smile)]}\n")
    bot.send_message(message.chat.id, text, reply_markup=mes_button)


@bot.message_handler(commands=['info', 'information'])
def info(message):
    text = str(message.from_user).replace(",", "\n")
    bot.send_message(message.chat.id, text[1:-1])


@bot.message_handler(commands=['skip_lesson'])
def skip_lesson(message):
    rand_value = random.randint(0, 100)
    if rand_value >= 80:
        num_answer = random.randint(0, len(answer_the_question_about_skip_true) - 1)
        bot.reply_to(message, answer_the_question_about_skip_true[num_answer])
    else:
        num_answer = random.randint(0, len(answer_the_question_about_skip_false) - 1)
        bot.reply_to(message, answer_the_question_about_skip_false[num_answer])


@bot.message_handler(commands=["schedule"])
def schedule(message):
    bot.send_message(message.chat.id, "Напиши номер группы")
    bot.register_next_step_handler(message, schedule_from_number_group)


def schedule_from_number_group(message):
    text = get_schedule(message.text)
    bot.send_message(message.chat.id, text)


@bot.callback_query_handler(func=lambda callback: True)
def callback_func(callback):
    if callback.data == "reload_weather":
        now = datetime.now().strftime("%H:%M:%S")

        bot.answer_callback_query(callback.id)
        mes_button = telebot.types.InlineKeyboardMarkup()
        btn1 = telebot.types.InlineKeyboardButton("Обновить🔁", callback_data="reload_weather")
        mes_button.add(btn1)
        information = request_weather()
        text = (
            f"Погода {information['town']['loc_case_name']}: "
            f"{information['current_weather']['temperature']} "
            f"{weather_smile[(callback.message.message_id - 1) % len(weather_smile)]}\n"
            f"Обновлено: {now}")
        bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, reply_markup=mes_button)


bot.infinity_polling()
