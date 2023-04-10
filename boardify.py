import os
from time import sleep

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

from db import *
from keyboard import *
from functions import *
from config import *

bot = telebot.TeleBot("TOKEN", parse_mode="HTML")  # server


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
        to_send, keyboard = build_learn(user_id, company_id, learn_type)
        bot.send_message(user_id, to_send, reply_markup=keyboard)


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


def build_learn(user_id, company_id, learn_type, base=True):
    state_num = get_learn_state(user_id, learn_type)
    last_state = get_last_state(user_id, learn_type)
    learning_id, company_id, info, question, correct_answer = get_learn(company_id, "position", state_num)
    answers = get_answers(learning_id)
    send_text = ""
    keyboard = InlineKeyboardMarkup()
    if state_num:
        if base:
            send_text += f"Задание {state_num}.\n\n{info}"
            if answers:
                if state_num != 1:
                    keyboard.add(InlineKeyboardButton("⬅", callback_data=f"go_task {state_num - 1}"),
                                 InlineKeyboardButton("❓", callback_data=f"go_question {state_num}"))
                else:
                    keyboard.add(InlineKeyboardButton("❓", callback_data=f"go_question {state_num}"))
            else:
                if state_num != 1:
                    if state_num != last_state:
                        keyboard.add(InlineKeyboardButton("⬅", callback_data=f"go_task {state_num - 1}"),
                                     InlineKeyboardButton("➡", callback_data=f"go_task {state_num + 1}"))
                    else:
                        keyboard.add(InlineKeyboardButton("⬅", callback_data=f"go_task {state_num - 1}"),
                                     InlineKeyboardButton("🏁", callback_data=f"finish"))
                else:
                    keyboard.add(InlineKeyboardButton("➡", callback_data=f"go_task {state_num + 1}"))
        else:
            send_text += f"Вопрос к заданию {state_num}.\n\n{question}"
            mas = []
            for num, i in enumerate(answers):
                mas.append(InlineKeyboardButton(i[0], callback_data=f"check_answer {i[1]}"))
                if num % 3 == 0 and num != 0:
                    keyboard.add(*mas)
                    mas = []
            keyboard.add(*mas)
    else:
        send_text = "Заданий ещё нет"
    return send_text, keyboard


while True:
    try:
        print("START ONBOARDING")
        bot.infinity_polling()
    except:
        sleep(3)
