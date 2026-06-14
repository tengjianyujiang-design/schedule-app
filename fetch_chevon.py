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

    # 1. 画面上のすべての文字を、改行やスペースを維持したまま1本の大きな文字列にする
    full_text = soup.get_text(" \n ", strip=True)
    
    # 冒頭の不要な年号ナビゲーション（LIVE 2026 2025...）を大掃除
    full_text = re.sub(r"LIVE\s+\d{4}.*?\d{4}", "", full_text)

    # 2. 【核心ロジック】「2026/」や「2026.」といった日付の登場を合図に、文章を強制的にぶった切る
    # 日付の直前に特殊な区切り文字 [SPLIT] を埋め込みます
    prepared_text = re.sub(r"(\d{4}[/\.]\d{1,2}[/\.]\d{1,2})", r"[SPLIT]\1", full_text)
    prepared_text = re.sub(r"(\d{4}\s*\.\s*\d{1,2}\s*・)", r"[SPLIT]\1", prepared_text) # 2026. 6 ・14 のような特殊形式にも対応
    
    # 区切り文字で配列に分解
    chunks = prepared_text.split("[SPLIT]")
    
    for chunk in chunks:
        chunk_str = chunk.strip()
        if not chunk_str or len(chunk_str) < 10:
            continue

        # 塊の先頭にある日付（2026/06/14 など）をきれいに見つける
        date_match = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", chunk_str)
        
        # もし見つからない場合、特殊形式（2026. 6 ・14）を探す
        special_match = None
        if not date_match:
            special_match = re.search(r"(\d{4})\s*\.\s*(\d{1,2})\s*・\s*(\d{1,2})", chunk_str)
        
        if not date_match and not special_match:
            continue

        # 日付のパース
        try:
            if date_match:
                year = int(date_match.group(1))
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                matched_text = date_match.group(0)
            else:
                year = int(special_match.group(1))
                month = int(special_match.group(2))
                day = int(special_match.group(3))
                matched_text = special_match.group(0)
                
            event_date = datetime(year, month, day)
        except:
            continue

        # 3. タイトルの抽出とクレンジング
        # 日付の文字を消去し、残った文章をその日のライブタイトルにする
        title_content = chunk_str.replace(matched_text, "").strip()
        
        # 後ろに次の月ナビゲーション（2026. 7 など）がくっついていたらそれ以降を切り捨てる
        title_content = re.split(r"\d{4}\s*\.\s*\d{1,2}", title_content)[0].strip()
        title_content = re.split(r"(\d{4}[/\.])", title_content)[0].strip()
        
        # 連続する不要な空白や改行を1つのスペースに統合
        title_content = re.sub(r"\s+", " ", title_content)
        
        # 余計な記号や、メニューバーのフッター文字（©など）を排除
        if len(title_content) < 5 or "©" in title_content or "BIOGRAPHY" in title_content:
            continue

        # 個別詳細URLの判定（チケットページなどのリンクがあれば最優先で紐付け）
        final_url = list_url
        # 塊の中に含まれるURL（href）を簡易抽出
        url_match = re.search(r"https?://[^\s]+", chunk_str)
        if url_match:
            final_url = url_match.group(0)

        events.append({
            "artist": "Chevon",
            "title": title_content,
            "date": event_date,
            "place": "公式サイトをご参照ください",
            "url": final_url
        })

    # 同じ日付の重複を綺麗に1本にまとめる
    clean_dict = {}
    for ev in events:
        date_str = ev["date"].strftime("%Y-%m-%d")
        if date_str not in clean_dict:
            clean_dict[date_str] = ev
        else:
            if len(ev["title"]) > len(clean_dict[date_str]["title"]):
                clean_dict[date_str] = ev

    unique_events = list(clean_dict.values())
    
    # 上から現在に近い順（古い順 ＝ 昇順）に並び替える
    unique_events.sort(key=lambda x: x["date"])
    return unique_events
