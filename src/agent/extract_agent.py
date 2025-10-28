import json
import requests
from src.in_out import document_loader, markdown_writer


def extract_agent_entities(text: str, access_token: str, prompt: str, model: str = "GigaChat") -> dict:
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    request = prompt + text[:12000]
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": request}],
        "temperature": 0.0
    }
    
    response = requests.post(url, headers=headers, json=payload, verify=False)
    raw_output = response.json()["choices"][0]["message"]["content"]
    
    if raw_output.strip().startswith("```json"):
        raw_output = raw_output.split("```json")[1].split("```")[0]
    elif raw_output.strip().startswith("```"):
        raw_output = raw_output.split("```")[1]
    
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Не удалось распарсить JSON: {e}\nОтвет: {raw_output}")
