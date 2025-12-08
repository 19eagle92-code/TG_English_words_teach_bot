# from unittest import result
# from dotenv import load_dotenv
# import os
# import asyncio
# from telebot.async_telebot import AsyncTeleBot
# from telebot import types, custom_filters
# from telebot.asyncio_storage import StateMemoryStorage
# from telebot.handler_backends import State, StatesGroup
# import telebot.async_telebot as telebot
# import sys
# import os
# import random
print("Hello! I am an English words teach bot!")

import asyncio
import os
import sys
import random
from dotenv import load_dotenv

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot import custom_filters

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
russian_word = {}
lesson_right_word = {}
lesson_wrong_words = {}

create_tables(engine)


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

    button_help = types.InlineKeyboardButton(text="Help 📎", callback_data="help")
    button_lesson = types.InlineKeyboardButton(text="Lesson 📖", callback_data="lesson")
    button_info = types.InlineKeyboardButton(text="Info ℹ️", callback_data="info")
    button_add = types.KeyboardButton("Добавить слово 📥")
    button_delete = types.KeyboardButton("Удалить слово 📤")
    button_cancel = types.KeyboardButton("Отмена")

    keyboard.add(button_help, button_lesson, button_info)
    keyboard_settings.add(button_add, button_delete, button_cancel)

    # Заменяем bot.reply_to() на bot.send_message()
    await bot.send_message(chat_id, text, reply_markup=keyboard)
    await bot.send_message(
        chat_id, "Выберите действие из меню ниже:", reply_markup=keyboard_settings
    )


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
        await show_next_card(call.message.chat.id, call.message)

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
    if count is False:
        text = "❌ Пользователь не найден"
    elif count == 0:
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
    await bot.send_message(chat_id, text)


@bot.message_handler(commands=["help"])
async def send_help(message):
    name = message.from_user.first_name
    chat_id = message.chat.id
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
    await bot.send_message(chat_id, text)


@bot.message_handler(func=lambda m: m.text == "Добавить слово 📥")
async def add_word_button(message: types.Message):
    """получаем слово от пользователя по кнопке"""
    chat_id = message.chat.id
    user_states[chat_id] = "waiting_for_word"
    await bot.send_message(chat_id, "Введите русское слово для добавления в словарь:")


@bot.message_handler(commands=["add"])
async def add_word(message: types.Message):
    """получаем слово от пользователя по команде"""
    chat_id = message.chat.id
    user_states[chat_id] = "waiting_for_word"
    await bot.send_message(chat_id, "Введите русское слово для добавления в словарь:")


@bot.message_handler(func=lambda message: True)
async def handle_all_messages_add(message: types.Message):
    chat_id = message.chat.id

    if message.text.startswith("/"):
        await bot.send_message(
            chat_id, "‼️ Сначала завершите текущую операцию (/cancel)"
        )
        return

    if chat_id in user_states and user_states[chat_id] == "waiting_for_word":
        russian_word = message.text.strip()
        reg_russian_word = russian_word.lower()

        is_unique, message_text = uniqe_word(reg_russian_word, chat_id)

        if not is_unique:
            del user_states[chat_id]
            await bot.send_message(
                chat_id, f"Слово '{russian_word}' уже существует в базе"
            )
            return

        trans_word_1, trans_word_2 = translate_word(reg_russian_word)

        if trans_word_1 is None or not trans_word_1:
            await bot.send_message(
                chat_id,
                f"❌ Ошибка при переводе слова '{russian_word}'.\n\n"
                " Проверьте написание и попробуйте ввести слово еще раз:",
            )
            return

        success = add_word_with_translations(
            ru_word=reg_russian_word,
            chat_id=chat_id,
            trans_word_1=trans_word_1,
            trans_word_2=trans_word_2,
        )

        if success:
            if trans_word_2:
                await bot.send_message(
                    chat_id,
                    f" Слово '{russian_word}' успешно добавлено ✅\n\n"
                    f"  Переводится как '{trans_word_1}' или '{trans_word_2}' ",
                )
            else:
                await bot.send_message(
                    chat_id,
                    f" Слово '{russian_word}' успешно добавлено ✅\n\n"
                    f"  Переводится как '{trans_word_1}'",
                )
        else:
            await bot.send_message(
                chat_id, f"❌ Ошибка при добавлении слова '{russian_word}'"
            )

        if chat_id in user_states:
            del user_states[chat_id]


async def start_delete_process(message: types.Message):
    """Общая функция для начала удаления"""
    chat_id = message.chat.id
    user_states[chat_id] = "waiting_for_word_to_delete"
    await bot.send_message(chat_id, "Введите русское слово для удаления из словаря:")


@bot.message_handler(func=lambda m: m.text == "Удалить слово 📤")
async def delete_word_button(message: types.Message):
    await start_delete_process(message)


@bot.message_handler(commands=["delete"])
async def delete_word_command(message: types.Message):
    await start_delete_process(message)


