from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

back_k = ReplyKeyboardMarkup(resize_keyboard=True)
back = KeyboardButton("Назад")
back_k.add(back)

admin_k = ReplyKeyboardMarkup(resize_keyboard=True)
admin_k.add("Все сотрудники", "Рассылка")

main_k = ReplyKeyboardMarkup(resize_keyboard=True)
main_k.add("👤Мой профиль👤")
main_k.add("💼Должность💼", "👥Сотрудники👥")
main_k.add("📦Продукты компании📦", "ℹ️О компанииℹ️")
main_k.add("❓Задать вопрос❓")

