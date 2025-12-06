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

load_dotenv()
password = os.getenv("SECRET_KEY")

DSN = f"postgresql://postgres:{password}@localhost:5432/english_words_bot"
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)
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


def add_russian_word_with_translation(ru_word, chat_id, translation):
    """Функция добавления русского слова и его перевода"""

    try:
        with session_scope() as session:
            # Находим клиента в бд
            user = session.query(User).filter_by(chat_id=chat_id).first()

            if user:
                # добавляем слова для клиента
                new_ru_word = RussianWord(
                    ru_word=ru_word,
                    user_id=user.user_id,
                    english_words=[
                        EnglishWord(en_word=translation)
                    ],  # Создаем связь сразу
                )
                session.add(new_ru_word)
                print(f"Слово{ru_word} с переводом {translation} -  успешно добавлены")
                return True
            else:
                return False

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
                print(f"Пользователь с № {chat_id} не найден")
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
    """Функция плдсчета количества изучаемых пользователем слов"""
    with session_scope() as session:
        user = session.query(User).filter_by(chat_id=chat_id).first()

        if user:
            print(f"Клиент с таким {chat_id} уже существует")
            return False

        from sqlalchemy import func

        count = (
            session.query(func.count(EnglishWord.en_word_id))
            .join(RussianWord)
            .filter(RussianWord.user_id == user.user_id)
            .scalar()
        )

        return count or 0
