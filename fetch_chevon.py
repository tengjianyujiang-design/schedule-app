# fetch_chevon.py
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

BASE_URL = "https://chevon.biz"

def fetch_chevon():
    list_url = f"{BASE_URL}/live/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(list_url, headers=headers, method="GET")
    
    html = None
    # タイムアウト対策（最大3回リトライ）
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                html = response.read().decode("utf-8")
                break
        except Exception as e:
            print(f"Chevon接続試行 {attempt + 1} 回目失敗: {e}")
            if attempt < 2:
                time.sleep(2)
            else:
                return []

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    events = []

    # 1. 巨大な1つの塊になっているaタグをすべて探す
    a_tags = soup.find_all("a")
    
    for a_tag in a_tags:
        href = a_tag.get("href", "")
        # メニューバーなどの無関係なリンクはスキップ
        if any(k in href for k in ["/biography", "/discography", "/goods", "/shop", "/contact"]):
            continue
            
        # aタグ内の文章を改行ごとに分解する（これで各ライブが1行ずつに分かれます）
        raw_text = a_tag.get_text("\n", strip=True)
        lines = raw_text.split("\n")
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            # 「2026/06/13」や「2026.06.13」のような日付を探す
            date_match = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", line_str)
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
                
            # タイトルのクレンジング（日付の文字を消す）
            display_title = line_str.replace(date_match.group(0), "").strip()
            # 余計な年号ナビゲーション（LIVE 2026...など）を排除
            display_title = re.sub(r"LIVE\s+\d{4}.*?\d{4}", "", display_title)
            display_title = re.sub(r"\s+", " ", display_title).strip()
            
            # あまりに短すぎる文字はゴミデータとして弾く
            if len(display_title) < 4:
                continue
                
            # 【個別URLの解決】
            # 各公演の個別リンク（例: /live/xxxxx）がhrefにあればそれを採用し、
            # なければ一覧ページ(list_url)を安全に割り当てます
            if href and href != "/" and href != "/live" and href != "/live/":
                final_url = href if href.startswith("http") else BASE_URL + href
            else:
                final_url = list_url

            events.append({
                "artist": "Chevon",
                "title": display_title,
                "date": event_date,
                "place": "公式サイトをご参照ください",
                "url": final_url  # ここに各公演固有のリンク、または正しい一覧リンクが入ります
            })

    # 同じ日付の重複を排除（文字数が多い詳細なタイトルを優先して残す）
    clean_dict = {}
    for ev in events:
        date_str = ev["date"].strftime("%Y-%m-%d")
        if date_str not in clean_dict:
            clean_dict[date_str] = ev
        else:
            if len(ev["title"]) > len(clean_dict[date_str]["title"]):
                clean_dict[date_str] = ev

    unique_events = list(clean_dict.values())
    
    # 最後に日付の近い順（昇順）に並び替える
    unique_events.sort(key=lambda x: x["date"])
    return unique_events

