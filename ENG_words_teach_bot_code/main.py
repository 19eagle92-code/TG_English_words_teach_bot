print("Hello! I am an English words teach bot!")

from dotenv import load_dotenv
import os
import asyncio
from telebot.async_telebot import AsyncTeleBot


load_dotenv()
TOKEN = os.getenv("TG_BOT_TOKEN")
# TOKEN = input("Insert your TG token:")

bot = AsyncTeleBot("TOKEN")


# Handle '/start' and '/help'
@bot.message_handler(commands=["help", "start"])
async def send_welcome(message):
    text = "Hi, I am EchoBot.\nJust write me something and I will repeat it!"
    await bot.reply_to(message, text)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    await bot.reply_to(message, message.text)


if __name__ == "__main__":
    print("Bot is running")
    asyncio.run(bot.polling())
