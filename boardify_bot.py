import os
from threading import Thread
from time import sleep

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

from db import *
from keyboard import *
from functions import *
from config import *

bot = telebot.TeleBot("6036111995:AAFnqTm4Llx3xrMaL5NlDwwP-P_izRqzFpM", parse_mode="HTML")  # server


@bot.message_handler(commands=['info'])
def info(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Добро пожаловать в @BoardifyBot!\n"
                              "Здесь Вы можете обучиться профессиональным навыкам и влиться в коллектив,"
                              " а если останутся какие-то вопросы - смело задавайте их администратору.")
    bot.send_message(user_id, "Краткий экскурс по меню:\n\n"
                              "<b>💼Должность💼:</b> Ваши должностные обязанности как сотрудника. "
                              "Внимательно изучите их - там много полезного\n\n"
                              "<b>📦Продукты компании📦:</b> В этой категории Вы можете увидеть продукты "
                              "Вашей компании, что она производит, чем живёт и т.д.\n\n"
                              "<b>👥Сотрудники👥:</b> Место, где Вы можете ознакомиться с другими сотрудниками, "
                              "узнать что-то о их жизни и области работы\n\n"
                              "<b>ℹО компанииℹ:</b> Узнайте новые факты о Вашей компании, "
                              "её историю и основные направления работы\n\n"
                              "<b>❓Задать вопрос❓:</b> Если не нашли то, что искали, то Вы можете написать "
                              "свой вопрос сюда и получить ответ от администратора\n\n"
                              "На этом всё. Чтобы ещё раз увидеть это меню пропишите /info", parse_mode="HTML")


@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username
    text = message.text
    if not username:
        bot.send_message(user_id, "Для начала работы необходимо установить @username")
        return
    if is_user_exists(user_id):
        set_username(user_id, username)
        company_id = get_company(user_id)
        bot.send_message(user_id, f"{get_position_by_id(get_user_position(user_id)[0], company_id)} "
                                  f"компании {get_company_by_id(company_id)}", reply_markup=main_k)
        return
    args = message.text.split()
    if len(args) == 2:
        try:
            company_id, position_id = args[1].split("_")
            company = get_company_by_id(company_id)
            position = get_position_by_id(position_id, company_id)
            if company and position:
                new_user(user_id, username, company_id, position_id)
                bot.send_message(user_id, f"Вход успешен!\nКомпания: {company}\nДолжность: {position}",
                                 reply_markup=main_k)
                info(message)
            else:
                bot.send_message(user_id, "Неверные данные в ссылке")
        except Exception as e:
            print(e)
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
        position_id = get_user_position(user_id)
        if not company_id or not position_id:
            bot.send_message(user_id, "Вы ещё не состоите ни в одной компании")
            return
        position_id = position_id[0]
        if text[:3] == "sql":
            s = sql(text[4:])
            ms = ""
            for i in s:
                ms += f"{i}\n"
            bot.send_message(user_id, ms)
            return
        if text == main_k.keyboard[0][0]["text"]:  # Profile
            bot.send_message(user_id, build_profile(user_id), reply_markup=main_k, parse_mode="HTML")
            return
        elif text == main_k.keyboard[1][0]["text"]:  # Position
            learn_type = "position"
        elif text == main_k.keyboard[1][1]["text"]:  # Users
            learn_type = "users"
        elif text == main_k.keyboard[2][0]["text"]:  # Products
            learn_type = "products"
        elif text == main_k.keyboard[2][1]["text"]:  # Company
            learn_type = "company"
        elif text == main_k.keyboard[3][0]["text"]:  # Question
            bot.send_message(user_id, "Введите сообщение", reply_markup=back_k)
            bot.register_next_step_handler_by_chat_id(user_id, message_to_admin)
            return
        else:
            bot.send_message(user_id, "Неизвестная команда", reply_markup=main_k)
            return
        learning_id = get_learn_state(user_id, learn_type)
        if learning_id == 0:
            bot.send_message(user_id, "Вы уже прошли все блоки комплекса")
            return
        if not get_learn(learning_id):
            learning_id = -1
        if learning_id < 0:
            next_id = found_first_learning(user_id, learning_id, learn_type)
            if next_id:
                set_state(user_id, learn_type, next_id)
                learning_id = get_learn_state(user_id, learn_type)
            else:
                bot.send_message(user_id, "Информации ещё нет")
                return
        to_send, keyboard, path = build_learn(company_id, position_id, learn_type, learning_id)
        send_media(user_id, to_send, keyboard, path)


