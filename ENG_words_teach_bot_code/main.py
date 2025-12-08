print("Hello! I am an English words teach bot!")

import asyncio
import os
import sys
import random
from types import DynamicClassAttribute
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

default_words = [
    "зеленый",
    "машина",
    "снег",
    "дом",
    "солнце",
    "книга",
    "вода",
    "любовь",
    "работа",
    "время",
]


# Хранение состояния пользователей
user_states = {}  # {chat_id: "state"}

# Данные для уроков (глобальные, но с защитой от race conditions)
russian_word = {}  # {chat_id: "русское слово"}
lesson_right_word = {}  # {chat_id: "правильный перевод"}
lesson_wrong_words = (
    {}
)  # {chat_id: ["неправильный 1", "неправильный 2", "неправильный 3"]}

# Блокировки для защиты от одновременных операций с уроками (бустрых нажатий)
lesson_locks = {}

create_tables(engine)

# ========== КОМАНДЫ ==========


@bot.message_handler(commands=["start"])
async def send_welcome(message):
    """Обработка команды /start"""
    user = message.from_user
    user_name = user.first_name
    chat_id = message.chat.id

    # Добавляем пользователя в БД
    add_client(chat_id, user_name)

    # Добавляем слова по умолчанию с помощью отдельной функции
    success = add_words_to_user(chat_id, default_words)

    text = (
        f"👋 Привет {user_name}! Я English words teacher.\n"
        f"Давай изучать английские слова!\n\n"
    )

    if success:
        text += "✅ Ваш словарь пополнен базовыми словами!\n\n"
    else:
        text += "⚠️ Не удалось добавить некоторые слова\n\n"

    text += (
        f"Выбери:\n"
        f"• /lesson - начать урок\n"
        f"• /help - узнать, что я могу\n"
        f"• /info - узнать, сколько слов вы изучаете"
    )

    # Inline-клавиатура (кнопки под сообщением)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    button_help = types.InlineKeyboardButton(text="Help 📎", callback_data="help")
    button_lesson = types.InlineKeyboardButton(text="Lesson 📖", callback_data="lesson")
    button_info = types.InlineKeyboardButton(text="Info ℹ️", callback_data="info")
    keyboard.add(button_help, button_lesson, button_info)

    # Reply-клавиатура (постоянное меню внизу)
    keyboard_settings = types.ReplyKeyboardMarkup(
        resize_keyboard=True, row_width=2, one_time_keyboard=False
    )
    button_add = types.KeyboardButton("Добавить слово 📥")
    button_delete = types.KeyboardButton("Удалить слово 📤")
    button_cancel = types.KeyboardButton("Отмена ⛔")
    button_lesson_reply = types.KeyboardButton("Lesson 📖")
    keyboard_settings.add(button_add, button_delete)
    keyboard_settings.add(button_cancel)
    keyboard_settings.add(button_lesson_reply)

    await bot.send_message(chat_id, text, reply_markup=keyboard)
    await bot.send_message(
        chat_id,
        "Так же можете выбрать действие из меню ниже:",
        reply_markup=keyboard_settings,
    )


@bot.message_handler(commands=["help"])
async def send_help(message):
    """Обработка команды /help"""
    name = message.from_user.first_name
    chat_id = message.chat.id

    text = (
        f"{name}, я помогу тебе учить английские слова!\n\n"
        "Основные команды:\n"
        "• /start - Начать работу с ботом\n"
        "• /info - Узнать количество изучаемых слов\n"
        "• /add - Добавить новое слово в словарь\n"
        "• /delete - Удалить выученное слово\n"
        "• /cancel - Прервать операцию\n"
        "• /lesson - Начать урок\n"
        "• /next - Следующее слово\n\n"
        "🎓 Учи слова регулярно для лучшего запоминания!"
    )

    await bot.send_message(chat_id, text)


