import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Создаем движок SQLite в памяти для тестов
engine = create_engine("sqlite:///:memory:", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


# Определяем модель User
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    user_name = Column(String(100), nullable=False)


# Создаем таблицу
Base.metadata.create_all(engine)


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
