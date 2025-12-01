import requests
from dotenv import load_dotenv
import os

url = "https://dictionary.yandex.net/api/v1/dicservice.json/lookup"


load_dotenv()
dict_token = os.getenv("API_YANDEX_DICT_TOKEN")
# dict_token = input("Insert your Yandex API token:") #для использования стороннего токена


def translate_word(word):
    """
    Функция для перевода слова с русского на английский
    """
    try:
        params = {"key": dict_token, "lang": "ru-en", "text": word, "ui": "ru"}

        response = requests.get(url, params=params)

        # Проверяем успешность запроса
        if response.status_code == 200:
            data = response.json()

            # Проверяем, есть ли переводы в ответе
            if data.get("def") and len(data["def"]) > 0:
                translations = data["def"][0].get("tr", [])

                if len(translations) >= 2:
                    # Если есть как минимум два перевода, возвращаем оба
                    trans_word_1 = translations[0].get("text")
                    trans_word_2 = translations[1].get("text")
                    return trans_word_1, trans_word_2
                elif len(translations) == 1:
                    # Если только один перевод
                    trans_word_1 = translations[0].get("text")
                    return trans_word_1, None
            else:
                # Если нет переводов в ответе
                return None, None
        else:
            # Если запрос не удался
            print(f"Ошибка запроса: статус {response.status_code}")
            return None, None

    except requests.exceptions.RequestException as e:
        # Ошибки сети или запроса
        print(f"Ошибка подключения: {e}")
        return None, None
    except Exception as e:
        # Любые другие ошибки
        print(f"Непредвиденная ошибка: {e}")
        return None, None


if __name__ == "__main__":
    word = "машина"
    result = translate_word(word)
    print(result[0])
    print(f"{word} = {result}")