@bot.message_handler(commands=["info"])
async def send_info(message):
    """Обработка команды /info"""
    chat_id = message.chat.id
    count = count_user_english_words(chat_id)

    if count is False:
        text = "❌ Пользователь не найден"
    elif count == 0:
        text = "У вас еще нет добавленных слов 🥲"
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


@bot.message_handler(commands=["add"])
async def add_word_command(message):
    """Обработка команды /add"""
    chat_id = message.chat.id
    user_states[chat_id] = "waiting_for_word"
    await bot.send_message(chat_id, "Введите русское слово для добавления в словарь:")


@bot.message_handler(commands=["delete"])
async def delete_word_command(message):
    """Обработка команды /delete"""
    chat_id = message.chat.id
    user_states[chat_id] = "waiting_for_word_to_delete"
    await bot.send_message(chat_id, "Введите русское слово для удаления из словаря:")


@bot.message_handler(commands=["cancel"])
async def cancel_command(message):
    """Обработка команды /cancel"""
    chat_id = message.chat.id
    if chat_id in user_states:
        user_states.pop(chat_id)
        await bot.send_message(chat_id, "✅ Операция отменена")
    else:
        await bot.send_message(chat_id, "ℹ️ Нет активных операций для отмены")


@bot.message_handler(commands=["lesson", "next"])
async def lesson_command(message):
    """Обработка команд /lesson и /next"""
    await show_next_card(message.chat.id, message)


# ========== ОБРАБОТКА КНОПОК REPLY-КЛАВИАТУРЫ ==========


@bot.message_handler(
    func=lambda m: m.text
    in ["Добавить слово 📥", "Удалить слово 📤", "Отмена ⛔", "Lesson 📖"]
)
async def handle_reply_buttons(message):
    """Обработка кнопок Reply-клавиатуры (постоянное меню внизу)"""
    chat_id = message.chat.id

    if message.text == "Добавить слово 📥":
        user_states[chat_id] = "waiting_for_word"
        await bot.send_message(chat_id, "Введите русское слово для добавления:")

    elif message.text == "Удалить слово 📤":
        user_states[chat_id] = "waiting_for_word_to_delete"
        await bot.send_message(chat_id, "Введите русское слово для удаления:")

    elif message.text == "Отмена ⛔":
        await cancel_command(message)

    elif message.text == "Lesson 📖":
        await lesson_command(message)


# ========== ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ==========


@bot.message_handler(func=lambda message: True, content_types=["text"])
async def handle_text_messages(message: types.Message):
    """
    Обрабатывает ВСЕ текстовые сообщения, которые не попали в другие обработчики.
    Сюда попадают только сообщения, которые не команды и не кнопки Reply-клавиатуры.
    """
    chat_id = message.chat.id
    text = message.text.strip()

    # Если пользователь в состоянии ожидания
    if chat_id in user_states:
        state = user_states[chat_id]

        # Защита: игнорируем команды во время ожидания
        if text.startswith("/"):
            await bot.send_message(
                chat_id, "⚠️ Завершите текущую операцию или используйте /cancel"
            )
            return

        if state == "waiting_for_word":
            await process_add_word(chat_id, text)
            return

        elif state == "waiting_for_word_to_delete":
            await process_delete_word(chat_id, text)
            return

    # Если не состояние и не команда - показываем подсказку
    await bot.send_message(
        chat_id,
        "Используйте команды из меню, /help или начните сначала /start",
        reply_markup=types.ReplyKeyboardRemove(),
    )


