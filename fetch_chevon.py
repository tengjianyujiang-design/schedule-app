# fetch_chevon.py
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
import re

BASE_URL = "https://chevon.biz"

def fetch_chevon():
    # ライブ一覧ページ
    list_url = f"{BASE_URL}/live/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(list_url, headers=headers, method="GET")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        print("Chevon公式サイトの通信エラー:", e)
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
        title_content = re.split(r"\d{4}\s*\.\s*\d{1,2}", title_content)[0].strip()
        title_content = re.split(r"\d{4}[/\.]", title_content)[0].strip()
        title_content = re.sub(r"\s+", " ", title_content)
        
        if len(title_content) < 5 or "©" in title_content or "BIOGRAPHY" in title_content:
            continue

        temp_events.append({
            "artist": "Chevon",
            "title": title_content,
            "date": event_date,
            "place": "公式サイトをご参照ください",
            "url": list_url  # 一旦デフォルト
        })

    # 2. 【超重要】ページ内のすべてのaタグ（リンク）を個別にスキャンしてURLを紐付ける
    # タップして飛べる「各公演の詳細URL」を正確に割り当てます
    for a_tag in soup.find_all("a"):
        text = a_tag.get_text(" ", strip=True)
        href = a_tag.get("href", "")
        
        if not href:
            continue
            
        # リンクの文字の中、またはリンクのURL自体に日付の形が含まれているかチェック
        dm = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", text + href)
        if dm:
            try:
                ev_date = datetime(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                date_str = ev_date.strftime("%Y-%m-%d")
                
                # 正しいURLの形に整形
                final_url = href if href.startswith("http") else BASE_URL + href
                
                # 先ほどテキストから分解した同じ日付の予定を探し、URLを上書きする
                for ev in temp_events:
                    if ev["date"].strftime("%Y-%m-%d") == date_str:
                        ev["url"] = final_url
            except:
                pass

    # 日付順に並び替え
    temp_events.sort(key=lambda x: x["date"])
    return temp_events
