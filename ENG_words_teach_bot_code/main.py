print("Hello! I am an English words teach bot!")

from dotenv import load_dotenv
import os
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types, custom_filters
from telebot.asyncio_storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
import telebot.async_telebot as telebot


load_dotenv()
TOKEN = os.getenv("TG_BOT_TOKEN")
# TOKEN = input("Insert your TG token:")

state_storage = StateMemoryStorage()

bot = AsyncTeleBot(TOKEN, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []


def show_hint(*lines):
    """Функция формирования многострочного сообщения"""
    return "\n".join(lines)


# def show_target(data):
#     """Функция формирования строки ответа"""
#     return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = "Добавить слово 📥"
    DELETE_WORD = "Удалить слово📤"
    NEXT = "Дальше ⏭️"


# Handle '/start' and '/help'
@bot.message_handler(commands=["help📎", "start"])
async def send_welcome(message):
    user = message.from_user
    name = user.first_name
    text = f"Hi {name}, I am ENG_words_teach_bot .\nLet's learn ENGLISH words!"
    await bot.reply_to(message, text)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    await bot.reply_to(message, message.text)


if __name__ == "__main__":
    print("Async Bot is running")
    asyncio.run(bot.polling())
