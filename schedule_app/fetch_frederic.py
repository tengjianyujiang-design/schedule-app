import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://frederic-official.com"

def fetch_frederic():
    # ライブページではなくトップページを取得
    url = BASE_URL
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    events = []

    # トップページのライブ一覧
    items = soup.select("ul.list--information__live > li")

    for item in items:
        # 日付
        date_text = item.select_one("p.date").get_text(strip=True)

        try:
            event_date = datetime.strptime(date_text, "%m.%d")
            event_date = event_date.replace(year=datetime.now().year)
        except:
            event_date = None

        # タイトル
        title = item.select_one("p.tit").get_text(strip=True)

        # 会場はHTMLに無いので空欄
        place = ""

        # 詳細URL
        link = item.select_one("a")["href"]
        if not link.startswith("http"):
            link = BASE_URL + "/" + link.lstrip("/")

        events.append({
            "artist": "Frederic",
            "title": title,
            "date": event_date,
            "place": place,
            "url": link,
            "source": "frederic-official"
        })

    return events
