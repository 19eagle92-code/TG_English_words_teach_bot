print("Hello! I am an English words teach bot!")

from dotenv import load_dotenv
import os
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types, custom_filters
from telebot.asyncio_storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
import telebot.async_telebot as telebot
import sys
import os
import random

# Добавляем родительскую директорию в путь Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ENG_words_teach_bot_code.db_tables_create import (
    create_tables,
    Base,
    User,
    RussianWord,
    EnglishWord,
)

from ENG_words_teach_bot_code.def_translate import translate_word

load_dotenv()
TOKEN = os.getenv("TG_BOT_TOKEN")
# TOKEN = input("Insert your TG token:") #для проверки на стороннем боте


bot = AsyncTeleBot(TOKEN)

known_users = []
userStep = {}
buttons = []


# async def show_hint(*lines):
#     """Функция формирования многострочного сообщения"""
#     return "\n".join(lines)


# def show_target(data):
#     """Функция формирования строки ответа"""
#     return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = "Добавить слово 📥"
    DELETE_WORD = "Удалить слово📤"
    NEXT_CARD = "Дальше ⏭️"


# Handle '/start'
@bot.message_handler(commands=["start"])
async def send_welcome(message):
    user = message.from_user
    name = user.first_name
    text = f"Hi {name}, I am ENG_words_teach_bot. \nLet's learn ENGLISH words! Please choose: \n/lesson - to start learning words \nor \n/help to know what i can"

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    button_help = types.InlineKeyboardButton(
        text="Help 📎", callback_data="help"  # Данные, которые придут при нажатии
    )

    button_lesson = types.InlineKeyboardButton(
        text="Lesson 📖", callback_data="/lesson"
    )

    keyboard.add(button_help, button_lesson)
    await bot.reply_to(message, text, reply_markup=keyboard)


# обработканажатий на кнопки help и lesson
@bot.callback_query_handler(func=lambda call: True)
async def handle_callback(call):
    # call.data содержит callback_data из кнопки
    if call.data == "help":
        user = call.from_user
        name = user.first_name
        text = f"{name}, I'll help you learn English words. Just add the ones you want to learn: \n/lesson - command to start learning words \nДобавить слово 📥 -add words to my database \nУдалить слово📤 -удалить выученные слова из базы данных \nДальше ⏭️ - next card with a word"
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)

    elif call.data == "lesson":
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, "Lets start lesson")


# @bot.message_handler(commands=["help"])
# async def send_welcome(message):
#     user = message.from_user
#     name = user.first_name
#     text = f"{name}, I'll help you learn English words. Just add the ones you want to learn: \n/lesson - command to start learning words \nДобавить слово 📥 -add words to my database \nУдалить слово📤 -удалить выученные слова из базы данных \nДальше ⏭️ - next card with a word"
#     await bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["lesson"])
async def send_welcome(message):
    user = message.from_user
    name = user.first_name
    text = f"Hi {name}, abra kadabra"
    await bot.reply_to(message, text)


@bot.message_handler(commands=["cards", "start"])
def create_cards(message):
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        bot.send_message(cid, "Hello, stranger, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []
    target_word = "Peace"  # брать из БД
    translate = "Мир"  # брать из БД
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = ["Green", "White", "Hello", "Car"]  # брать из БД
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["target_word"] = target_word
        data["translate_word"] = translate
        data["other_words"] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        print(data["target_word"])  # удалить из БД


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1
    print(message.text)  # сохранить в БД


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    await bot.reply_to(message, message.text)


if __name__ == "__main__":
    print("Async Bot is running")
    asyncio.run(bot.polling())
