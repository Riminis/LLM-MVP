import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def get_current_time(timezone_name: str = "UTC") -> datetime:
    sources = [
        "https://httpbin.org/get",
        "https://api.github.com",
    ]
    
    utc_time = None
    for url in sources:
        try:
            response = requests.get(url, timeout=3)
            date_header = response.headers.get("Date")
            if date_header:

                naive_utc = datetime.strptime(date_header, "%a, %d %b %Y %H:%M:%S %Z")

                utc_time = naive_utc.replace(tzinfo=timezone.utc)
                break
        except Exception:
            continue
    
    if utc_time is None:
        raise RuntimeError("Не удалось получить время")

    utc_time = utc_time.replace(microsecond=0)
    
    if timezone_name.upper() == "UTC":
        return utc_time
    else:
        target_tz = ZoneInfo(timezone_name)
        return utc_time.astimezone(target_tz)