async def process_add_word(chat_id: int, word_text: str):
    """Обработка добавления слова"""
    # Проверка слова
    if not word_text or len(word_text) > 50:
        await bot.send_message(
            chat_id, "❌ Некорректное слово. Используйте слова длиной до 50 символов."
        )
        user_states.pop(chat_id, None)
        return

    reg_word = word_text.lower()

    # Проверка уникальности
    is_unique, msg = uniqe_word(reg_word, chat_id)

    if not is_unique:
        user_states.pop(chat_id, None)
        await bot.send_message(chat_id, f"Слово '{word_text}' уже есть в словаре")
        return

    # Перевод слова
    translation_1, translation_2 = translate_word(reg_word)

    if not translation_1:
        await bot.send_message(
            chat_id,
            f"❌ Не удалось перевести '{word_text}'. Проверьте написание и введите снова:.",
        )
        # НЕ удаляем состояние, можем попробовать снова
        return

    # Сохранение в БД
    success = add_word_with_translations(
        ru_word=reg_word,
        chat_id=chat_id,
        trans_word_1=translation_1,
        trans_word_2=translation_2,
    )

    if success:
        if translation_2:
            await bot.send_message(
                chat_id,
                f"✅ Слово добавлено!\n\n"
                f"**{word_text}** переводится как **{translation_1}** или **{translation_2}**\n\n"
                f"Введите следующее русское слово для добавления: \n\n"
                f"P.s. /cancel или Отмена ⛔ - для отмены",
                parse_mode="Markdown",
            )
        else:
            await bot.send_message(
                chat_id,
                f"✅ Слово добавлено!\n\n**{word_text}** переводится как **{translation_1}**\n\n"
                f"Введите следующее русское слово для добавления: \n\n"
                f"P.s. /cancel или Отмена ⛔ - для отмены",
                parse_mode="Markdown",
            )
        return

    else:
        await bot.send_message(chat_id, "❌ Ошибка при сохранении в базу данных")

    # Очищаем состояние
    user_states.pop(chat_id, None)


async def process_delete_word(chat_id: int, word_text: str):
    """Обработка удаления слова"""
    reg_word = word_text.lower()

    is_unique, msg = uniqe_word(reg_word, chat_id)

    # Если слово НЕ уникально (т.е. уже существует) - удаляем
    if not is_unique and msg == "Слово уже существует":
        deleted = delete_word(reg_word, chat_id)
        if deleted:
            await bot.send_message(chat_id, f"✅ Слово '{word_text}' удалено")
        else:
            await bot.send_message(chat_id, "❌ Ошибка при удалении")
    elif not is_unique:
        await bot.send_message(chat_id, f"ℹ️ {msg}")
    else:
        await bot.send_message(chat_id, f"ℹ️ Слово '{word_text}' не найдено")

    # Очищаем состояние
    user_states.pop(chat_id, None)


# ========== ОБРАБОТКА CALLBACK (INLINE-КНОПОК) ==========


@bot.callback_query_handler(func=lambda call: True)
async def unified_callback_handler(call):
    """
    Единый обработчик ВСЕХ callback (нажатий на inline-кнопки)
    """
    # Меню (help, lesson, info) - обрабатываем здесь
    if call.data in ["help", "lesson", "info"]:
        await handle_menu_callback(call)
    else:
        # Урок (right, wrong_1, wrong_2, wrong_3, next)
        await handle_lesson_callback(call)


async def handle_menu_callback(call):
    """Обработка callback-ов меню (help, lesson, info)"""
    chat_id = call.message.chat.id

    if call.data == "help":
        name = call.from_user.first_name
        text = (
            f"{name}, я помогу тебе учить английские слова!\n\n"
            "Основные команды:\n"
            "• /start - Начать работу с ботом\n"
            "• /info - Узнать количество изучаемых слов\n"
            "• /add - Добавить новое слово в словарь\n"
            "• /delete - Удалить выученное слово\n"
            "• /cancel - Прервать операцию\n"
            "• /lesson - Начать урок\n"
            "• /next - Следующее слово\n\n"
            "🎓 Учи слова регулярно для лучшего запоминания!"
        )
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, text)

    elif call.data == "lesson":
        await bot.answer_callback_query(call.id)
        await show_next_card(chat_id, call.message)

    elif call.data == "info":
        count = count_user_english_words(chat_id)
        if not count or count == 0:
            text = "У вас еще нет добавленных слов 🥲"
        else:
            # Склонение слова "слов"
            if count % 10 == 1 and count % 100 != 11:
                word = "слово"
            elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
                word = "слова"
            else:
                word = "слов"
            text = f"📊 Изучаете {count} {word}"
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, text)


