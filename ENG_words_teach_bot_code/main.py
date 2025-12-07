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

from ENG_words_teach_bot_code.work_with_storage import *

from ENG_words_teach_bot_code.def_translate import translate_word


load_dotenv()
TOKEN = os.getenv("TG_BOT_TOKEN")
# TOKEN = input("Insert your TG token:") #для проверки на стороннем боте

bot = AsyncTeleBot(TOKEN)

user_states = {}  # хранение состояний
russin_word = {}
lesson_right_word = {}
lesson_wrong_words = {}


class Command:
    ADD_WORD = "Добавить слово 📥"
    DELETE_WORD = "Удалить слово📤"
    NEXT_CARD = "Дальше ⏭️"


# Handle '/start'
@bot.message_handler(commands=["start"])
async def send_welcome(message):
    user = message.from_user
    user_name = user.first_name
    chat_id = message.chat.id
    text = f"👋Привет {user_name}! Я English words teacher. \nДавай изучать английские слова! Пожалуйста выбери: \n/lesson - для начала урока \nили \n/help - что бы узнать что я могу \nили \n/info - узнать сколько слов вы сейчас изучаете"
    add_client(chat_id, user_name)

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard_settings = types.ReplyKeyboardMarkup(
        resize_keyboard=True, row_width=2, one_time_keyboard=False
    )

    button_help = types.InlineKeyboardButton(
        text="Help 📎", callback_data="help"  # Данные, которые придут при нажатии
    )

    button_lesson = types.InlineKeyboardButton(text="Lesson 📖", callback_data="lesson")

    button_info = types.InlineKeyboardButton(text="Info ℹ️", callback_data="info")

    button_add = types.KeyboardButton("Добавить слово 📥")
    button_delete = types.KeyboardButton("Удалить слово 📤")
    button_cancel = types.KeyboardButton("Отмена")

    keyboard.add(button_help, button_lesson, button_info)
    keyboard_settings.add(button_add, button_delete, button_cancel)

    await bot.reply_to(message, text, reply_markup=keyboard)
    await bot.reply_to(message, reply_markup=keyboard_settings)


# обработканажатий на кнопки help, lesson и info
@bot.callback_query_handler(func=lambda call: True)
async def handle_callback(call):
    user = call.from_user
    name = user.first_name
    if call.data == "help":
        text = (
            f"{name}, я помогу тебе учить английские слова!\n\n"
            " Основные команды:\n"
            "• /start - Начать работу с ботом\n"
            "• /info - Узнать количество изучаемых слов\n"
            "• /add - Добавить слово 📥 - Добавить новое слово в словарь\n"
            "• /delete - Удалить слово 📤 - Удалить выученное слово\n"
            "• /cancel - Прервать операцию по добавлению или удалению слова \n"
            "• /next - Дальше ⏭️ - Следующее слово для повторения\n"
            "🎓 Учи слова регулярно для лучшего запоминания!"
        )
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)

    elif call.data == "lesson":
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, "Давай начнем урок")

    elif call.data == "info":
        chat_id = call.message.chat.id
        count = count_user_english_words(chat_id)
        if count is False or count == 0:
            text = "У вас еще нет добавленных слов🥲"
        else:
            # Склонение слова "слов"
            if count % 10 == 1 and count % 100 != 11:
                word = "слово"
            elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
                word = "слова"
            else:
                word = "слов"
            text = f"📊 Сейчас вы изучаете {count} английских {word}"
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)


@bot.message_handler(commands=["info"])
async def send_info(message):
    chat_id = message.chat.id
    count = count_user_english_words(chat_id)
    if count is False or count == 0:
        text = "У вас еще нет добавленных слов🥲"
    else:
        # Склонение слова "слов"
        if count % 10 == 1 and count % 100 != 11:
            word = "слово"
        elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
            word = "слова"
        else:
            word = "слов"
        text = f"📊 Сейчас вы изучаете {count} английских {word}"
    await bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["help"])
