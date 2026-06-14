# fetch_frederic.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def fetch_frederic():
    # 【最新仕様】実際のライブ予定が日付順に格納されている正確なURL
    url = "https://frederic-official.com/news/3?range=future_event_end_time&sort=asc"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print("フレデリック公式サイト通信エラー:", e)
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    events = []

    # サイト内のリンクやリスト要素を網羅的に探す
    # 最新のFanPlus系サイト（公式が使用しているシステム）の構造に合わせて、テキストとリンクを解析します
    items = soup.find_all(["li", "div", "article", "a"])

    for item in items:
        # aタグそのもの、または子要素にaタグがあるか確認
        link_tag = item if item.name == "a" else item.find("a")
        if not link_tag or not link_tag.get("href"):
            continue

        text_content = item.get_text(" ", strip=True)
        href = link_tag["href"]

        # 「06.18.」や「2026.06.18」のような日付パターンを探す
        date_match = re.search(r"(\d{2,4})\.(\d{2})\.(\d{2})|(\d{2})\.(\d{2})\.", text_content)
        if not date_match:
            continue

        # 日付のパース処理
        event_date = None
        try:
            if date_match.group(4) and date_match.group(5):
                # "06.18." 形式の場合
                month = int(date_match.group(4))
                day = int(date_match.group(5))
                event_date = datetime(datetime.now().year, month, day)
            else:
                # "2026.06.18" 形式の場合
                year = int(date_match.group(1)) if len(date_match.group(1)) == 4 else datetime.now().year
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                event_date = datetime(year, month, day)
        except:
            continue

        # すでにツアータイトルやフェス名がテキストに含まれているため、全体を綺麗にクレンジング
        # 余計な改行や重複スペースを削除
        cleaned_text = re.sub(r"\s+", " ", text_content)
        
        # リンクの補正
        link = href if href.startswith("http") else f"https://frederic-official.com{href}"

        # 予定の組み立て（テキストから日付部分をトリミングして綺麗にする）
        display_title = cleaned_text.replace(date_match.group(0), "").strip()
        
        # 不要なナビゲーション文字などが混ざっていたら除外
        if len(display_title) < 5 or "公式アカウント" in display_title:
            continue

        # 地名（東京、大阪など）がタイトルの先頭にあれば簡易的に場所として分離
        place = "公式サイト参照"
        place_match = re.search(r"(東京|大阪|愛知|名古屋|神奈川|横浜|兵庫|神戸|千葉|山梨|福岡|北海道|宮城|仙台)「(.+?)」", display_title)
        if place_match:
            place = place_match.group(1)
            display_title = place_match.group(2)

        events.append({
            "artist": "フレデリック",
            "title": display_title,
            "date": event_date,
            "place": place,
            "url": link
        })

    # 同じURLの重複イベントを排除する
    seen_urls = set()
    unique_events = []
    for ev in events:
        if ev["url"] not in seen_urls:
            seen_urls.add(ev["url"])
            unique_events.append(ev)

    return unique_events

