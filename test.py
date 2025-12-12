import os
import json
from pathlib import Path
from src.extract_agent import GigaChatClient
from src.document_loader import DocumentLoader


client_id = "019a0884-a71f-7bf2-9d3a-b753f145b3e6"
client_secret = "9eac3076-7e96-46b2-8711-8c761e601539"

input_file = "examples/math_sample.txt"
prompt_file = "prompts/universal_prompt.txt"

output_md = "examples/result.md"
output_json = "examples/result.json"

client = GigaChatClient(client_id=client_id, client_secret=client_secret)

text = DocumentLoader.load(input_file)['content']

print(f"Прочитан файл: {input_file}")
print(f"Размер: {len(text)} символов")
print("=" * 50)

prompt = DocumentLoader.load(prompt_file)['content']

print(f"Прочитан файл: {prompt_file}")
print(f"Размер: {len(prompt)} символов")
print("=" * 50)

summary = client.chat(text=text, prompt=prompt)

print(f"Получена выжимка: {len(summary)} символов")
print("=" * 50)

with open(output_md, "w", encoding="utf-8") as f:
    f.write(summary)

print(f"Markdown сохранён: {output_md}")
