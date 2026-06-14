# fetch_chevon.py
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
import re

BASE_URL = "https://chevon.biz"

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
    
    # 1. サイト全体の文字を1つの巨大な文字列として取得
    full_text = soup.get_text(" ", strip=True)
    
    # 不要な過去の年やメニュー文字（LIVE 2026 2025...）などをカットするための大掃除
    full_text = re.sub(r"LIVE\s+\d{4}.*?\d{4}", "", full_text)

    # 2. 【超重要】「2026/06/13」や「2026/12/20」のような「日付」を合図に文章をバラバラに分割する
    # 日付の直前に特殊な目印（[SPLIT]）を埋め込みます
    split_marker = "[SPLIT]"
    # 2026/06/14 や 2026/09/13 などのパターンを見つけて目印を打つ
    prepared_text = re.sub(r"(\d{4}[/\.]\d{1,2}[/\.]\d{1,2})", rf"{split_marker}\1", full_text)
    
    # 目印を元に、1公演ずつの塊（ブロック）に分解
    chunks = prepared_text.split(split_marker)
    
    events = []

    for chunk in chunks:
        chunk_str = chunk.strip()
        if not chunk_str:
            continue
            
        # 塊の先頭から日付を抜き出す
        date_match = re.match(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", chunk_str)
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

        # 塊（文章）から日付部分を取り除いた残りを「ツアー名・詳細」とする
        title_content = chunk_str.replace(date_match.group(0), "").strip()
        
        # 別の不要な日付（連日公演の・25など）が後ろの予定と混ざるのを防ぐため、
        # 次の日付の年（2026. 7 や 2026. 8）などが紛れ込んでいたらそこから後ろを綺麗に消去する
        title_content = re.split(r"\d{4}\s*\.\s*\d{1,2}", title_content)[0].strip()
        title_content = re.split(r"\d{4}[/\.]", title_content)[0].strip()
        
        # 連続する不要な空白スペースを1つのスペースに統合
        title_content = re.sub(r"\s+", " ", title_content)
        
        # メインタイトルが短すぎるゴミデータやフッター文字は除外
        if len(title_content) < 5 or "©" in title_content or "BIOGRAPHY" in title_content:
            continue

        events.append({
            "artist": "Chevon",
            "title": title_content,
            "date": event_date,
            "place": "公式サイトをご参照ください",
            "url": url
        })

    # 日付順に並び替え
    events.sort(key=lambda x: x["date"])
    return events
