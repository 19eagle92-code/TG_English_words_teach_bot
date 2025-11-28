try:
    import sys
    import os

    # Добавляем родительскую директорию в путь Python
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Теперь можно импортировать из db_tables_create
    from ENG_words_teach_bot_code.db_tables_create import (
        create_tables,
        Base,
        User,
        RussianWord,
        EnglishWord,
    )

    print("Успех!")
except ImportError as e:
    print(f"Ошибка: {e}")
