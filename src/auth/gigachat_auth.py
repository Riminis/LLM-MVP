import base64
import uuid
import requests


def get_gigachat_token(client_id, client_secret):
    credentials = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {encoded_auth}"
    }
    payload = {"scope": "GIGACHAT_API_PERS"}

    response = requests.post(url, headers=headers, data=payload, verify=False)

    print(response.status_code)

    token_data = response.json()
    access_token = token_data["access_token"]
    
    return access_token