# fetch_chevon.py
import urllib.request
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re

BASE_URL = "https://www.chevon.biz/"

def fetch_chevon():
    url = f"{BASE_URL}/live/"
    
    # 相手のサイトに拒否されないためのヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        print("Chevon公式サイトの通信エラー:", e)
        return []

    soup = BeautifulSoup(html, "html.parser")
    events = []

    # Chevonのサイト構造（テキスト要素を網羅的にスキャン）
    items = soup.find_all(["div", "p", "li", "a"])

    for item in items:
        link_tag = item if item.name == "a" else item.find("a")
        text_content = item.get_text(" ", strip=True)
        
        if not text_content:
            continue

        # 「2026/06/13」や「2026.06.13」のような日付パターンを探す
        date_match = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", text_content)
        if not date_match:
            continue

        # 日付のパース
        try:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            event_date = datetime(year, month, day)
        except:
            continue

        # 詳細URLの補正
        link = url  # デフォルトは一覧ページ
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            if href.startswith("http"):
                link = href
            else:
                link = BASE_URL + href

        # タイトルの整形（日付部分を取り除く）
        display_title = text_content.replace(date_match.group(0), "").strip()
        display_title = re.sub(r"\s+", " ", display_title) # 余計な空白を削除

        # 記号や不要な文字だけのものは除外
        if len(display_title) < 4 or "LIVE" == display_title.upper():
            continue

        events.append({
            "artist": "Chevon",
            "title": display_title,
            "date": event_date,
            "place": "公式サイト参照",
            "url": link
        })

    # 重複URLを排除
    seen_urls = set()
    unique_events = []
    for ev in events:
        if ev["url"] not in seen_urls:
            seen_urls.add(ev["url"])
            unique_events.append(ev)

    return unique_events
