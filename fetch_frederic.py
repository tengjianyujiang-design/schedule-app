# fetch_frederic.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://frederic-official.com"

def fetch_frederic():
    url = f"{BASE_URL}/live/"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    events = []

    items = soup.select(".live-list-item")

    for item in items:
        # 日付
        date_text = item.select_one(".date").get_text(strip=True)

        # 例: "07.12" → datetime(2026, 7, 12)
        try:
            event_date = datetime.strptime(date_text, "%m.%d")
            event_date = event_date.replace(year=datetime.now().year)
        except:
            event_date = None

        # タイトル
        title = item.select_one(".title").get_text(strip=True)

        # 会場（あれば）
        place_tag = item.select_one(".place")
        place = place_tag.get_text(strip=True) if place_tag else ""

        # 詳細URL
        link = BASE_URL + item.select_one("a")["href"]

        events.append({
            "artist": "Frederic",
            "title": title,
            "date": event_date,
            "place": place,
            "url": link,
            "source": "frederic-official"
        })

    return events
