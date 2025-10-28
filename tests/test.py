from prompts import agent_prompts
from src.in_out import document_loader, markdown_writer
from src.auth import gigachat_auth
from src.agent import extract_agent


client_id = "019a0884-a71f-7bf2-9d3a-b753f145b3e6"
client_secret = "33de7dd8-98d5-4682-8acd-883e65e17b87"

authorization_key = "MDE5YTA4ODQtYTcxZi03YmYyLTlkM2EtYjc1M2YxNDViM2U2OjMzZGU3ZGQ4LTk4ZDUtNDY4Mi04YWNkLTg4M2U2NWUxN2I4Nw=="

input_path = "examples/math_sample.txt"


def main():
    access_token = gigachat_auth.get_gigachat_token(client_id, client_secret)
    if access_token: print(f"Получен токен")

    text = document_loader.load_document(input_path)

    extracted_math = extract_agent.extract_agent_entities(text, access_token, prompt=agent_prompts.MATH_AGENT_PROMPT)

    markdown_writer.save_to_markdown(extracted_math, "examples/math_summary.md")
    print(f"Результат сохранён в examples/math_summary.md")

    print(f"Обработка завершена")


if __name__ == "__main__":
    main()
