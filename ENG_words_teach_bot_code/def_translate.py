import requests

url = "https://dictionary.yandex.net/api/v1/dicservice.json/lookup"
token = "dict.1.1.20251012T151735Z.12c290dabd4c3643.9aa47948f360b0dc9a067845d6a9e509bdccfdda"


def translate_word(word):
    params = {"key": token, "lang": "ru-en", "text": word, "ui": "ru"}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        # Проверяем, есть ли переводы
        if data.get("def") and len(data["def"]) > 0:
            # Берем первый перевод из первого определения
            translations = data["def"][0].get("tr", [])
            if translations:
                trans_word = translations[0].get("text")
                return trans_word

    # Если что-то пошло не так, возвращаем None или исходное слово
    return None


if __name__ == "__main__":
    word = "машина"
    result = translate_word(word)
    print(f"{word} = {result}")


# import requests

# # Базовый URL для обращения к API Яндекс.Словаря
# url = "https://dictionary.yandex.net/api/v1/dicservice.json/lookup"
# # Токен для доступа к API. Его получают в личном кабинете Яндекс.Разработчика.
# token = "dict.1.1.20220928T183617Z.4449b33063fe4328.b93679d48620ed6f3c20da6bff0237bcbd0e8d6a"


# def translate_word(word):
#     params = {
#         "key": token,  # ключ для авторизации в API
#         "lang": "ru-en",  # направление перевода: с русского на английский
#         "text": word,  # слово, которое нужно перевести
#     }

#     # Выполняем GET-запрос к API со всеми параметрами
#     response = requests.get(url, params=params)

#     # Преобразуем JSON-ответ в Python-словарь
#     data = response.json()

#     # Проверяем, содержит ли ответ переводы
#     if data.get("def"):
#         # Возвращаем текст первого перевода из списка
#         return data["def"][0]["tr"][0]["text"]


# if __name__ == "__main__":
#     word = "машина"
#     assert translate_word(word) == "car"
