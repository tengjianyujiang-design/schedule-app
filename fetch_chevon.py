# fetch_chevon.py
import urllib.request
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re

BASE_URL = "https://www.chevon.biz/"

def fetch_chevon():
    url = f"{BASE_URL}/live/"
    
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

    # 【最新対策】テキスト分割をやめ、公式サイトの各スケジュールブロックを正確にターゲットにします
    # Chevonのサイトは、各予定がaタグやli、divといった個別ブロックに包まれています
    blocks = soup.select("a, li, .live-item, .schedule-item")

    for block in blocks:
        text_content = block.get_text(" ", strip=True)
        if not text_content:
            continue

        # 「2026/12/20」や「2026.06.13」などの日付パターンを正確に検知
        date_match = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", text_content)
        if not date_match:
            continue

        # 日付をパース
        try:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            event_date = datetime(year, month, day)
        except:
            continue

        # そのブロックの中にある文字をまるごと予定タイトルとして取得
        # 日付の文字列だけを綺麗に消去します
        display_title = text_content.replace(date_match.group(0), "").strip()
        
        # 不要なナビゲーションやフッター文字（メニュー項目など）が混ざったものは排除
        if len(display_title) < 5 or "©" in display_title or "BIOGRAPHY" in display_title:
            continue

        # 連続する不要な空白スペースを1つのスペースに綺麗に整える
        display_title = re.sub(r"\s+", " ", display_title)

        # 詳細URLの判定
        href = block.get("href", "") if block.name == "a" else (block.find("a")["href"] if block.find("a") else "")
        link = url
        if href:
            link = href if href.startswith("http") else BASE_URL + href

        events.append({
            "artist": "Chevon",
            "title": display_title,
            "date": event_date,
            "place": "公式サイト参照",
            "url": link
        })

    # 同じ日付の重複を排除し、かつ文字数（情報量）が最も多く残っている方を採用する
    # これにより「・21」のようなゴミデータを完全に上書きし、正しいフルタイトルを残せます
    seen_dates = {}
    for ev in events:
        date_key = ev["date"].strftime("%Y-%m-%d")
        
        if date_key not in seen_dates:
            seen_dates[date_key] = ev
        else:
            # すでに登録されているタイトルより、新しく見つかったタイトルの方が文字数が多い（詳細が削れていない）場合
            if len(ev["title"]) > len(seen_dates[date_key]["title"]):
                seen_dates[date_key] = ev

    # 綺麗になったデータをリストに戻す
    unique_events = list(seen_dates.values())

    return unique_events
