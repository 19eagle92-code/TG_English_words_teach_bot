if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ENG_words_teach_bot_code.db_tables_create import (
        create_tables,
        Base,
        User,
        RussianWord,
        EnglishWord,
    )
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from ENG_words_teach_bot_code.db_tables_create import create_tables

    # простой переводчик-заглушка: можете заменить на вызов внешнего API
    def dummy_translator(ru: str) -> list[str]:
        # Примеры:
        mapping = {
            "привет": ["hello"],
            "дом": ["house", "home"],
            "ключ": ["key"],
        }
        return mapping.get(
            ru.lower(), [f"trans_{ru}"]
        )  # если нет в словаре — делаем placeholder

    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    create_tables(engine)

    with Session() as s:
        u = add_user(s, chat_id=12345, user_name="ivan")
        print("Created user:", u)

        # добавляем слово
        try:
            rw = add_russian_word_with_translations(
                s, user_id=u.user_id, ru_word="привет", translate_fn=dummy_translator
            )
            print("Added RW:", rw)
        except Exception as e:
            print("Error:", e)

        # показываем слова пользователя
        words = list_user_words(s, user_id=u.user_id)
        print("User words:", words)

        # попытка удалить
        ok = delete_russian_word(s, user_id=u.user_id, ru_word_id=rw.ru_word_id)
        print("Deleted:", ok)
