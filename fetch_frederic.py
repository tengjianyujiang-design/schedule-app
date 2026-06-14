# fetch_frederic.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def fetch_frederic():
    # ライブと関連ニュースが含まれるURL
    url = "https://frederic-official.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print("フレデリック公式サイトの通信エラー:", e)
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    events = []

    items = soup.select(".news-list__item, .news-list-item, article, li")

    for item in items:
        link_tag = item if item.name == "a" else item.find("a")
        if not link_tag or not link_tag.get("href"):
            continue

        text_content = item.get_text(" ", strip=True)
        href = link_tag["href"]

        # 日付を正規表現で探す
        date_match = re.search(r"(\d{2,4})\.(\d{2})\.(\d{2})|(\d{2})\.(\d{2})\.", text_content)
        if not date_match:
            continue

        # 日付のパース（変換）
        event_date = None
        try:
            if date_match.group(4) and date_match.group(5):
                month = int(date_match.group(4))
                day = int(date_match.group(5))
                event_date = datetime(datetime.now().year, month, day)
            else:
                year = int(date_match.group(1)) if len(date_match.group(1)) == 4 else datetime.now().year
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                event_date = datetime(year, month, day)
        except:
            continue

        # タイトルの整形
        display_title = text_content.replace(date_match.group(0), "").strip()
        display_title = re.sub(r"\s+", " ", display_title)
        
        if len(display_title) < 5 or "一覧" in display_title or "公式アカウント" in display_title:
            continue

        # 【最新対策】ライブ情報だけに絞り込むためのキーワードフィルター
        # タイトルに以下の言葉が含まれている場合のみ「ライブ予定」として認めます
        live_keywords = [
            "TOUR", "Tour", "tour", "ワンマン", "対バン", "LIVE", "Live", "live", 
            "ライブ", "フェス", "FES", "Fes", "fes", "出演", "公演", "イベント", 
            "フレデリズム", "FREDERHYTHM", "ステージ", "開場", "チケット"
        ]
        
        # 逆に、ライブに関係のないグッズ販売などのニュースを弾く除外キーワード
        ignore_keywords = ["GOODS", "goods", "グッズ", "通販", "販売開始", "ファンクラブ限定", "リリース"]

        # 判定ロジック
        is_live = any(keyword in display_title for keyword in live_keywords)
        is_ignore = any(keyword in display_title for keyword in ignore_keywords)

        # ライブキーワードが含まれており、かつグッズ等の除外ワードが含まれていない場合のみ追加
        if is_live and not is_ignore:
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

