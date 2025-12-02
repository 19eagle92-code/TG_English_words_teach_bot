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

state_storage = StateMemoryStorage()

bot = AsyncTeleBot(TOKEN, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []


async def show_hint(*lines):
    """Функция формирования многострочного сообщения"""
    return "\n".join(lines)


# def show_target(data):
#     """Функция формирования строки ответа"""
#     return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = "Добавить слово 📥"
    DELETE_WORD = "Удалить слово📤"
    NEXT = "Дальше ⏭️"


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

    button_lesson = types.InlineKeyboardButton(text="Lesson 📖", callback_data="lesson")

    keyboard.add(button_help, button_lesson)
    await bot.reply_to(message, text, reply_markup=keyboard)


@bot.message_handler(commands=["help"])
async def send_welcome(message):
    user = message.from_user
    name = user.first_name
    text = f"{name}, I'll help you learn English words. Just add the ones you want to learn: \n/lesson - command to start learning words \nДобавить слово 📥 -add words to my database \nУдалить слово📤 -удалить выученные слова из базы данных \nДальше ⏭️ - next card with a word"
    await bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["lesson"])
async def send_welcome(message):
    user = message.from_user
    name = user.first_name
    text = f"Hi {name}, abra kadabra"
    await bot.reply_to(message, text)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    await bot.reply_to(message, message.text)


if __name__ == "__main__":
    print("Async Bot is running")
    asyncio.run(bot.polling())
