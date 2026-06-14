# fetch_frederic.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def fetch_frederic():
    # 【最新】実際のライブスケジュールが格納されている正確なURL
    url = "https://frederic-official.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # 確実に最新のURLへリクエストを送る
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print("フレデリック公式サイトの通信エラー:", e)
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    events = []

    # FanPlusシステムの最新のHTML構造（ニュース・ライブ一覧）を解析
    items = soup.select(".news-list__item, .news-list-item, article, li")

    for item in items:
        link_tag = item if item.name == "a" else item.find("a")
        if not link_tag or not link_tag.get("href"):
            continue

        text_content = item.get_text(" ", strip=True)
        href = link_tag["href"]

        # 「06.18.」や「2026.06.18」のような日付を正規表現で探す
        date_match = re.search(r"(\d{2,4})\.(\d{2})\.(\d{2})|(\d{2})\.(\d{2})\.", text_content)
        if not date_match:
            continue

        # 日付のパース（変換）
        event_date = None
        try:
            if date_match.group(4) and date_match.group(5):
                # "06.18." 形式
                month = int(date_match.group(4))
                day = int(date_match.group(5))
                event_date = datetime(datetime.now().year, month, day)
            else:
                # "2026.06.18" 形式
                year = int(date_match.group(1)) if len(date_match.group(1)) == 4 else datetime.now().year
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                event_date = datetime(year, month, day)
        except:
            continue

        # タイトルの整形と、不要なナビゲーション文字の除外
        display_title = text_content.replace(date_match.group(0), "").strip()
        display_title = re.sub(r"\s+", " ", display_title) # 余計な空白を消す
        
        if len(display_title) < 5 or "一覧" in display_title or "公式" in display_title:
            continue

        # URLの補正
        link = href if href.startswith("http") else f"https://frederic-official.com{href}"

        events.append({
            "artist": "フレデリック",
            "title": display_title,
            "date": event_date,
            "place": "公式サイトをご確認ください",
            "url": link
        })

    # 重複するURLの予定を排除
    seen_urls = set()
    unique_events = []
    for ev in events:
        if ev["url"] not in seen_urls:
            seen_urls.add(ev["url"])
            unique_events.append(ev)

    return unique_events

