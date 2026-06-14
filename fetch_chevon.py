# fetch_chevon.py
import urllib.request
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re

BASE_URL = "https://www.chevon.biz"

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

    # 【対策】大きな塊ではなく、各スケジュールが記述されている最小限の要素（テキスト行やブロック）に分解する
    # サイト全体のテキストを取得し、改行や日付の出現をベースに1個ずつの予定に切り分けます
    raw_text = soup.get_text("\n", strip=True)
    lines = raw_text.split("\n")

    current_date = None
    current_title = []

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # 「2026/06/13」や「2026.06.13」、「2026/09/13」のような日付パターンを正確に検知
        date_match = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", line_str)
        
        if date_match:
            # すでに前の予定が組み立て中の場合は、先に保存する
            if current_date and current_title:
                title_text = " ".join(current_title).strip()
                if len(title_text) > 5 and "LIVE" not in title_text.upper():
                    events.append({
                        "artist": "Chevon",
                        "title": title_text,
                        "date": current_date,
                        "place": "公式サイト参照",
                        "url": url
                    })
            
            # 新しい予定の日付をパース
            try:
                year = int(date_match.group(1))
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                current_date = datetime(year, month, day)
                # 日付行の残りの文字をタイトルの最初にする
                rem = line_str.replace(date_match.group(0), "").strip()
                current_title = [rem] if rem else []
            except:
                current_date = None
                current_title = []
        else:
            # 日付がない行は、現在の予定のタイトル（詳細）として文字を繋げていく
            if current_date:
                # ナビゲーションや無関係なフッター文字が混ざるのを防ぐ防波堤
                if "©" in line_str or "SHOP" in line_str or "倶楽部" in line_str:
                    continue
                current_title.append(line_str)

    # 最後の1件を滑り込みで保存
    if current_date and current_title:
        title_text = " ".join(current_title).strip()
        if len(title_text) > 5:
            events.append({
                "artist": "Chevon",
                "title": title_text,
                "date": current_date,
                "place": "公式サイト参照",
                "url": url
            })

    # さらに確実を期すため、各要素の個別解析（個別リンク取得用）もバックアップとして回す
    # ページ内の a タグから個別の「三者山羊」や「フェス名」を綺麗に抽出
    for a_tag in soup.find_all("a"):
        text = a_tag.get_text(" ", strip=True)
        href = a_tag.get("href", "")
        
        # 個別リンクの中に日付と予定が綺麗に収まっている場合
        dm = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", text)
        if dm and href and ("/live/" in href or "ticket" in href or "http" in href):
            try:
                ev_date = datetime(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                t_text = text.replace(dm.group(0), "").strip()
                if len(t_text) > 5 and "LIVE" not in t_text.upper():
                    link = href if href.startswith("http") else BASE_URL + href
                    events.append({
                        "artist": "Chevon",
                        "title": t_text,
                        "date": ev_date,
                        "place": "公式サイト参照",
                        "url": link
                    })
            except:
                pass

    # 重複する予定（同じ日付・同じタイトル）を綺麗に1本にまとめる
    unique_events = []
    seen = set()
    for ev in events:
        # 日付とタイトルの組み合わせで重複チェック
        date_str = ev["date"].strftime("%Y-%m-%d")
        key = (date_str, ev["title"][:20]) # 先頭20文字で判定
        if key not in seen:
            seen.add(key)
            unique_events.append(ev)

    return unique_events