@bot.callback_query_handler(func=lambda call: True)
def new_call(call):
    if call.message:
        user_id = call.message.chat.id
        chat_id = call.message.chat.id
        message_id = call.message.id
        data = call.data
        info = data.split()
        company_id = get_company(user_id)
        position_id = get_user_position(user_id)[0]
        if info[0] == "go_next":
            learn_type = info[1]
            learning_id = int(info[2])
            next_id = found_next_learning(user_id, learning_id, learn_type)
            if next_id:
                if learning_id == get_learn_state(user_id, learn_type):
                    set_state(user_id, learn_type, next_id)
                to_send, keyboard, path = build_learn(company_id, position_id, learn_type, next_id)
                edit_media(user_id, to_send, message_id, keyboard, path)
            else:
                edit_media("Поздравляем! Вы прошли все блоки комплекса!", user_id, message_id)
        if info[0] == "go_prev":
            learn_type = info[1]
            learning_id = info[2]
            prev_id = found_prev_learning(user_id, learning_id, learn_type)
            if prev_id:
                to_send, keyboard, path = build_learn(company_id, position_id, learn_type, prev_id)
                edit_media(user_id, to_send, message_id, keyboard, path)
        elif info[0] == "go_question":
            learn_type = info[1]
            question_stage = int(info[2])
            to_send, keyboard, path = build_learn(company_id, position_id, learn_type, question_stage, False)
            edit_media(user_id, to_send, message_id, keyboard, path)
        elif info[0] == "check_answer":
            learn_type = info[1]
            answer_id = info[2]
            correct_questions = info[3].split(",")
            learning_id = get_learn_id_by_answer(answer_id)
            state_num = get_learn_state(user_id, learn_type)
            if is_correct(answer_id):
                correct_questions.append(get_question_by_answer(answer_id))
                if get_questions(learning_id, correct_questions):
                    to_send, keyboard, path = build_learn(company_id, position_id, learn_type, state_num, False,
                                                          correct_questions)
                    edit_media(user_id, to_send, message_id, keyboard, path)
                else:
                    if learning_id == get_last_state(company_id, position_id, learn_type):
                        set_state(user_id, learn_type, 0)
                        edit_media(user_id, "Поздравляем! Вы прошли все блоки этого комплекса!", message_id)
                    else:
                        next_id = found_next_learning(user_id, learning_id, learn_type)
                        if learning_id == get_learn_state(user_id, learn_type):
                            set_state(user_id, learn_type, next_id)
                        to_send, keyboard, path = build_learn(company_id, position_id, learn_type, next_id)
                        edit_media(user_id, to_send, message_id, keyboard, path)
            else:
                bot.answer_callback_query(call.id, "Неверный ответ")
                to_send, keyboard, path = build_learn(company_id, position_id, learn_type, state_num)
                edit_media(user_id, to_send, message_id, keyboard, path)
        elif info[0] == "finish":
            learn_type = info[1]
            set_state(user_id, learn_type, 0)
            edit_media(user_id, "Поздравляем! Вы прошли все блоки этого комплекса!", message_id)


def message_to_admin(message):
    chat_id = message.chat.id
    try:
        text = message.text
    except:
        bot.send_message(chat_id, "Неверный формат", reply_markup=main_k)
        return
    if text == back_k.keyboard[0][0]["text"] or text == "/start":
        bot.send_message(chat_id, "Отмена", reply_markup=main_k)
        return
    new_message(chat_id, text, get_company(chat_id), 0)
    bot.send_message(chat_id, "Сообщение отправлено, ожидайте ответа", reply_markup=main_k)


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


