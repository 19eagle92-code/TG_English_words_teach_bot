import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError

# Создаем движок SQLite в памяти для тестов
engine = create_engine("sqlite:///:memory:", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


# Определяем модель User
class User(Base):
    __tablename__ = "users"
    user_id = sq.Column(sq.Integer, primary_key=True)
    chat_id = sq.Column(sq.Integer, unique=True, nullable=False)
    user_name = sq.Column(sq.String(100), nullable=True)

    def __repr__(self):
        return (
            f"<User(id={self.user_id}, chat_id={self.chat_id}, name={self.user_name})>"
        )


class RussianWord(Base):
    __tablename__ = "russian_words"
    ru_word_id = sq.Column(sq.Integer, primary_key=True)
    ru_word = sq.Column(sq.String(200), nullable=False)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("users.user_id"), nullable=False)

    user = relationship("User", back_populates="russian_words")
    english_words = relationship(
        "EnglishWord", back_populates="russian_word", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("user_id", "ru_word", name="uq_user_ru_word"),)

    def __repr__(self):
        return f"<RussianWord(id={self.ru_word_id}, word={self.ru_word}, user_id={self.user_id})>"


class EnglishWord(Base):
    __tablename__ = "english_words"
    en_word_id = sq.Column(sq.Integer, primary_key=True)
    en_word = sq.Column(sq.String(200), nullable=False)
    ru_word_id = sq.Column(
        sq.Integer, sq.ForeignKey("russian_words.ru_word_id"), nullable=False
    )

    russian_word = relationship("RussianWord", back_populates="english_words")

    def __repr__(self):
        return f"<EnglishWord(id={self.en_word_id}, word={self.en_word}, ru_word_id={self.ru_word_id})>"


User.russian_words = relationship(
    "RussianWord", back_populates="user", cascade="all, delete-orphan"
)


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
            existing_client = session.query(User).filter_by(chat_id=chat_id).first()

            if existing_client:
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


def delete_word(word_to_delet, chat_id):
    try:
        with session_scope() as session:
            # Находим клиента в бд
            user = session.query(User).filter_by(chat_id=chat_id).first()

            if not user:
                print(f"Пользователь с № {chat_id} не найден")
                return False
                # добавляем слова для клиента
            else:
                query = (
                    session.query(
                        User.chat_id, RussianWord.ru_word, EnglishWord.en_word
                    )
                    .join(User, RussianWord.user_id == User.user_id)
                    .join(RussianWord, EnglishWord.ru_word_id == RussianWord.ru_word_id)
                ).filter(RussianWord.ru_word == word_to_delet)

                results = query.all()
                for chat_id, ru_word, en_word in results:
                    session.delete(ru_word)
                    session.delete(en_word)
                print(f"Слово{word_to_delet} с переводом {en_word} -  успешно удалены")
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


if __name__ == "__main__":
    print("Тестируем добавление пользователей...")

    # Тест 1 - добавляем первого
    print("\n1. Добавляем первого пользователя:")
    success1 = add_client(1001, "Иван")
    print(f"Успешно: {success1}")

    # Тест 2 - пробуем добавить того же
    print("\n2. Пробуем добавить того же пользователя:")
    success2 = add_client(1001, "Иван Иванов")
    print(f"Успешно: {success2}")

    # Тест 3 - добавляем другого
    print("\n3. Добавляем второго пользователя:")
    success3 = add_client(1002, "Мария")
    print(f"Успешно: {success3}")
