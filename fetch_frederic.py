# fetch_frederic.py
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
import re

def fetch_frederic():
    # 【確定】ライブ情報だけが完璧に並んでいる正しいエンドポイントURL
    url = "https://frederic-official.com/news/3?range=future_event_end_time&sort=asc"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # httpxに依存せず、絶対に壊れないurllibで構築します
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        print("フレデリック公式サイトの通信エラー:", e)
        return []

    soup = BeautifulSoup(html, "html.parser")
    events = []

    # サイト内の箇条書き（liタグなど）に格納されているライブ項目を正確にターゲットにします
    items = soup.find_all("li")

    for item in items:
        text_content = item.get_text(" ", strip=True)
        link_tag = item.find("a")
        
        if not text_content:
            continue

        # 「06.18」や「12.20」のような、月.日の日付パターンを綺麗に検知
        date_match = re.search(r"(\d{2})\.(\d{2})", text_content)
        if not date_match:
            continue

        # 日付のパース（現在の年を自動補完）
        try:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            event_date = datetime(datetime.now().year, month, day)
        except:
            continue

        # テキスト全体の成形（余計な空白を排除）
        cleaned_text = re.sub(r"\s+", " ", text_content)

        # リンクの補正
        link = f"https://frederic-official.com/news/3?range=future_event_end_time&sort=asc"
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            link = href if href.startswith("http") else f"https://frederic-official.com{href}"

        # 18:00通知用のメニュー項目などのゴミデータを省く最終防衛線
        if "公式アカウント" in cleaned_text or "PROFILE" in cleaned_text or "©" in cleaned_text:
            continue

        events.append({
            "artist": "フレデリック",
            "title": cleaned_text,  # 「06.18 東京『ツアー名』」の形でそのまま綺麗に入ります
            "date": event_date,
            "place": "公式サイトをご確認ください",
            "url": link
        })

    # 同じ内容の予定の重複排除
    unique_events = []
    seen = set()
    for ev in events:
        key = (ev["date"].strftime("%m-%d"), ev["title"][:15])
        if key not in seen:
            seen.add(key)
            unique_events.append(ev)

    return unique_events
