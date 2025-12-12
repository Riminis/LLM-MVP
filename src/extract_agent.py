import base64
import uuid
import json
import requests


class GigaChatClient:
    def __init__(self, client_id: str, client_secret: str, scope: str = "GIGACHAT_API_PERS", model: str = "GigaChat"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.model = model
        self.oauth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        self.access_token = None

    def get_token(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(credentials.encode("utf-8")).decode("ascii")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {encoded_auth}"
        }
        payload = {"scope": self.scope}

        response = requests.post(self.oauth_url, headers=headers, data=payload, verify=False)
        token_data = response.json()
        self.access_token = token_data["access_token"]
        return self.access_token

    def chat(self, text: str, prompt: str, temperature: float = 0.0) -> str:
        if not self.access_token:
            self.get_token()

        request_text = prompt + text[:20000]

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": request_text}],
            "temperature": temperature
        }

        response = requests.post(self.api_url, headers=headers, json=payload, verify=False)
        content = response.json()["choices"][0]["message"]["content"]
        return content

    def chat_json(self, text: str, prompt: str, temperature: float = 0.0) -> dict:
        raw_output = self.chat(text=text, prompt=prompt, temperature=temperature)

        if raw_output.strip().startswith("```json"):
            raw_output = raw_output.split("```json")[1].split("```")[0]
        elif raw_output.strip().startswith("```"):
            raw_output = raw_output.split("```")[1]

        return json.loads(raw_output)