def build_learn(company_id, position_id, learn_type, learning_id, base=True, answered_questions=None):
    if answered_questions is None:
        answered_questions = [-1]
    last_state = get_last_state(company_id, position_id, learn_type)
    first_state = get_first_state(company_id, position_id, learn_type)
    info = get_learn(learning_id)
    questions = get_questions(learning_id, answered_questions)
    answers = []
    if not base:
        answers = get_answers(questions[0][0])
    send_text = ""
    keyboard = InlineKeyboardMarkup()
    path = []
    if last_state:
        if base:
            path = get_learning_file(learning_id)
            if path:
                path = f"./files/{company_id}/{path[0]}_{path[1]}"
            send_text += f"{info}"
            if questions:
                if learning_id != first_state:
                    keyboard.add(InlineKeyboardButton("⬅", callback_data=f"go_prev {learn_type} {learning_id}"),
                                 InlineKeyboardButton("❓", callback_data=f"go_question {learn_type} {learning_id}"))
                else:
                    keyboard.add(InlineKeyboardButton("❓", callback_data=f"go_question {learn_type} {learning_id}"))
            else:
                if learning_id != first_state:
                    if learning_id != last_state:
                        keyboard.add(InlineKeyboardButton("⬅", callback_data=f"go_prev {learn_type} {learning_id}"),
                                     InlineKeyboardButton("➡", callback_data=f"go_next {learn_type} {learning_id}"))
                    else:
                        keyboard.add(InlineKeyboardButton("⬅", callback_data=f"go_prev {learn_type} {learning_id}"),
                                     InlineKeyboardButton("🏁", callback_data=f"finish {learn_type}"))
                else:
                    if learning_id != last_state:
                        keyboard.add(InlineKeyboardButton("➡", callback_data=f"go_next {learn_type} {learning_id}"))
                    else:
                        keyboard.add(InlineKeyboardButton("🏁", callback_data=f"finish {learn_type}"))
        else:
            send_text += f"{questions[0][1]}"
            for i in answers:
                keyboard.add(InlineKeyboardButton(i[1],
                                                  callback_data=f"check_answer {learn_type} {i[0]} "
                                                                f"{','.join([str(i) for i in answered_questions])}"))

    else:
        send_text = "Информации ещё нет"
    return send_text, keyboard, path


def build_profile(user_id):
    company_id = get_company(user_id)
    company = get_company_by_id(company_id)
    position_id, position = get_user_position(user_id)
    percents = []
    count_position = [i[0] for i in get_learning_ids(company, position_id, "position")]
    count_users = [i[0] for i in get_learning_ids(company, position_id, "users")]
    count_products = [i[0] for i in get_learning_ids(company, position_id, "products")]
    count_company = [i[0] for i in get_learning_ids(company, position_id, "company")]
    all_users = get_all_users(company_id)
    for i in all_users:
        if i[0] != user_id:
            continue
        percents = [100 if not i[3] else 0 if i[3] == -1 else count_position.index(i[3]) * 100 // len(
            count_position) if count_position else 0,
         100 if not i[4] else 0 if i[4] == -1 else count_users.index(i[4]) * 100 // len(
             count_users) if count_users else 0,
         100 if not i[5] else 0 if i[5] == -1 else count_products.index(i[5]) * 100 // len(
             count_products) if count_products else 0,
         100 if not i[6] else 0 if i[6] == -1 else count_company.index(i[6]) * 100 // len(
             count_company) if count_company else 0]
        break
    text = f"{position} компании {company}\n\n" \
           f"Прогресс по обучению:\n<pre>" \
           f"💼Должность:  {percents[0]}%\n"\
           f"👥Сотрудники: {percents[1]}%\n"\
           f"📦Продукты:   {percents[2]}%\n"\
           f"ℹО компании: {percents[3]}%\n</pre>"
    return text


def send_media(user_id, caption, keyboard, path=None):
    if path:
        file_extension = path[path.rfind("."):]
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
            bot.send_photo(chat_id=user_id, photo=open(path, 'rb'), caption=caption, reply_markup=keyboard)
        elif file_extension in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mpeg']:
            bot.send_video(chat_id=user_id, video=open(path, 'rb'), caption=caption, reply_markup=keyboard)
        elif file_extension in ['.mp3', '.wav', '.ogg', '.aac']:
            bot.send_audio(chat_id=user_id, audio=open(path, 'rb'), caption=caption, reply_markup=keyboard)
        else:
            bot.send_document(chat_id=user_id, document=open(path, 'rb'), caption=caption, reply_markup=keyboard)
    else:
        bot.send_message(chat_id=user_id, text=caption, reply_markup=keyboard)


def edit_media(user_id, caption, message_id, keyboard=None, path=None):
    if path:
        try:
            file_extension = path[path.rfind("."):]
            bot.delete_message(user_id, message_id)
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
                bot.send_photo(user_id, photo=open(path, 'rb'), caption=caption, reply_markup=keyboard)
            elif file_extension in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mpeg']:
                bot.send_video(user_id, video=open(path, 'rb'), caption=caption, reply_markup=keyboard)
            elif file_extension in ['.mp3', '.wav', '.ogg', '.aac']:
                bot.send_audio(user_id, audio=open(path, 'rb'), caption=caption, reply_markup=keyboard)
            else:
                bot.send_document(user_id, document=open(path, 'rb'), caption=caption, reply_markup=keyboard)
        except Exception as e:
            print(e)
    else:
        try:
            bot.edit_message_text(chat_id=user_id, text=caption, message_id=message_id, reply_markup=keyboard)
        except:
            bot.delete_message(user_id, message_id)
            bot.send_message(chat_id=user_id, text=caption, reply_markup=keyboard)