async def send_help(message):
    name = message.from_user.first_name
    text = (
        f"{name}, я помогу тебе учить английские слова!\n\n"
        " Основные команды:\n"
        "• /start - Начать работу с ботом\n"
        "• /info - Узнать количество изучаемых слов\n"
        "• /add - Добавить слово 📥 - Добавить новое слово в словарь\n"
        "• /delete - Удалить слово 📤 - Удалить выученное слово\n"
        "• /cancel - Отмена - Прервать операцию по добавлению или удалению слова \n"
        "• /next - Дальше ⏭️ - Следующее слово для повторения\n"
        "🎓 Учи слова регулярно для лучшего запоминания!"
    )
    await bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "Добавить слово 📥")
async def add_word_button(message: types.Message):
    """получаем слово от пользователя по кнопке"""
    chat_id = message.chat.id

    # Устанавливаем состояние "ожидаем слово" для пользователя
    user_states[chat_id] = "waiting_for_word"

    await bot.reply_to(message, "Введите русское слово для добавления в словарь:")


@bot.message_handler(commands=["add"])
async def add_word(message: types.Message):
    """получаем слово от пользователя по команде"""
    chat_id = message.chat.id

    # Устанавливаем состояние "ожидаем слово" для пользователя
    user_states[chat_id] = "waiting_for_word"

    await bot.reply_to(message, "Введите русское слово для добавления в словарь:")


@bot.message_handler(func=lambda message: True)  # Обрабатывает все сообщения
async def handle_all_messages(message: types.Message):
    chat_id = message.chat.id

    # Проверяем, находится ли пользователь в состоянии добавления слова
    if chat_id in user_states and user_states[chat_id] == "waiting_for_word":
        # приводим слово к нижнему регистру
        russian_word = message.text.strip()
        reg_russian_word = russian_word.lower()

        # Проверяем уникальность
        is_unique, message_text = uniqe_word(reg_russian_word, chat_id)

        if not is_unique:
            # Удаляем состояние
            del user_states[chat_id]
            await bot.reply_to(message, f"Слово '{russian_word}' уже существует в базе")
            return  # Выходим из функции

        # Получаем перевод
        trans_word_1, trans_word_2 = translate_word(reg_russian_word)

        if trans_word_1 is None or not trans_word_1:
            await message.reply(
                f"❌ Ошибка при переводе слова '{russian_word}'.\n\n"
                " Проверьте написание и попробуйте ввести слово еще раз:"
            )
            return  # Выходим из функции

        # Добавляем в БД
        success = add_word_with_translations(
            ru_word=reg_russian_word,
            chat_id=chat_id,
            trans_word_1=trans_word_1,
            trans_word_2=trans_word_2,
        )

        if success:
            if trans_word_2:
                await message.reply(
                    f" Слово '{russian_word}' успешно добавлено ✅\n\n"
                    f"  Переводится как '{trans_word_1}' или '{trans_word_2}' "
                )
            else:
                await message.reply(
                    f" Слово '{russian_word}' успешно добавлено ✅\n\n"
                    f"  Переводится как '{trans_word_1}'"
                )
        else:
            await message.reply(f"❌ Ошибка при добавлении слова '{russian_word}'")

        if chat_id in user_states:
            del user_states[chat_id]


async def start_delete_process(message: types.Message):
    """Общая функция для начала удаления"""
    chat_id = message.chat.id
    user_states[chat_id] = "waiting_for_word_to_delete"
    await bot.reply_to(message, "Введите русское слово для удаления из словаря:")


@bot.message_handler(func=lambda m: m.text == "Удалить слово 📤")
async def delete_word_button(message: types.Message):
    await start_delete_process(message)


@bot.message_handler(commands=["delete"])
async def delete_word_command(message: types.Message):
    await start_delete_process(message)