async def handle_lesson_callback(call):
    """Обработка callback-ов урока (right, wrong_*, next)"""
    chat_id = call.message.chat.id

    # Проверяем, что урок активен для этого пользователя
    if chat_id not in lesson_right_word:
        await bot.answer_callback_query(call.id, "❌ Урок неактивен. Начните новый.")
        return

    if call.data == "right":
        await bot.answer_callback_query(call.id, "✅ Верно!")
        await asyncio.sleep(0.5)  # Небольшая задержка
        await show_next_card(chat_id, call.message)

    elif call.data.startswith("wrong_"):
        # Все неправильные ответы обрабатываем одинаково
        await bot.answer_callback_query(call.id, "❌ Неверно, попробуйте ещё")

    elif call.data == "next":
        await bot.answer_callback_query(call.id, "⏭️ Пропускаем...")
        await asyncio.sleep(0.5)
        await show_next_card(chat_id, call.message)


# ========== ФУНКЦИИ УРОКОВ ==========


async def show_next_card(chat_id, message=None):
    """
    Показать следующую карточку для урока.
    Защищено от race conditions с помощью блокировок.
    """
    # Создаём или получаем блокировку для этого пользователя
    if chat_id not in lesson_locks:
        lesson_locks[chat_id] = asyncio.Lock()

    # Блокируем - только один урок одновременно для этого пользователя
    async with lesson_locks[chat_id]:
        # Очищаем предыдущее состояние урока
        russian_word.pop(chat_id, None)
        lesson_right_word.pop(chat_id, None)
        lesson_wrong_words.pop(chat_id, None)

        # Получаем случайное слово для урока
        result = random_right_ru_en_couple(chat_id)

        if result is None:
            await bot.send_message(
                chat_id, "📝 У вас нет слов в словаре. Добавьте слова через /add"
            )
            return

        ru_word, right_trans, wrong_trans_list = result

        # Валидация: нужно минимум 3 неправильных варианта
        if not wrong_trans_list or len(wrong_trans_list) < 3:
            await bot.send_message(
                chat_id,
                "⚠️ Недостаточно слов для урока. "
                "Нужно минимум 4 разных слова в словаре.",
            )
            return

        # Сохраняем данные урока
        russian_word[chat_id] = ru_word
        lesson_right_word[chat_id] = right_trans
        lesson_wrong_words[chat_id] = wrong_trans_list[:3]  # Берём только 3 варианта

        # Создаём клавиатуру с вариантами ответа
        keyboard = types.InlineKeyboardMarkup(row_width=2)

        # 4 варианта ответа (1 правильный + 3 неправильных)
        buttons = [
            types.InlineKeyboardButton(right_trans, callback_data="right"),
            types.InlineKeyboardButton(wrong_trans_list[0], callback_data="wrong_1"),
            types.InlineKeyboardButton(wrong_trans_list[1], callback_data="wrong_2"),
            types.InlineKeyboardButton(wrong_trans_list[2], callback_data="wrong_3"),
        ]

        random.shuffle(buttons)

        # Добавляем кнопку "Дальше"
        buttons.append(types.InlineKeyboardButton("Дальше ⏭️", callback_data="next"))

        keyboard.add(*buttons)

        # Отправляем сообщение с карточкой
        await bot.send_message(
            chat_id,
            f"📖 Найдите правильный перевод слова:\n\n**{ru_word}**",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


if __name__ == "__main__":
    print("🤖 Async Bot is running...")
    try:
        asyncio.run(bot.polling())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
