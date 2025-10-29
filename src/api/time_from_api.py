import requests
from datetime import datetime
from zoneinfo import ZoneInfo

def get_current_time_from_api(timezone: str = "Etc/UTC") -> datetime:
    url = f"https://worldtimeapi.org/api/timezone/{timezone}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        datetime_str = data.get("datetime")
        if not datetime_str:
            raise ValueError("Ответ API не содержит поля 'datetime'")
        
        return datetime.fromisoformat(datetime_str)
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Ошибка при запросе к WorldTimeAPI: {e}") from e
    except (ValueError, KeyError) as e:
        raise ValueError(f"Некорректный ответ от WorldTimeAPI: {e}") from e