@bot.message_handler(func=lambda message: True)  # Обрабатывает все сообщения
async def handle_all_messages(message: types.Message):
    chat_id = message.chat.id

    # Проверяем, находится ли пользователь в состоянии добавления слова
    if chat_id in user_states and user_states[chat_id] == "waiting_for_word_to_delete":
        # приводим слово к нижнему регистру
        russian_word = message.text.strip()
        reg_russian_word = russian_word.lower()

        # Проверяем уникальность
        is_unique, msg = uniqe_word(reg_russian_word, chat_id)

        if not is_unique and msg == "Слово уже существует":
            deleted = delete_word(reg_russian_word, chat_id)
            if deleted:
                await message.reply(f" Слово '{russian_word}' удалено✅")
            else:
                await message.reply(f"❌ Ошибка при удалении")
        elif not is_unique:
            # Другая ошибка (пользователь не найден)
            await message.reply(f"❌ {msg}")
        else:
            # Слово не существует (is_unique == True)
            await message.reply(f"ℹ️ Слово '{russian_word}' не найдено")

        # Удаляем состояние в любом случае
        if chat_id in user_states:
            del user_states[chat_id]


@bot.message_handler(commands=["cancel"])
async def cancel_command(message: types.Message):
    chat_id = message.chat.id
    if chat_id in user_states:
        del user_states[chat_id]
        await message.reply("✅ Операция отменена")


@bot.message_handler(func=lambda m: m.text == "Отмена")
async def cancel_button(message: types.Message):
    chat_id = message.chat.id
    if chat_id in user_states:
        del user_states[chat_id]
        await message.reply("✅ Операция отменена")


@bot.message_handler(func=lambda m: m.text == "Lesson 📖")
async def add_lesson_button(message: types.Message):
    """получаем слово от пользователя по кнопке"""
    chat_id = message.chat.id

    # Устанавливаем состояние "ожидаем слово" для пользователя
    user_states[chat_id] = "waiting_for_word"

    await bot.reply_to(message, "Введите русское слово для добавления в словарь:")


@bot.message_handler(commands=["lesson", "next"])
async def lesson_command(message):

    user = message.from_user
    name = user.first_name
    chat_id = message.chat.id
    # очищаем перед вызовом функции
    del russin_word[chat_id]
    del lesson_right_word[chat_id]
    del lesson_wrong_words[chat_id]

    ru_word, right_translation, wrong_translations = random_right_ru_en_couple(chat_id)

    keyboard_cards = types.InlineKeyboardMarkup(row_width=2)

    button_right = types.InlineKeyboardButton(
        text=right_translation,
        callback_data="right",  # Данные, которые придут при нажатии
    )
    button_wrong_1 = types.InlineKeyboardButton(
        text=wrong_translations[0], callback_data="wrong_1"
    )
    button_wrong_2 = types.InlineKeyboardButton(
        text=wrong_translations[1], callback_data="wrong_2"
    )
    button_wrong_3 = types.InlineKeyboardButton(
        text=wrong_translations[2], callback_data="wrong_3"
    )
    button_next = types.InlineKeyboardButton(text="Дальше⏭️", callback_data="next")

    answers = random.shuffle(
        button_wrong_1, button_wrong_2, button_wrong_3, button_right
    )

    text = f"Найдите правильный перевод слова {ru_word}"

    keyboard_cards.add(answers, button_next)
    await bot.reply_to(message, text, reply_markup=keyboard_cards)


@bot.callback_query_handler(func=lambda call: True)
async def handle_callback_lesson(call):
    user = call.from_user
    name = user.first_name
    chat_id = call.chat.id

    ru_word, right_translation, wrong_translations = random_right_ru_en_couple(chat_id)

    if call.data == "right":
        text = "right"

        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)

    elif call.data == "wrong_1":
        text = "wrong_1"
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)
    elif call.data == "wrong_2":
        text = "wrong_2"
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)
    elif call.data == "wrong_3":
        text = "wrong_3"
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)


if __name__ == "__main__":
    print("Async Bot is running")
    asyncio.run(bot.polling())
