import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.in_out import document_loader, markdown_writer
from src.auth import gigachat_auth
from src.agent import extract_agent
from src.api import time_from_api


client_id = "019a0884-a71f-7bf2-9d3a-b753f145b3e6"
client_secret = "9eac3076-7e96-46b2-8711-8c761e601539"

authorization_key = "MDE5YTA4ODQtYTcxZi03YmYyLTlkM2EtYjc1M2YxNDViM2U2OjllYWMzMDc2LTdlOTYtNDZiMi04NzExLThjNzYxZTYwMTUzOQ=="

input_path = "examples/math_sample.txt"

prompt_math = document_loader.load_document("prompts/math_prompt.txt")


def main():
    access_token = gigachat_auth.get_gigachat_token(client_id, client_secret)
    if access_token: print(f"Получен токен")

    print(prompt_math)

    test_api_giga(access_token, input_path, prompt_math)

    # print(test_api_time("Europe/Moscow"))



def test_api_giga(access_token, input_path, prompt):
    text = document_loader.load_document(input_path)

    extracted_math = extract_agent.extract_agent_entities(text, access_token, prompt=prompt)

    print(text)

    # Получаем текущее время
    time = time_from_api.get_current_time("Europe/Moscow")
    # Указываем темы и теги
    topics = ["Математика", "Анализ"]
    tags = ["производная", "интеграл", "теорема"]

    # Добавляем домен к извлеченным данным
    extracted_math['domain'] = 'Математический анализ'

    markdown_writer.save_to_markdown(extracted_math, "examples/math_summary.md", time, topics, tags)

    print(extracted_math)

    print(f"Результат сохранён в examples/math_summary.md")

    print(f"Обработка завершена")
    return '200'


def test_api_time(time_zone):
    time = time_from_api.get_current_time(time_zone)
    return time


if __name__ == "__main__":
    main()
