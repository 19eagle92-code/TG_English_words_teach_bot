import sys
import os
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ENG_words_teach_bot_code.db_tables_create import (
    create_tables,
    Base,
    User,
    RussianWord,
    EnglishWord,
)
from ENG_words_teach_bot_code.def_translate import translate_word
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
import sqlalchemy.exc
from sqlalchemy.orm import Session
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy import func


load_dotenv()
password = os.getenv("SECRET_KEY")

DSN = f"postgresql://postgres:{password}@localhost:5432/english_words_bot"
engine = sqlalchemy.create_engine(DSN)


Session = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    """Контекстный менеджер для сессии"""

    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def add_client(chat_id, user_name):
    """Функция добавления нового пользователя"""
    try:
        with session_scope() as session:
            # Проверяем существование клиента
            user = session.query(User).filter_by(chat_id=chat_id).first()

            if user:
                print(f"Клиент с таким {chat_id} уже существует")
                return False

            # Создаем нового клиента
            new_user = User(chat_id=chat_id, user_name=user_name)
            session.add(new_user)
            session.flush()
            print(f"ID созданного клиента:", new_user.user_id)
            return True

    except sqlalchemy.exc.IntegrityError:
        print("Ошибка: нарушение уникальности данных")
        return False
    except sqlalchemy.exc.SQLAlchemyError as e:
        print(f"Ошибка базы данных: {e}")
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return False


def add_word_with_translations(ru_word, chat_id, trans_word_1, trans_word_2=None):
    """Функция добавляет слово с одним или двумя переводами"""
    try:
        with session_scope() as session:
            user = session.query(User).filter_by(chat_id=chat_id).first()

            if not user:
                print(f"Пользователь {chat_id} не найден")
                return False

            # Собираем непустые переводы
            english_words_list = [EnglishWord(en_word=trans_word_1)]
            if trans_word_2:  # Если есть второй перевод
                english_words_list.append(EnglishWord(en_word=trans_word_2))

            new_ru_word = RussianWord(
                ru_word=ru_word, user_id=user.user_id, english_words=english_words_list
            )

            session.add(new_ru_word)
            # Логируем
            if trans_word_2:
                print(
                    f"Добавлено слово {ru_word} с переводами {trans_word_1}, {trans_word_2}"
                )
            else:
                print(f"Добавлено слово {ru_word} с переводом {trans_word_1}")

            return True

    except sqlalchemy.exc.IntegrityError:
        print("Ошибка: нарушение уникальности данных")
        return False
    except sqlalchemy.exc.SQLAlchemyError as e:
        print(f"Ошибка базы данных: {e}")
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return False


def delete_word(word_to_delete, chat_id):
    """Функция удаления русского слова и его перевода"""
    try:
        with session_scope() as session:
            # Находим клиента в бд
            user = session.query(User).filter_by(chat_id=chat_id).first()

            if not user:
                print(f"Пользователь {chat_id} не найден")
                return False

            russian_word = (
                session.query(RussianWord)
                .filter_by(
                    ru_word=word_to_delete,  # фильтр по удаляемому слову
                    user_id=user.user_id,  # фильтр по пользователю
                )
                .first()
            )

            if russian_word:
                session.delete(russian_word)
                print(f"Слово {word_to_delete} с переводом  успешно удалены")
                return True
            else:
                print(f"Слово '{word_to_delete}' не найдено у пользователя {chat_id}")
                return False

    except sqlalchemy.exc.IntegrityError as e:
        print(f"Ошибка целостности данных при удалении: {e}")
        return False
    except sqlalchemy.exc.SQLAlchemyError as e:
        print(f"Ошибка базы данных: {e}")
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return False


def count_user_english_words(chat_id):
    """Функция подсчета количества изучаемых английских слов"""
    with session_scope() as session:
        user = session.query(User).filter_by(chat_id=chat_id).first()

        if not user:
            print(f"Пользователь  {chat_id} не найден")
            return 0

        count = (
            session.query(func.count(EnglishWord.en_word_id))
            .join(RussianWord, RussianWord.ru_word_id == EnglishWord.ru_word_id)
            .filter(RussianWord.user_id == user.user_id)
            .scalar()
        )

        return count or 0


def count_user_russian_words(chat_id):
    """Функция подсчета количества руских слов в базе"""
    with session_scope() as session:
        user = session.query(User).filter_by(chat_id=chat_id).first()

        if not user:
            print(f"Пользователь  {chat_id} не найден")
            return 0

        count = (
            session.query(func.count(RussianWord.ru_word_id))
            .filter(RussianWord.user_id == user.user_id)
            .scalar()
        )

        return count or 0


def uniqe_word(new_word, chat_id):
    """Функция проверки уникальности слова"""
    # Проверяем что слово не пустое
    if not new_word or not new_word.strip():
        print("Пустое слово")
        return False, "Пустое слово"

    # Нормализуем слово (приводим к нижнему регистру)
    normalized_word = new_word.strip().lower()

    with session_scope() as session:
        user = session.query(User).filter_by(chat_id=chat_id).first()

        if not user:
            print(f"Пользователь с № {chat_id} не найден")
            return False, "Пользователь не найден"

        # Ищем слово у этого пользователя
        existing_word = (
            session.query(RussianWord)
            .filter_by(
                ru_word=normalized_word,  # Ищем нормализованное слово
                user_id=user.user_id,
            )
            .first()
        )

        # Проверяем найдено ли слово
        if existing_word:
            print(f'Слово "{new_word}" уже существует в базе')
            return False, "Слово уже существует"
        else:
            return True, "Слово уникально"
