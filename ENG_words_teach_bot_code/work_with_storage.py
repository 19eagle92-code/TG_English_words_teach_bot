class PostgreSQLStorage:
    def __init__(self):
        # Инициализация подключения к PostgreSQL
        pass

    def set_state(self, chat_id, user_id, state):
        # Сохраняем состояние в PostgreSQL
        pass

    def get_state(self, chat_id, user_id):
        # Получаем состояние из PostgreSQL
        pass

    def delete_state(self, chat_id, user_id):
        # Удаляем состояние из PostgreSQL
        pass


import os
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

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


load_dotenv()
password = os.getenv("SECRET_KEY")

DSN = f"postgresql://postgres:{password}@localhost:5432/english_words_bot"
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)


Session = sessionmaker(bind=engine)
session = Session()

try:
    session.add_all(read_json("ORM code/data/book_data.json"))
    session.commit()
    print("Данные успешно загружены в базу данных")
except Exception as e:
    session.rollback()
    print(f"Ошибка при загрузке данных: {e}")
finally:
    session.close()

session = Session()

publisher = input("Введите название издателя")
query = (
    session.query(Book.title, Publisher.name, Shop.name, Sale.price, Sale.date_sale)
    .join(Publisher, Book.id_publisher == Publisher.id)
    .join(Stock, Book.id == Stock.id_book)
    .join(Shop, Stock.id_shop == Shop.id)
    .join(Sale, Stock.id == Sale.id_stock)
    .filter(Publisher.name == publisher)
)

results = query.all()

for title, publisher, shop, price, date in results:
    print(
        f"Книга: {title}, Издатель: {publisher}, Магазин: {shop}, Цена: {price}, Дата: {date}"
    )
session.close()