@bot.message_handler(func=lambda message: True)
async def handle_all_messages_delete(message: types.Message):
    chat_id = message.chat.id

    if chat_id in user_states and user_states[chat_id] == "waiting_for_word_to_delete":
        russian_word = message.text.strip()
        reg_russian_word = russian_word.lower()

        is_unique, msg = uniqe_word(reg_russian_word, chat_id)

        if not is_unique and msg == "Слово уже существует":
            deleted = delete_word(reg_russian_word, chat_id)
            if deleted:
                await bot.send_message(chat_id, f" Слово '{russian_word}' удалено✅")
            else:
                await bot.send_message(chat_id, f"❌ Ошибка при удалении")
        elif not is_unique:
            await bot.send_message(chat_id, f"❌ {msg}")
        else:
            await bot.send_message(chat_id, f"ℹ️ Слово '{russian_word}' не найдено")

        if chat_id in user_states:
            del user_states[chat_id]


@bot.message_handler(commands=["cancel"])
async def cancel_command(message: types.Message):
    chat_id = message.chat.id
    if chat_id in user_states:
        del user_states[chat_id]
        await bot.send_message(chat_id, "✅ Операция отменена")
    else:
        await bot.send_message(chat_id, "Нечего отменять")


@bot.message_handler(func=lambda m: m.text == "Отмена")
async def cancel_button(message: types.Message):
    chat_id = message.chat.id
    if chat_id in user_states:
        del user_states[chat_id]
        await bot.send_message(chat_id, "✅ Операция отменена")


async def show_next_card(chat_id, message=None):
    """Показать следующую карточку (общая логика)"""
    global russian_word, lesson_right_word, lesson_wrong_words

    # очищаем перед вызовом функции
    if (
        chat_id in russian_word
        and chat_id in lesson_right_word
        and chat_id in lesson_wrong_words
    ):
        del russian_word[chat_id]
        del lesson_right_word[chat_id]
        del lesson_wrong_words[chat_id]

    result = random_right_ru_en_couple(chat_id)

    if result is None:
        await bot.send_message(
            chat_id, "📝 У вас нет слов в словаре. Добавьте слова сначала!"
        )
        return
    else:
        ru_word, right_translation, wrong_translations = result

        russian_word[chat_id] = ru_word
        lesson_right_word[chat_id] = right_translation
        lesson_wrong_words[chat_id] = wrong_translations

    keyboard_cards = types.InlineKeyboardMarkup(row_width=2)

    button_right = types.InlineKeyboardButton(
        text=right_translation,
        callback_data="right",  # Данные, которые придут при нажатии
    )

    if len(lesson_wrong_words[chat_id]) != 3:
        del russian_word[chat_id]
        del lesson_right_word[chat_id]
        del lesson_wrong_words[chat_id]
        await bot.send_message(chat_id, "Слов недостаточно или слишком много")
        return

    button_wrong_1 = types.InlineKeyboardButton(
        text=lesson_wrong_words[chat_id][0], callback_data="wrong_1"
    )
    button_wrong_2 = types.InlineKeyboardButton(
        text=lesson_wrong_words[chat_id][1], callback_data="wrong_2"
    )
    button_wrong_3 = types.InlineKeyboardButton(
        text=lesson_wrong_words[chat_id][2], callback_data="wrong_3"
    )
    answers = [button_wrong_1, button_wrong_2, button_wrong_3, button_right]
    random.shuffle(answers)
    button_next = types.InlineKeyboardButton(text="Дальше⏭️", callback_data="next")
    text = f"Найдите правильный перевод слова {russian_word[chat_id]}"
    keyboard_cards.add(*answers, button_next)

    if message:
        await bot.send_message(chat_id, text, reply_markup=keyboard_cards)


@bot.message_handler(commands=["lesson", "next"])
async def lesson_command(message):
    await show_next_card(message.chat.id, message)


@bot.callback_query_handler(func=lambda call: True)
async def handle_callback_lesson(call):

    if call.data == "right":

        chat_id = call.message.chat.id
        if chat_id not in lesson_right_word:
            await bot.answer_callback_query(call.id, "❌ Урок устарел")
            return

        text = "Вы совершенно правы!✅ "
        await bot.answer_callback_query(call.id, text)
        await asyncio.sleep(1)
        await show_next_card(call.message.chat.id, call.message)

    elif call.data == "wrong_1":
        text = "Ответ не верный, попробуйте еще раз"
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)
    elif call.data == "wrong_2":
        text = "Ответ не верный, попробуйте еще раз"
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)
    elif call.data == "wrong_3":
        text = "Ответ не верный, попробуйте еще раз"
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, text)
    elif call.data == "next":
        text = "Переходим к следующему слову"
        await bot.answer_callback_query(call.id)
        await asyncio.sleep(1)
        await show_next_card(call.message.chat.id, call.message)


print(user_states)  # хранение состояний
print(russian_word)
print(lesson_right_word)
print(lesson_wrong_words)
if __name__ == "__main__":
    print("Async Bot is running")
    asyncio.run(bot.polling())
