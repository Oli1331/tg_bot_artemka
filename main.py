import telebot
import requests
import sqlite3
import random
import os
from datetime import datetime

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
answer_the_question_about_skip_true=["Скипай.","Нечего тебе там делать","Чё шутишь? Скип.","Эту пару запрещено посещать","Чутьё подсказывает, что эту пару можно безболезненно скипать.","Духи говорят, что эта пара тебе не нужна"]
answer_the_question_about_skip_false=["Чё умный самый? Иди давай","Надо идти, дружочек, надо.","Вали на пару","Сори братан, надо идти","Чутьё подсказывает, что сёдня скипать нельзя","Духи говорят, что сегодня обязательно отметят. Иди на пару короч."]
weather_smile=("⛅️","☀️","☁️")


connect_start = sqlite3.connect("data_base.db")
cursor=connect_start.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS user(id INTEGER PRIMARY KEY, first_name TEXT,last_name TEXT,chat_id INTEGER,UNIQUE(chat_id))")
connect_start.commit()
connect_start.close()



def request_weather():
    connect_to_site = requests.get(
        "https://weather.rambler.ru/api/v3/now/?url_path=v-novosibirskom-akademgorodke&only_current=1")
    return connect_to_site.json()

def insert_in_bd(first_name,last_name,chat_id):
    connect = sqlite3.connect("data_base.db")
    sql_cursor=connect.cursor()

    sql_cursor.execute("INSERT OR IGNORE INTO user (first_name, last_name,chat_id) VALUES (?, ?,?)",
                       (first_name, last_name,chat_id))
    connect.commit()
    connect.close()

@bot.message_handler(commands=['start'])
def start(message):
    base_buttons = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("/weather")
    btn2 = telebot.types.KeyboardButton("/info")
    btn3= telebot.types.KeyboardButton("/start")
    btn4= telebot.types.KeyboardButton("/skip_lesson")


    base_buttons.add(btn1,btn2,btn4)
    base_buttons.add(btn3)

    bot.send_message(message.chat.id,"Hello, "+message.from_user.first_name,reply_markup=base_buttons)
    print(message.from_user.first_name)
    insert_in_bd(message.from_user.first_name,message.from_user.last_name,message.chat.id)



@bot.message_handler(commands=['weather'])
def start(message):
    mes_button=telebot.types.InlineKeyboardMarkup()
    btn1=telebot.types.InlineKeyboardButton("Обновить🔁",callback_data="reload_weather")
    mes_button.add(btn1)
    connect_to_site = requests.get("https://weather.rambler.ru/api/v3/now/?url_path=v-novosibirskom-akademgorodke&only_current=1")
    information = request_weather()
    text = (
        f"Погода {information['town']['loc_case_name']}: "
        f"{information['current_weather']['temperature']} "
        f"{weather_smile[message.message_id % len(weather_smile)]}\n")
    bot.send_message(message.chat.id,text,reply_markup=mes_button)

    

@bot.message_handler(commands=['info','information'])
def info(message):
    text=str(message.from_user).replace(",","\n")
    bot.send_message(message.chat.id,text[1:-1])

@bot.message_handler(commands=['skip_lesson'])
def skip_lesson(message):
    rand_value=random.randint(0,100)
    if(rand_value>=80):
        num_answer=random.randint(0,len(answer_the_question_about_skip_true)-1)
        bot.reply_to(message,answer_the_question_about_skip_true[num_answer])
    else:
        num_answer = random.randint(0, len(answer_the_question_about_skip_false) - 1)
        bot.reply_to(message, answer_the_question_about_skip_false[num_answer])


@bot.callback_query_handler(func=lambda callback: True)
def callback_func(callback):
    if callback.data=="reload_weather":
        now = datetime.now().strftime("%H:%M:%S")

        bot.answer_callback_query(callback.id)
        mes_button = telebot.types.InlineKeyboardMarkup()
        btn1 = telebot.types.InlineKeyboardButton("Обновить🔁", callback_data="reload_weather")
        mes_button.add(btn1)
        information=request_weather()
        text = (
            f"Погода {information['town']['loc_case_name']}: "
            f"{information['current_weather']['temperature']} "
            f"{weather_smile[(callback.message.message_id-1)%len(weather_smile)]}\n"
            f"Обновлено: {now}")
        bot.edit_message_text(text,callback.message.chat.id,callback.message.message_id,reply_markup=mes_button)


bot.infinity_polling()