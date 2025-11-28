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
    from sqlalchemy.exc import IntegrityError


def add_user(session, chat_id: int, user_name: str | None = None) -> User:
    """Добавить пользователя, если не существует; вернуть объект User."""
    user = session.query(User).filter_by(chat_id=chat_id).one_or_none()
    if user:
        return user
    user = User(chat_id=chat_id, user_name=user_name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def add_russian_word_with_translations(
    session, user_id: int, ru_word: str, translate_fn
) -> RussianWord:
    """
    Добавить русское слово для user_id и автоматом создать переводы.
    translate_fn - callable(ru_word: str) -> list[str] (список переводов).
    Операция атомарна: либо всё создаётся, либо откатывается при ошибке.
    """
    # простая нормализация
    ru_word = ru_word.strip()

    # проверка существования пользователя
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("User not found")

    try:
        # Начинаем транзакцию (Session по умолчанию управляет транзакцией)
        rw = RussianWord(ru_word=ru_word, user_id=user_id)
        session.add(rw)
        session.flush()  # гарантируем, что rw.ru_word_id присвоится

        # получаем переводы (может бросить исключение если переводчик упал)
        translations = translate_fn(ru_word)
        if not translations:
            # Если перевод не найден, можно сделать откат.
            raise RuntimeError("No translations returned")

        # создаём EnglishWord для каждого перевода (дубликаты можно фильтровать)
        seen = set()
        for t in translations:
            t_norm = t.strip()
            if not t_norm or t_norm in seen:
                continue
            seen.add(t_norm)
            ew = EnglishWord(en_word=t_norm, ru_word_id=rw.ru_word_id)
            session.add(ew)

        session.commit()
        session.refresh(rw)
        return rw

    except IntegrityError as e:
        session.rollback()
        # скорее всего нарушение уникальности (один пользователь пытался добавить повтор)
        raise ValueError("Word already exists for this user") from e
    except Exception:
        session.rollback()
        raise  # пробрасываем дальше — вызывающий код решит, как обработать


def delete_russian_word(session, user_id: int, ru_word_id: int) -> bool:
    """
    Удалить русское слово, только если оно принадлежит user_id.
    Возвращает True если удалено, False если не найдено / не владелец.
    """
    rw = session.get(RussianWord, ru_word_id)
    if rw is None:
        return False
    if rw.user_id != user_id:
        # попытка удалить чужое слово — запрещаем
        return False
    session.delete(rw)
    session.commit()
    return True


def list_user_words(session, user_id: int):
    """Вернуть список русских слов и их переводов для пользователя."""
    rows = session.query(RussianWord).filter_by(user_id=user_id).all()
    result = []
    for rw in rows:
        translations = [ew.en_word for ew in rw.english_words]
        result.append(
            {
                "ru_word_id": rw.ru_word_id,
                "ru_word": rw.ru_word,
                "translations": translations,
            }
        )
    return result

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
