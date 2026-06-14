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
    
    # サイト全体のソースコードを文字列にする
    html_str = str(soup)
    
    # 【最新ロジック】各公演のリンクタグ(<a>〜</a>)そのものを1つの塊（ブロック）として直接切り分けます
    # これにより、ブロック内のテキスト（日付・タイトル）と個別のURLが絶対に離れ離れになりません
    raw_chunks = html_str.split("<a")
    
    events = []

    for chunk in raw_chunks:
        # 綺麗に解析するために擬似的なaタグを再構築
        chunk_soup = BeautifulSoup("<a " + chunk, "html.parser")
        a_tag = chunk_soup.find("a")
        
        if not a_tag:
            continue
            
        text_content = a_tag.get_text(" ", strip=True)
        href = a_tag.get("href", "")
        
        if not text_content or not href:
            continue
            
        # ナビゲーションメニューなどの無関係なリンクを弾く
        if any(k in href for k in ["/biography", "/discography", "/goods", "/shop", "/contact"]):
            continue

        # テキストの中から日付（2026/06/13 など）を探す
        date_match = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", text_content)
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
        display_title = text_content.replace(date_match.group(0), "").strip()
        
        # 不要な「LIVE」の年号ナビゲーションなどが混ざっていたら除去
        display_title = re.sub(r"LIVE\s+\d{4}.*?\d{4}", "", display_title)
        display_title = re.sub(r"\s+", " ", display_title).strip()
        
        if len(display_title) < 5:
            continue

        # 個別詳細URLの補正
        final_url = href if href.startswith("http") else BASE_URL + href

        events.append({
            "artist": "Chevon",
            "title": display_title,
            "date": event_date,
            "place": "公式サイトをご参照ください",
            "url": final_url  # 各公演固有のURLがここに入ります
        })

    # 同じ日付の重複を排除（最も文字数が多い詳細なタイトルを優先して残す）
    clean_dict = {}
    for ev in events:
        date_str = ev["date"].strftime("%Y-%m-%d")
        if date_str not in clean_dict:
            clean_dict[date_str] = ev
        else:
            if len(ev["title"]) > len(clean_dict[date_str]["title"]):
                clean_dict[date_str] = ev

    unique_events = list(clean_dict.values())
    unique_events.sort(key=lambda x: x["date"])
    return unique_events
