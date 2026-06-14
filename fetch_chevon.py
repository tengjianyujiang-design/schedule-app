# fetch_chevon.py
import urllib.request
import json
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
    # タイムアウト対策のリトライループ（最大3回）
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
                print("Chevon公式サイトの通信エラー（3回すべて失敗しました）")
                return []

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    
    # 1. サイト全体の文字を取得し、日付をベースに大まかに解体
    full_text = soup.get_text(" ", strip=True)
    full_text = re.sub(r"LIVE\s+\d{4}.*?\d{4}", "", full_text)

    split_marker = "[SPLIT]"
    prepared_text = re.sub(r"(\d{4}[/\.]\d{1,2}[/\.]\d{1,2})", rf"{split_marker}\1", full_text)
    chunks = prepared_text.split(split_marker)
    
    temp_events = []

    for chunk in chunks:
        chunk_str = chunk.strip()
        if not chunk_str:
            continue
            
        date_match = re.match(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", chunk_str)
        if not date_match:
            continue
            
        try:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            event_date = datetime(year, month, day)
        except:
            continue

        title_content = chunk_str.replace(date_match.group(0), "").strip()
        
        # 【修正箇所】re.splitのバグを修正。リストではなく文字列として正しく処理します
        title_parts = re.split(r"\d{4}\s*\.\s*\d{1,2}", title_content)
        title_content = title_parts[0].strip() if title_parts else title_content
        
        title_parts_2 = re.split(r"\d{4}[/\.]", title_content)
        title_content = title_parts_2[0].strip() if title_parts_2 else title_content
        
        # 連続するスペースを1つに統合
        title_content = re.sub(r"\s+", " ", title_content)
        
        if len(title_content) < 5 or "©" in title_content or "BIOGRAPHY" in title_content:
            continue

        temp_events.append({
            "artist": "Chevon",
            "title": title_content,
            "date": event_date,
            "place": "公式サイトをご参照ください",
            "url": list_url
        })

    # 2. 各公演に詳細ページURLを紐付ける
    for a_tag in soup.find_all("a"):
        text = a_tag.get_text(" ", strip=True)
        href = a_tag.get("href", "")
        
        if not href:
            continue
            
        dm = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", text + href)
        if dm:
            try:
                ev_date = datetime(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                date_str = ev_date.strftime("%Y-%m-%d")
                final_url = href if href.startswith("http") else BASE_URL + href
                
                for ev in temp_events:
                    if ev["date"].strftime("%Y-%m-%d") == date_str:
                        ev["url"] = final_url
            except:
                pass

    temp_events.sort(key=lambda x: x["date"])
    return temp_events
