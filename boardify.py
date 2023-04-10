import os
from time import sleep

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

from db import *
from keyboard import *
from functions import *
from config import *

bot = telebot.TeleBot("6036111995:AAFnqTm4Llx3xrMaL5NlDwwP-P_izRqzFpM", parse_mode="HTML")  # server
kf = 3
kf_i = 2


@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text
    if is_user_exists(user_id):
        bot.send_message(user_id, "Сотрудник компании ", reply_markup=main_k)
        return
    args = message.text.split()
    if len(args) == 2:
        company_id, position_id = args[1].split("_")
        company = get_company_by_id(company_id)
        position = get_position_by_id(position_id, company_id)
        if company and position:
            new_user(user_id, company_id, position_id)
            bot.send_message(user_id, f"Вход успешен!\nКомпания: {company}\nДолжность: {position}",
                             reply_markup=main_k)
        else:
            bot.send_message(user_id, "Неверные данные в ссылке")
    else:
        bot.send_message(user_id, "Сначала нужно получить ссылку у работодателя")


@bot.message_handler(content_types=['text'])
def i_get_message(message):
    if message.chat.type == "private":
        chat_id = message.chat.id
        text = message.text
        user_id = message.from_user.id
        message_id = message.id
        company_id = get_company(user_id)
        if not company_id:
            bot.send_message(user_id, "Вы ещё не состоите ни в одной компании")
            return
        if text == main_k.keyboard[0][0]["text"]:  # Position
            learn_type = "position"
        elif text == main_k.keyboard[0][1]["text"]:  # Users
            learn_type = "users"
        elif text == main_k.keyboard[1][0]["text"]:  # Products
            learn_type = "products"
        elif text == main_k.keyboard[1][1]["text"]:  # Company
            learn_type = "company"
        else:
            return
        position_learn_state = get_learn_state(user_id, position_learn_state)
        company_state = get_learn_state(user_id, learn_type)
        info = get_learn(company_id, "position", position_learn_state)

def mailing(message):
    chat_id = message.chat.id
    try:
        text = message.text
    except:
        bot.send_message(chat_id, "Неверный формат", reply_markup=admin_k)
        return
    if text == back_k.keyboard[0][0]["text"] or text == "/start":
        bot.send_message(chat_id, "Админка", reply_markup=admin_k)
        return
    all_users = get_all_users(chat_id)
    bot.send_message(chat_id, "Начинаю рассылку...", reply_markup=admin_k)
    for user_id in all_users:
        try:
            bot.send_message(user_id[0], text)
        except:
            pass
    bot.send_message(chat_id, "Рассылка завершена!")


while True:
    try:
        print("START ONBOARDING")
        bot.infinity_polling()
    except:
        sleep(3)
